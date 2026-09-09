import hashlib
import pathlib
import sys


EXPECTED_FILES = {
    "index.json",
    "index.sha256",
    "registry-agentstration-0.2.json",
    "registry-agentstration-0.2.sha256",
    "sources/agentstration/bootstrap-samples/1/source.yaml",
}


def files(root: pathlib.Path) -> dict[str, bytes]:
    actual = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    if set(actual) != EXPECTED_FILES:
        missing = sorted(EXPECTED_FILES - set(actual))
        unexpected = sorted(set(actual) - EXPECTED_FILES)
        raise ValueError(f"publication allowlist mismatch; missing={missing}, unexpected={unexpected}")
    return actual


def verify_digest(publication: dict[str, bytes], document: str, digest_file: str) -> None:
    expected = "sha256:" + hashlib.sha256(publication[document]).hexdigest() + "\n"
    actual = publication[digest_file].decode("ascii")
    if actual != expected:
        raise ValueError(f"{digest_file} does not match {document}")


def main() -> None:
    if len(sys.argv) not in (2, 3):
        raise SystemExit("usage: verify_publication.py <publication> [<second-publication>]")

    first = files(pathlib.Path(sys.argv[1]))
    verify_digest(first, "index.json", "index.sha256")
    verify_digest(
        first,
        "registry-agentstration-0.2.json",
        "registry-agentstration-0.2.sha256",
    )

    if len(sys.argv) == 3 and first != files(pathlib.Path(sys.argv[2])):
        raise ValueError("registry builds are not byte-for-byte reproducible")

    print(f"Verified {len(first)} published files.")


if __name__ == "__main__":
    main()
