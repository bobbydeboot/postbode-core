# YouTube capabilities

The core models YouTube publication metadata and exposes a small injectable
transport boundary for authenticated channel readback and video readback.
Applications may add upload, thumbnail, caption, playlist, scheduling, or
deletion operations behind the same exact-destination and readback checks.

No live provider call is required by the test suite, and the examples use
fictitious identities.
