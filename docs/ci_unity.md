# Unity CI Workflows

## Why non-Unity workflows ignore Unity paths
Most of our GitHub Actions workflows build and test the backend, web, or data pipelines. Changes scoped to the Unity client (under `mobile/unity/`) should not trigger these jobs because they require the Unity editor and dramatically increase runtime. By adding `paths-ignore: mobile/unity/**` to the standard push and pull request triggers, we keep CI green for Unity-only PRs while still exercising the relevant pipelines for other parts of the repo.

## Unity Tests workflow
The dedicated **Unity Tests** workflow (`.github/workflows/unity-tests.yml`) runs only when files under `mobile/unity/**` change. It executes Unity edit-mode tests through the [game-ci/unity-test-runner](https://github.com/game-ci/unity-test-runner) GitHub Action.

### Secrets required
To run Unity in CI you need the following repository secrets:

| Secret | Description |
| --- | --- |
| `UNITY_LICENSE` | The base64-encoded Unity license file. |
| `UNITY_EMAIL` | Unity account email used for activation. |
| `UNITY_PASSWORD` | Unity account password. |

If these secrets are absent, the workflow exits early so forks and local clones do not fail. For guidance on generating a license, refer to Unity's [CI licensing documentation](https://example.com/unity-license-docs).

### Overriding the Unity version
The workflow defaults to Unity `2022.3.21f1`. To test against a different editor version, define the `UNITY_VERSION` environment variable in the workflow or repository/environment settings. The workflow will automatically use the provided value when present.
