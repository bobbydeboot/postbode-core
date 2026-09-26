from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from . import receipts
from .authority import PublicationAuthority
from .contracts import PublicationError, PublicationReceipt, PublicationRequest
from .destination import DestinationPolicy

DEFAULT_UPLOAD_CHUNK_SIZE = 8 * 1024 * 1024
UPLOAD_CHUNK_MULTIPLE = 256 * 1024


@dataclass(frozen=True)
class YouTubeResponse:
    status: int
    headers: dict[str, str]
    body: bytes = b""

    def json(self) -> dict[str, Any]:
        if not self.body:
            return {}
        try:
            value = json.loads(self.body)
        except json.JSONDecodeError as error:
            raise PublicationError("provider response was not valid JSON") from error
        if not isinstance(value, dict):
            raise PublicationError("provider response was not an object")
        return value


def build_upload_metadata(request: PublicationRequest) -> dict[str, Any]:
    request.validate()
    return {
        "snippet": {
            "title": request.title,
            "description": request.description,
            "tags": list(request.tags),
        },
        "status": {
            "privacyStatus": request.privacy_status,
            "selfDeclaredMadeForKids": request.made_for_kids,
        },
    }


class YouTubeTransport:
    """Small injectable transport boundary; real calls are opt-in by the caller."""

    def __init__(
        self, access_token: str, request_fn: Callable[..., dict[str, Any]] | None = None
    ) -> None:
        if not access_token:
            raise PublicationError("access token is required")
        self._access_token = access_token
        self._request_fn = request_fn

    def _request(
        self,
        method: str,
        url: str,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        if self._request_fn:
            return self._request_fn(method, url, body=body, headers=headers)
        request_headers = {"Authorization": f"Bearer {self._access_token}"}
        if headers:
            request_headers.update(headers)
        request = urllib.request.Request(
            url, data=body, method=method, headers=request_headers
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read())
        except (urllib.error.URLError, json.JSONDecodeError) as error:
            raise PublicationError("provider request failed") from error

    def _request_response(
        self,
        method: str,
        url: str,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> YouTubeResponse:
        if self._request_fn:
            result = self._request_fn(method, url, body=body, headers=headers)
            if isinstance(result, YouTubeResponse):
                return result
            if isinstance(result, dict):
                return YouTubeResponse(
                    200,
                    {},
                    json.dumps(result, separators=(",", ":")).encode(),
                )
            raise PublicationError("request function returned an invalid response")
        request_headers = {"Authorization": f"Bearer {self._access_token}"}
        if headers:
            request_headers.update(headers)
        request = urllib.request.Request(
            url, data=body, method=method, headers=request_headers
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return YouTubeResponse(
                    response.status,
                    dict(response.headers.items()),
                    response.read(),
                )
        except urllib.error.HTTPError as error:
            return YouTubeResponse(
                error.code,
                dict(error.headers.items()),
                error.read(),
            )
        except urllib.error.URLError as error:
            raise PublicationError("provider request result is ambiguous") from error

    @staticmethod
    def _header(response: YouTubeResponse, name: str) -> str | None:
        wanted = name.lower()
        return next(
            (value for key, value in response.headers.items() if key.lower() == wanted),
            None,
        )

    @staticmethod
    def _uploaded_through(response: YouTubeResponse) -> int | None:
        value = YouTubeTransport._header(response, "Range")
        if not value:
            return None
        try:
            prefix, bounds = value.split("=", 1)
            first, last = bounds.split("-", 1)
            if prefix.strip().lower() != "bytes":
                raise ValueError
            if int(first) != 0:
                raise ValueError
            return int(last)
        except (ValueError, TypeError) as error:
            raise PublicationError(
                "provider returned an invalid upload range"
            ) from error

    def _resume_offset(
        self, session_url: str, total_size: int
    ) -> tuple[int, str | None]:
        response = self._request_response(
            "PUT",
            session_url,
            body=b"",
            headers={
                "Content-Length": "0",
                "Content-Range": f"bytes */{total_size}",
            },
        )
        if response.status in {200, 201}:
            provider_id = response.json().get("id")
            if not provider_id:
                raise PublicationError(
                    "provider completion response did not contain an ID"
                )
            return total_size, str(provider_id)
        if response.status != 308:
            raise PublicationError("provider upload status could not be reconciled")
        uploaded_through = self._uploaded_through(response)
        return (uploaded_through + 1 if uploaded_through is not None else 0), None

    def channel(self) -> tuple[str, str | None]:
        payload = self._request(
            "GET",
            "https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true",
        )
        item = (payload.get("items") or [None])[0]
        if not item:
            raise PublicationError("authenticated channel was not found")
        snippet = item.get("snippet", {})
        return item["id"], snippet.get("customUrl")

    def upload_private(
        self,
        request: PublicationRequest,
        chunk_size: int = DEFAULT_UPLOAD_CHUNK_SIZE,
        media_content_type: str = "video/mp4",
    ) -> str:
        """Upload a private video using bounded-memory resumable chunks."""
        if chunk_size <= 0 or chunk_size % UPLOAD_CHUNK_MULTIPLE:
            raise PublicationError("chunk size must be a multiple of 256 KiB")
        if not media_content_type.strip():
            raise PublicationError("media content type is required")
        request.validate()
        total_size = request.artifact_path.stat().st_size
        metadata = json.dumps(
            build_upload_metadata(request), separators=(",", ":")
        ).encode()
        init = self._request_response(
            "POST",
            "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
            body=metadata,
            headers={
                "Content-Type": "application/json; charset=UTF-8",
                "Content-Length": str(len(metadata)),
                "X-Upload-Content-Length": str(total_size),
                "X-Upload-Content-Type": media_content_type,
            },
        )
        if init.status != 200:
            raise PublicationError("provider resumable session was not created")
        session_url = self._header(init, "Location")
        if not session_url:
            raise PublicationError("provider resumable response lacked a session URL")
        offset = 0
        with request.artifact_path.open("rb") as stream:
            while offset < total_size:
                stream.seek(offset)
                chunk = stream.read(min(chunk_size, total_size - offset))
                if not chunk:
                    raise PublicationError("artifact ended before the expected size")
                end = offset + len(chunk) - 1
                try:
                    response = self._request_response(
                        "PUT",
                        session_url,
                        body=chunk,
                        headers={
                            "Content-Length": str(len(chunk)),
                            "Content-Type": media_content_type,
                            "Content-Range": f"bytes {offset}-{end}/{total_size}",
                        },
                    )
                except PublicationError as error:
                    if "ambiguous" not in str(error):
                        raise
                    offset, provider_id = self._resume_offset(session_url, total_size)
                    if provider_id:
                        return provider_id
                    continue
                if response.status in {200, 201}:
                    provider_id = response.json().get("id")
                    if not provider_id:
                        raise PublicationError(
                            "provider completion response did not contain an ID"
                        )
                    return str(provider_id)
                if response.status == 308:
                    uploaded_through = self._uploaded_through(response)
                    offset = uploaded_through + 1 if uploaded_through is not None else 0
                    continue
                if response.status in {500, 502, 503, 504}:
                    offset, provider_id = self._resume_offset(session_url, total_size)
                    if provider_id:
                        return provider_id
                    continue
                raise PublicationError("provider resumable upload failed")
        raise PublicationError("provider did not complete the upload")

    def video(self, video_id: str) -> dict[str, Any]:
        return self._request(
            "GET",
            f"https://www.googleapis.com/youtube/v3/videos?part=snippet,status&id={video_id}",
        )


def publish_plan(
    plan: Any,
    authority: PublicationAuthority | None,
    policy: DestinationPolicy,
    transport: Any,
) -> tuple[PublicationReceipt, str]:
    prior = receipts.read_receipt(plan.request_identity)
    if prior:
        if prior.state in {"submission_started", "provider_readback_mismatch"}:
            raise PublicationError(
                "prior submission is ambiguous; inspect provider state before retry"
            )
        return prior, "existing"
    if plan.privacy_status != "private" and authority is None:
        raise PublicationError("authority is required")
    channel_id, _ = transport.channel()
    if channel_id != policy.expected_channel_id:
        raise PublicationError("authenticated channel mismatch")
    started = PublicationReceipt(
        plan.request_identity,
        plan.destination_id,
        plan.platform,
        plan.artifact_sha256,
        channel_id,
        None,
        None,
        "submission_started",
        receipts.now(),
        plan.idempotency_key,
    )
    receipts.write_receipt(started)
    provider_id = transport.upload_private(
        PublicationRequest(
            plan.destination_id,
            "youtube",
            __import__("pathlib").Path(plan.artifact_path),
            plan.artifact_sha256,
            plan.title,
            plan.description,
            plan.privacy_status,
            plan.idempotency_key,
            True,
            plan.tags,
        )
    )
    readback = transport.video(provider_id)
    returned_channel = readback.get("snippet", {}).get("channelId")
    returned_privacy = readback.get("status", {}).get("privacyStatus")
    if returned_channel != channel_id or returned_privacy != plan.privacy_status:
        receipt = PublicationReceipt(
            plan.request_identity,
            plan.destination_id,
            plan.platform,
            plan.artifact_sha256,
            channel_id,
            provider_id,
            returned_privacy,
            "provider_readback_mismatch",
            receipts.now(),
            plan.idempotency_key,
            readback_privacy_status=returned_privacy,
        )
        receipts.write_receipt(receipt)
        raise PublicationError("provider readback does not match plan")
    receipt = PublicationReceipt(
        plan.request_identity,
        plan.destination_id,
        plan.platform,
        plan.artifact_sha256,
        channel_id,
        provider_id,
        returned_privacy,
        "completed",
        receipts.now(),
        plan.idempotency_key,
        readback_privacy_status=returned_privacy,
    )
    return receipts.write_receipt(receipt) and receipt, "created"
