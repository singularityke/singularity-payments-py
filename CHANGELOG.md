# Changelog

All notable changes to this project are documented in this file.

## [1.0.1] - 2026-10-10

### Security

- Upgrade `anyio` to `>=4.14.2` to fix CVE-2026-63374 (critical — TLS hostname/certificate mismatch) and CVE-2026-64847 (moderate — process-pool stderr denial of service).
- Upgrade `cryptography` to `>=50.0.0` to fix CVE-2026-69247 (PKCS#7 `pkcs7_decrypt_*` Bleichenbacher oracle).

### Changed

- Raise `requires-python` to `>=3.10`, required by `anyio >= 4.14.2`. Python 3.9 is no longer supported.
- Fix the `singularity-payments` console script, which previously pointed at a `main()` entry point that did not exist.
- Rewrite the README for the Python SDK (was a leftover copy of the TypeScript package).