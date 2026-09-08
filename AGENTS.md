# Contributor instructions

- Keep repository documentation, commits, and pull requests in English.
- Preserve localized sample content when localization is intentional.
- Treat every `SourceVersion` manifest as an immutable published definition.
  Increment `definition.version` whenever any functional definition field changes.
- Keep Channel `rootPath`, catalog paths, and entry paths normalized, relative,
  and strictly descendant. Never introduce `.` or `..` traversal.
- Declare catalogs explicitly. Do not add recursive repository discovery.
- Run `python scripts/validate.py` before proposing a change.
