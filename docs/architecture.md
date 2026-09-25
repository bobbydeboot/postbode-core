# Architecture

The package separates immutable request contracts, destination policy,
authority, deterministic planning, provider transport, and durable receipts.

```text
approved artifact -> request validation -> destination binding
    -> authority/idempotency check -> provider transport -> readback -> receipt
```

The transport is injectable so tests can use fakes and applications can select
their own OAuth library or secret store. The core never generates media or
decides what should be published.
