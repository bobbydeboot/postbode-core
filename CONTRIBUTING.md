# Contributing

Create a local environment and install the test extras:

```console
pip install -e ".[test]"
pytest
ruff check .
black --check .
```

Pull requests should explain the user-facing behavior, include regression
tests, preserve fail-closed behavior, and avoid unrelated changes. Do not add
secrets, provider credentials, private media, real account identifiers, or
production receipts to issues, commits, fixtures, or logs.

Please report reproducible bugs with the smallest safe example. Security
issues should follow [SECURITY.md](SECURITY.md), not a public issue.
