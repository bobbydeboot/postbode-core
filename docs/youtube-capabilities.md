# YouTube capabilities

The core models YouTube publication metadata and exposes a small injectable
transport boundary for authenticated channel readback and video readback.
The transport supports private video upload through YouTube's resumable upload
protocol. It reads the artifact incrementally and sends configurable chunks;
the default chunk size is 8 MiB and non-final chunks must be multiples of
256 KiB. If a chunk result is ambiguous or the provider returns a recoverable
server error, the transport checks the resumable session status before sending
any further bytes. It never blindly retries an ambiguous chunk.

Thumbnail, caption, playlist, scheduling, and deletion operations are outside
the current transport surface.

No live provider call is required by the test suite, and the examples use
fictitious identities.
