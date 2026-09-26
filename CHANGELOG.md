# Changelog

## 0.2.0

### Added

- Bounded-memory resumable YouTube uploads.
- Provider upload-session reconciliation after recoverable interruptions.
- Public `sha256_file` helper.

### Changed

- Artifact SHA-256 validation now streams file contents instead of loading the
  complete artifact into memory.
- YouTube media upload now uses bounded chunks instead of one complete
  in-memory multipart body.

### Safety

- Ambiguous upload results reuse and reconcile the existing resumable session.
- Unknown provider state continues to fail closed rather than blindly starting a
  duplicate upload.

## 0.1.0

- Initial standalone OSS preparation release.
- Added fail-closed artifact and destination contracts.
- Added deterministic plans, idempotency protection, secret-safe receipts,
  credential fingerprints, and injectable provider readback.
- Added generic asset validation, examples, documentation, and offline tests.
