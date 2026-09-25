from __future__ import annotations

import json
import uuid
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

from .authority import PublicationAuthority
from .contracts import PublicationError, PublicationReceipt, PublicationRequest
from .destination import DestinationPolicy
from . import receipts


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

    def upload_private(self, request: PublicationRequest) -> str:
        metadata = json.dumps(
            build_upload_metadata(request), separators=(",", ":")
        ).encode()
        media = request.artifact_path.read_bytes()
        boundary = f"postbode-{uuid.uuid4().hex}"
        delimiter = boundary.encode()
        body = b"".join(
            (
                b"--" + delimiter + b"\r\n",
                b"Content-Type: application/json; charset=UTF-8\r\n\r\n",
                metadata,
                b"\r\n--" + delimiter + b"\r\n",
                b"Content-Type: video/mp4\r\n\r\n",
                media,
                b"\r\n--" + delimiter + b"--\r\n",
            )
        )
        payload = self._request(
            "POST",
            "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=multipart&part=snippet,status",
            body=body,
            headers={
                "Content-Type": f"multipart/related; boundary={boundary}",
                "Content-Length": str(len(body)),
            },
        )
        provider_id = payload.get("id")
        if not provider_id:
            raise PublicationError("provider upload response did not contain an ID")
        return str(provider_id)

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
    try:
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
    except Exception:
        raise
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
