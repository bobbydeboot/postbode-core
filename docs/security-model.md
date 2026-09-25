# Security model

The package assumes that an application supplies a trusted artifact and an
authorized provider transport. It reduces accidental publication risk by
binding bytes, destination identity, metadata, privacy state, and idempotency
before mutation.

Ambiguous submissions are recorded as started and are not blindly retried.
Remote readback is required before a completed receipt is written. Credential
values are accepted only at an application boundary; receipts contain no raw
secret fields. Applications must protect state directories and access tokens.
