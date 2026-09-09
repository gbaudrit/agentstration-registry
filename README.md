# Agentstration Registry

The Agentstration Registry publishes official reusable content Sources as a
versioned static registry. Agentstration imports an immutable `SourceVersion`
manifest, then materializes one of its declared Channels through a locally
bound Source Provider.

## Public endpoints

The canonical endpoint is:

```text
https://registry.agentstration.io/v1/index.json
```

The same Pages deployment is also reachable through:

```text
https://gbaudrit.github.io/agentstration-registry/v1/index.json
```

Every URL inside the registry is relative. The generated publication can
therefore be copied unchanged to another static HTTPS origin.

## Published Sources

| Source | Version | Compatibility | Channel content |
| --- | --- | --- | --- |
| `agentstration/bootstrap-samples` | `1` | Agentstration `>=0.2.0-alpha.1` and `<0.3.0` | [`content/bootstrap-samples`](content/bootstrap-samples) |

The manifest only distributes the Source definition. Channel content is
acquired independently through the Source Provider declared by the Channel.

## Repository layout

```text
registry/v1/                         Authored registry inputs
  index.yaml                         Release-line index
  registry-agentstration-0.2.json    Agentstration 0.2.x shard
  sources/<publisher>/<source>/<version>/source.yaml
content/                             Git Channel content
site/                                Hosting-only root files
scripts/                             Content and publication validation
```

The published tree is generated from `registry/v1`; generated canonical output
and digest files are never edited or committed. Each SourceVersion path is immutable. A
functional manifest change requires a new opaque `definition.version`, a new
path, and a new shard entry. Content-only changes may keep the SourceVersion:
refreshing its moving Git Channel creates a snapshot for the newly resolved
commit.

## Local validation and build

The repository pins the exact compatible
`Agentstration.SourceRegistry.Tool` package. Restore it first:

```bash
dotnet tool restore
```

Validate the Bootstrap catalog and profiles:

```bash
python -m pip install PyYAML==6.0.3
python scripts/validate.py
python -m unittest scripts/test_validate.py
```

Validate the complete registry offline with the production Source readers:

```bash
dotnet tool run agentstration-source-registry -- \
  registry validate registry/v1/index.yaml \
  --publication-root registry/v1 \
  --base-uri https://registry.agentstration.io/v1/
```

Build it into a directory outside the authored input tree:

```bash
dotnet tool run agentstration-source-registry -- \
  registry build registry/v1/index.yaml \
  --publication-root registry/v1 \
  --base-uri https://registry.agentstration.io/v1/ \
  --output artifacts/registry

python scripts/verify_publication.py artifacts/registry
```

The .NET tool is the authority for strict Source, index and shard parsing,
RFC 8785 canonicalization, compatibility, path safety and digests. The Python
validator owns only this repository's Bootstrap catalog and content rules.

## Publication

Pull requests run both validators, validate the two supported origins, build
the registry twice, enforce the publication allowlist and compare every output
byte. Pushes to `main` repeat the checks and deploy the generated tree with the
GitHub Pages artifact and OIDC deployment actions.

GitHub Pages is configured in repository settings with **GitHub Actions** as
its source and `registry.agentstration.io` as its custom domain. DNS points
that subdomain to `gbaudrit.github.io`, and HTTPS enforcement is enabled. A
committed `CNAME` file is not used because Pages custom workflows take the
domain from repository settings.

## Rollback and migration

To roll back, revert the faulty commit on `main`; the next Pages deployment
rebuilds and atomically replaces the site. Do not modify an already published
SourceVersion in place. If clients may already have observed it, publish a new
version and adjust the shard instead.

To migrate away from GitHub Pages, build the registry with the command above,
copy `site/index.html`, `site/.nojekyll`, and the generated `v1` directory to
the new static HTTPS host, then move DNS. Relative registry references and
byte-stable artifacts require no manifest rewrite.

## Bootstrap samples

The catalog groups language variants beneath one logical Bootstrap identity:

```text
profiles/<bootstrap-name>/<locale>/
```

Locales use canonical BCP 47 identifiers such as `fr-FR` and `en-US`; a future
language-neutral variant uses `neutral`. Each variant is complete and selected
explicitly. Variants of one logical entry retain the same profile name, target
scope and binding declarations.

The French `solution-discovery` variant is synchronized from Agentstration's
`deploy/bootstrap/profiles/solution-discovery`. It targets one Workspace and
requires the administrator to bind `agent-model` to a compatible Model Profile
before preview and application.
