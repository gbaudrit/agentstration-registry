#!/usr/bin/env python3
"""Validate the static Agentstration registry and all referenced content."""

from __future__ import annotations

import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any, NoReturn

import yaml


ROOT = Path(__file__).resolve().parent.parent
SOURCE_PATH = ROOT / "sources/agentstration/bootstrap-samples/source.yaml"
GIT_SOURCE_CHANNEL_SCHEMA_DIGEST = (
    "sha256:1d6b1c53300ea531209a60ad56f50de209d4ae06bfc5c350de2d84bfe6842bf5"
)


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader rejecting duplicate mapping keys."""


def construct_unique_mapping(
    loader: UniqueKeyLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[str, Any]:
    mapping: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    construct_unique_mapping,
)


def fail(message: str) -> NoReturn:
    print(f"validation error: {message}", file=sys.stderr)
    raise SystemExit(1)


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        documents = list(yaml.load_all(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        fail(f"{relative(path)}: {error}")
    if len(documents) != 1:
        fail(f"{relative(path)} must contain exactly one YAML document")
    return require_dict(documents[0], relative(path))


def require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{label} must be an object")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{label} must be an array")
    return value


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        fail(f"{label} must be a non-empty string")
    return value


def descendant_path(value: Any, label: str) -> PurePosixPath:
    path = require_string(value, label)
    segments = path.split("/")
    invalid = (
        "\\" in path
        or path.startswith("/")
        or path.endswith("/")
        or re.match(r"^[A-Za-z]:", path) is not None
        or any(segment in ("", ".", "..") for segment in segments)
    )
    if invalid:
        fail(f"{label} must be a normalized relative descendant path")
    return PurePosixPath(path)


def envelope(
    document: dict[str, Any],
    path: Path,
    expected_kind: str | None = None,
) -> dict[str, Any]:
    label = relative(path)
    if document.get("apiVersion") != "agentstration.io/v1":
        fail(f"{label} has an unsupported apiVersion")
    kind = require_string(document.get("kind"), f"{label}.kind")
    if expected_kind is not None and kind != expected_kind:
        fail(f"{label} must use kind {expected_kind}")
    metadata = require_dict(document.get("metadata"), f"{label}.metadata")
    require_string(metadata.get("name"), f"{label}.metadata.name")
    require_dict(document.get("definition"), f"{label}.definition")
    return document


def resolve_descendant(root: Path, path: PurePosixPath, label: str) -> Path:
    resolved_root = root.resolve(strict=True)
    candidate = root.joinpath(*path.parts).resolve(strict=True)
    if candidate == resolved_root or not candidate.is_relative_to(resolved_root):
        fail(f"{label} must resolve strictly below {relative(root)}")
    return candidate


def validate_all_yaml() -> list[Path]:
    paths = sorted(
        path
        for base in (ROOT / "sources", ROOT / "content")
        for pattern in ("*.yaml", "*.yml")
        for path in base.rglob(pattern)
    )
    for path in paths:
        if path.is_symlink():
            fail(f"symbolic links are not allowed: {relative(path)}")
        envelope(load_yaml(path), path)
    return paths


def validate_registry() -> tuple[int, int, int]:
    yaml_paths = validate_all_yaml()
    source = envelope(load_yaml(SOURCE_PATH), SOURCE_PATH, "SourceVersion")
    definition = require_dict(source["definition"], "SourceVersion.definition")
    require_string(definition.get("version"), "SourceVersion.definition.version")

    bindings = require_list(definition.get("bindings"), "SourceVersion.definition.bindings")
    binding_names: list[str] = []
    for index, value in enumerate(bindings):
        binding = require_dict(value, f"SourceVersion.definition.bindings[{index}]")
        if binding.get("targetKind") != "sourceProvider":
            fail("Source bindings must target sourceProvider")
        binding_names.append(require_string(binding.get("name"), f"SourceVersion.definition.bindings[{index}].name"))
    if len(set(binding_names)) != len(binding_names):
        fail("Source binding names must be unique")

    channels = require_list(definition.get("channels"), "SourceVersion.definition.channels")
    if not channels:
        fail("At least one Source Channel is required")
    content_roots: dict[str, Path] = {}
    for index, value in enumerate(channels):
        channel = require_dict(value, f"SourceVersion.definition.channels[{index}]")
        name = require_string(channel.get("name"), f"SourceVersion.definition.channels[{index}].name")
        if name in content_roots:
            fail("Source Channel names must be unique")
        provider = require_dict(channel.get("provider"), f"Channel {name}.provider")
        if provider.get("binding") not in binding_names:
            fail(f"Channel {name} references an unknown binding")
        configuration = require_dict(channel.get("configuration"), f"Channel {name}.configuration")
        if configuration.get("optionSet") != "io.agentstration.git/source-channel":
            fail(f"Channel {name} must use the Git Source Provider option set")
        if configuration.get("version") != "1.0.0":
            fail(f"Channel {name} must use Git Source Provider options 1.0.0")
        digest = require_string(configuration.get("schemaDigest"), f"Channel {name}.configuration.schemaDigest")
        if digest != GIT_SOURCE_CHANNEL_SCHEMA_DIGEST:
            fail(f"Channel {name} does not pin the Git Source Provider 1.0.0 schema digest")
        values = require_dict(configuration.get("values"), f"Channel {name}.configuration.values")
        reference = require_string(values.get("ref"), f"Channel {name}.configuration.values.ref")
        if not (
            reference.startswith(("refs/heads/", "refs/tags/"))
            or re.fullmatch(r"[0-9a-f]{40}", reference)
        ):
            fail(f"Channel {name} must use an explicit Git ref")
        root_path = descendant_path(values.get("rootPath"), f"Channel {name} rootPath")
        root = ROOT.joinpath(*root_path.parts)
        if not root.is_dir():
            fail(f"Channel {name} rootPath does not exist")
        content_roots[name] = root

    catalogs = require_list(definition.get("catalogs"), "SourceVersion.definition.catalogs")
    if not catalogs:
        fail("At least one Source catalog is required")

    for channel_name, content_root in content_roots.items():
        for index, value in enumerate(catalogs):
            catalog_reference = require_dict(value, f"SourceVersion.definition.catalogs[{index}]")
            if catalog_reference.get("kind") != "BootstrapCatalog":
                fail("Only BootstrapCatalog is currently supported")
            catalog_relative = descendant_path(catalog_reference.get("path"), "BootstrapCatalog path")
            catalog_path = resolve_descendant(content_root, catalog_relative, f"Channel {channel_name} catalog")
            if not catalog_path.is_file():
                fail(f"Channel {channel_name} catalog is not a file: {catalog_relative}")

            catalog = envelope(load_yaml(catalog_path), catalog_path, "BootstrapCatalog")
            entries = require_list(catalog["definition"].get("entries"), "BootstrapCatalog.definition.entries")
            if not entries:
                fail("BootstrapCatalog must contain at least one entry")
            entry_names: list[str] = []
            for entry_index, entry_value in enumerate(entries):
                entry = require_dict(entry_value, f"BootstrapCatalog.definition.entries[{entry_index}]")
                entry_name = require_string(entry.get("name"), f"BootstrapCatalog.definition.entries[{entry_index}].name")
                entry_names.append(entry_name)
                entry_relative = descendant_path(entry.get("path"), f"BootstrapCatalog entry {entry_name} path")
                profile_root = resolve_descendant(catalog_path.parent, entry_relative, f"BootstrapCatalog entry {entry_name}")
                if not profile_root.is_dir():
                    fail(f"Bootstrap profile is not a directory: {entry_relative}")
                if not profile_root.is_relative_to(content_root.resolve(strict=True)):
                    fail(f"Bootstrap profile escapes the Channel root: {entry_relative}")

                descriptor_path = profile_root / "profile.yaml"
                if not descriptor_path.is_file():
                    fail(f"Bootstrap profile {entry_name} has no profile.yaml")
                descriptor = envelope(load_yaml(descriptor_path), descriptor_path, "BootstrapProfile")
                if descriptor["metadata"]["name"] != entry_name:
                    fail(f"Catalog entry {entry_name} and BootstrapProfile name differ")
                if descriptor["definition"].get("targetScope") != "workspace":
                    fail("Published Bootstrap samples must declare targetScope: workspace")

                resources = sorted(
                    path
                    for pattern in ("*.yaml", "*.yml")
                    for path in profile_root.glob(pattern)
                    if path.name != "profile.yaml"
                )
                if not resources:
                    fail(f"Bootstrap profile {entry_name} contains no resources")
                for resource in resources:
                    envelope(load_yaml(resource), resource)
            if len(set(entry_names)) != len(entry_names):
                fail("BootstrapCatalog entry names must be unique")

    return len(yaml_paths), len(channels), len(catalogs)


if __name__ == "__main__":
    yaml_count, channel_count, catalog_count = validate_registry()
    print(f"Validated {yaml_count} YAML files, {channel_count} Channel, and {catalog_count} catalog.")
