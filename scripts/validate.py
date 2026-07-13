#!/usr/bin/env python3
"""Validate corpus units against the frontmatter schema.

Checks:
- Required fields present with correct types
- Enum values valid
- id uniqueness across all units
- corpus_path matches the file's actual domain directory
- token count fields are positive integers

Exit code 0 = all pass. Non-zero = failures printed to stderr.

Usage:
    python3 scripts/validate.py [--corpus-dir corpus] [--verbose]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

REPO_ROOT = Path(__file__).parent.parent

VALID_TYPES = {"concept", "tool", "reference", "playbook", "case_study", "pointer"}
VALID_DOMAINS = {
    "methodology",
    "observability",
    "hardware",
    "kernel",
    "runtimes",
    "distributed",
    "gpu-ml",
}
VALID_TRACKS = {"core", "digest", "conservative", "pointer"}
VALID_QUALITY = {"seed", "reviewed", "eval-validated"}

REQUIRED_FIELDS = [
    "id",
    "title",
    "type",
    "domain",
    "tags",
    "source_id",
    "source_license",
    "license_verified",
    "track",
    "quality",
    "created",
    "last_verified",
]

OPTIONAL_FIELDS = {
    "source_url",
    "applicability",
    "tokens",
    "supersedes",
    "annex_raw",
}


def parse_frontmatter(path: Path) -> tuple[dict | None, str]:
    """Return (frontmatter_dict, error_message). error_message empty on success."""
    text = path.read_text(errors="replace")
    if not text.startswith("---"):
        return None, "no frontmatter delimiter at start of file"
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, "frontmatter not closed with '---'"
    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        return None, f"YAML parse error: {e}"
    if not isinstance(fm, dict):
        return None, "frontmatter did not parse as a mapping"
    return fm, ""


def validate_unit(path: Path, fm: dict) -> list[str]:
    """Return list of error strings for this unit (empty = valid)."""
    errors: list[str] = []
    prefix = str(path.relative_to(REPO_ROOT))

    # Required fields
    for field in REQUIRED_FIELDS:
        if field not in fm:
            errors.append(f"{prefix}: missing required field '{field}'")

    if errors:
        return errors

    # Type checks and enum validation
    uid = fm["id"]
    if not isinstance(uid, str) or not re.match(r"^[a-z0-9][a-z0-9\-]*$", uid):
        errors.append(f"{prefix}: id '{uid}' must be lowercase kebab-case")

    if fm.get("type") not in VALID_TYPES:
        errors.append(f"{prefix}: type '{fm.get('type')}' not in {sorted(VALID_TYPES)}")

    domain = fm.get("domain")
    if domain not in VALID_DOMAINS:
        errors.append(f"{prefix}: domain '{domain}' not in {sorted(VALID_DOMAINS)}")
    else:
        expected_dir = REPO_ROOT / "corpus" / domain
        if not str(path).startswith(str(expected_dir)):
            errors.append(
                f"{prefix}: domain='{domain}' but file is not under corpus/{domain}/"
            )

    if fm.get("track") not in VALID_TRACKS:
        errors.append(f"{prefix}: track '{fm.get('track')}' not in {sorted(VALID_TRACKS)}")

    if fm.get("quality") not in VALID_QUALITY:
        errors.append(
            f"{prefix}: quality '{fm.get('quality')}' not in {sorted(VALID_QUALITY)}"
        )

    tags = fm.get("tags")
    if not isinstance(tags, list) or not tags:
        errors.append(f"{prefix}: tags must be a non-empty list")

    if not isinstance(fm.get("license_verified"), bool):
        errors.append(f"{prefix}: license_verified must be a boolean")

    tokens = fm.get("tokens")
    if tokens is not None:
        if not isinstance(tokens, dict):
            errors.append(f"{prefix}: tokens must be a mapping with abstract/digest keys")
        else:
            for k in ("abstract", "digest"):
                v = tokens.get(k)
                if v is not None and (not isinstance(v, int) or v <= 0):
                    errors.append(f"{prefix}: tokens.{k} must be a positive integer, got {v!r}")

    applicability = fm.get("applicability")
    if applicability is not None:
        if not isinstance(applicability, dict):
            errors.append(f"{prefix}: applicability must be a mapping")
        else:
            for k in ("kernel", "hardware", "software"):
                if k not in applicability:
                    errors.append(f"{prefix}: applicability missing '{k}' key")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate perf-context corpus units")
    parser.add_argument("--corpus-dir", default="corpus", help="Corpus root relative to repo")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    corpus_root = REPO_ROOT / args.corpus_dir
    if not corpus_root.is_dir():
        print(f"ERROR: corpus directory not found: {corpus_root}", file=sys.stderr)
        return 1

    units = sorted(corpus_root.rglob("*.md"))
    units = [u for u in units if u.name != "INDEX.md"]

    if not units:
        print("No corpus units found.", file=sys.stderr)
        return 0

    all_errors: list[str] = []
    seen_ids: dict[str, Path] = {}

    for path in units:
        fm, parse_error = parse_frontmatter(path)
        if parse_error:
            all_errors.append(f"{path.relative_to(REPO_ROOT)}: {parse_error}")
            continue

        unit_errors = validate_unit(path, fm)
        all_errors.extend(unit_errors)

        uid = fm.get("id")
        if uid:
            if uid in seen_ids:
                all_errors.append(
                    f"Duplicate id '{uid}': "
                    f"{path.relative_to(REPO_ROOT)} and {seen_ids[uid].relative_to(REPO_ROOT)}"
                )
            else:
                seen_ids[uid] = path

        if args.verbose and not unit_errors:
            print(f"  OK  {path.relative_to(REPO_ROOT)}")

    if all_errors:
        for err in all_errors:
            print(f"FAIL {err}", file=sys.stderr)
        print(f"\n{len(all_errors)} error(s) in {len(units)} unit(s).", file=sys.stderr)
        return 1

    print(f"All {len(units)} unit(s) valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
