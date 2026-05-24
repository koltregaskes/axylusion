# Security Policy

## Reporting

If you discover a security issue in `axylusion`, please report it privately first.

Until a dedicated security inbox is published, do not open a public issue containing:

- secrets
- private workspace paths
- internal operational notes
- unpublished editorial or gallery research

## Scope

The most important security rule in this project is data separation:

- public output (gallery, posts, digests) must only come from allowlisted public-safe fields
- internal runtime / handoff data must not leak into committed public assets
- machine-local paths and credentials must never be committed
