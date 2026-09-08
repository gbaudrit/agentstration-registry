# Agentstration Registry

The Agentstration Registry publishes official reusable content Sources. It is a
static, provider-neutral registry: Agentstration imports a `SourceVersion`
manifest, then materializes one of its declared Channels through a locally bound
Source Provider.

The first published Source contains the official Bootstrap samples and uses the
Git Source Provider introduced by Agentstration pull request
[`#172`](https://github.com/gbaudrit/agentstration/pull/172).

## Published Sources

| Source | Manifest | Content root | Status |
| --- | --- | --- | --- |
| `agentstration/bootstrap-samples` | [`sources/agentstration/bootstrap-samples/source.yaml`](sources/agentstration/bootstrap-samples/source.yaml) | [`content/bootstrap-samples`](content/bootstrap-samples) | Initial catalog |

The moving raw URL for the published definition is:

```text
https://raw.githubusercontent.com/gbaudrit/agentstration-registry/main/sources/agentstration/bootstrap-samples/source.yaml
```

The manifest URL only distributes the Source definition. Channel content is
acquired independently through the Source Provider declared by the Channel.

## Layout

```text
sources/
  agentstration/
    bootstrap-samples/
      source.yaml
content/
  bootstrap-samples/
    catalog.yaml
    profiles/
      solution-discovery/
        fr-FR/
scripts/
  validate.py
```

Every catalog and entry path is an explicit normalized descendant of the Git
Channel `rootPath`. The registry never relies on recursive discovery or upward
path traversal.

## Versioning

- Change `definition.version` whenever the complete published Source definition
  changes, including its bindings, Channels, compatibility bounds, or catalogs.
- Content-only changes do not require a new Source Version. A Channel refresh
  resolves the moved Git ref and creates an immutable snapshot for the new
  commit.
- Stable releases can add a Channel backed by an explicit immutable Git tag.

## Bootstrap samples

The catalog groups language variants beneath the logical Bootstrap identity:

```text
profiles/<bootstrap-name>/<locale>/
```

Locales use BCP 47 identifiers such as `fr-FR` and `en-US`. Each variant is a
complete, independently applicable profile; variants are selected explicitly
and are never merged. A future language-neutral variant uses `neutral` rather
than implying that it is translated into every language.

The French `solution-discovery` variant is initially synchronized from
`deploy/bootstrap/profiles/solution-discovery` in the Agentstration repository.
It targets one Workspace and requires the administrator to bind `agent-model`
to a compatible Model Profile before preview and application.

The `BootstrapCatalog` contract is introduced by Agentstration issue
[`#156`](https://github.com/gbaudrit/agentstration/issues/156). Until that
increment is merged, this repository validates the proposed contract and
content layout locally; end-to-end consumption also depends on the Source
snapshot and Bootstrap integration increments.

## Validation

Run the same checks as CI with:

```bash
python scripts/validate.py
```

The validator parses every YAML document, validates the Source and catalog
envelopes, enforces descendant-only paths, and checks every referenced Bootstrap
Profile.
