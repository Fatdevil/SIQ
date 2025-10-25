# Web Client

## Type Checking Configurations

The production build runs TypeScript with `tsconfig.app.json`, which excludes test files. Tests and IDE tooling that rely on Vitest globals can point to `tsconfig.vitest.json`.
