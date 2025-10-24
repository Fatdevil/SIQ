# SIQ

[![Unity Tests](https://github.com/Fatdevil/SIQ/actions/workflows/unity-tests.yml/badge.svg)](.github/workflows/unity-tests.yml)

## Unity CI (optional)

Unity edit-mode tests run in [`.github/workflows/unity-tests.yml`](.github/workflows/unity-tests.yml) and only trigger when changes occur under `mobile/unity/**`. The workflow exits cleanly when Unity secrets are not configured, so regular contributions are unaffected.

To enable Unity CI, add the following repository secrets (see [docs/ci_unity.md](docs/ci_unity.md) for detailed guidance):

- `UNITY_LICENSE`
- `UNITY_EMAIL`
- `UNITY_PASSWORD`

You can override the default Unity editor version by setting the `UNITY_VERSION` environment variable when running the workflow.
