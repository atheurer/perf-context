#!/usr/bin/env python3
"""Regenerate all INDEX.md files and update SYMPTOMS.md Units column.

What this does:
  1. Scans corpus/<domain>/*.md for all units (reads frontmatter)
  2. Writes corpus/<domain>/INDEX.md — one line per unit: id, abstract, tokens, type
  3. Writes indexes/INDEX.md — per-domain sections from domain index files
  4. Updates the Units column in indexes/SYMPTOMS.md based on unit symptom tags

Run this after every distill/critique pass. It is fully idempotent.

Usage:
    python3 scripts/build_indexes.py [--dry-run] [--verbose]
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

REPO_ROOT = Path(__file__).parent.parent
CORPUS_ROOT = REPO_ROOT / "corpus"
INDEXES_DIR = REPO_ROOT / "indexes"
SYMPTOMS_PATH = INDEXES_DIR / "SYMPTOMS.md"
TOP_INDEX_PATH = INDEXES_DIR / "INDEX.md"

DOMAIN_ORDER = [
    "methodology",
    "observability",
    "hardware",
    "kernel",
    "runtimes",
    "distributed",
    "gpu-ml",
]

# Maps symptom tags (from unit frontmatter) to SYMPTOMS.md row patterns.
# The row pattern is matched against the "Symptom signature" column using
# a simple substring match. Multiple tags may map to the same row.
# When adding new rows to SYMPTOMS.md, add entries here.
TAG_TO_ROW_PATTERN: dict[str, str] = {
    "high-sys-cpu": "High sys%",
    "high-user-cpu": "High sys%",           # also belongs in sys% row
    "lock-contention": "High sys%",
    "low-cpu-low-throughput": "CPU not saturated",
    "throughput-collapse": "CPU not saturated",
    "p99-tail": "p99 >> p50",
    "gc-pause": "p99 >> p50",
    "low-ipc": "Low IPC",
    "frontend-bound": "Low IPC",
    "backend-bound": "Low IPC",
    "false-sharing": "Low IPC",
    "softirq-saturation": "One core pegged in softirq",
    "irq-storm": "One core pegged in softirq",
    "memory-pressure": "Throughput drops after minutes",
    "swap-thrash": "Throughput drops after minutes",
    "kv-cache-pressure": "TPOT degrades",
    "cgroup-throttled": "cgroup app slow",
    "gpu-underutilized": "GPU util low",
    "gpu-oom": "GPU util low",
    "ttft-high": "TTFT high",
    "tpot-high": "TPOT degrades",
    "collective-slow": "Multi-GPU scaling poor",
    "pcie-bound": "Multi-GPU scaling poor",
    "iowait-high": "iowait high",
    "packet-drops": "Packet drops",
    "retransmits": "Packet drops",
    "numa-remote": "p99 >> p50",            # NUMA causes tail; also iowait
    "run-queue-long": "High sys%",           # run-queue depth → scheduler pressure
}


def parse_frontmatter(path: Path) -> dict | None:
    text = path.read_text(errors="replace")
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        fm = yaml.safe_load(parts[1])
        return fm if isinstance(fm, dict) else None
    except yaml.YAMLError:
        return None


def extract_abstract(path: Path) -> str:
    """Return the first paragraph after '## Abstract' (max ~200 chars)."""
    text = path.read_text(errors="replace")
    in_abstract = False
    lines: list[str] = []
    for line in text.splitlines():
        if re.match(r"^## Abstract", line):
            in_abstract = True
            continue
        if in_abstract:
            if re.match(r"^#", line):
                break
            if line.strip() == "" and lines:
                break
            if line.strip():
                lines.append(line.strip())
    abstract = " ".join(lines)
    if len(abstract) > 220:
        abstract = abstract[:217] + "..."
    return abstract


def scan_corpus() -> dict[str, list[dict]]:
    """Return {domain: [unit_info, ...]} sorted by id within each domain."""
    by_domain: dict[str, list[dict]] = defaultdict(list)
    for path in sorted(CORPUS_ROOT.rglob("*.md")):
        if path.name == "INDEX.md":
            continue
        fm = parse_frontmatter(path)
        if not fm:
            print(f"  WARN: could not parse frontmatter: {path.relative_to(REPO_ROOT)}")
            continue
        domain = fm.get("domain", "")
        domain_dir = path.parent.name
        if domain != domain_dir and domain_dir in DOMAIN_ORDER:
            domain = domain_dir
        tokens = fm.get("tokens") or {}
        by_domain[domain].append(
            {
                "id": fm.get("id", path.stem),
                "title": fm.get("title", ""),
                "type": fm.get("type", ""),
                "domain": domain,
                "tags": fm.get("tags") or [],
                "abstract": extract_abstract(path),
                "digest_tokens": tokens.get("digest", "?"),
                "path": path,
            }
        )
    for domain in by_domain:
        by_domain[domain].sort(key=lambda u: u["id"])
    return dict(by_domain)


def build_domain_index(domain: str, units: list[dict], dry_run: bool) -> str:
    """Write corpus/<domain>/INDEX.md and return its content."""
    lines = [
        f"# {domain} — unit index\n",
        f"<!-- Auto-generated by scripts/build_indexes.py — do not edit manually -->\n",
        "\n",
        "| id | abstract | tokens | type |\n",
        "|---|---|---|---|\n",
    ]
    for u in units:
        abstract = u["abstract"].replace("|", "\\|")
        lines.append(
            f"| `{u['id']}` | {abstract} | {u['digest_tokens']} | {u['type']} |\n"
        )

    content = "".join(lines)
    domain_index = CORPUS_ROOT / domain / "INDEX.md"
    if not dry_run:
        domain_index.parent.mkdir(parents=True, exist_ok=True)
        domain_index.write_text(content)
    return content


def build_top_index(by_domain: dict[str, list[dict]], dry_run: bool) -> None:
    """Write indexes/INDEX.md with a section per domain."""
    lines = [
        "# perf-context index — all domains\n",
        "<!-- Auto-generated by scripts/build_indexes.py — do not edit manually -->\n",
        "\n",
        f"Total units: {sum(len(v) for v in by_domain.values())}\n",
        "\n",
    ]
    for domain in DOMAIN_ORDER:
        units = by_domain.get(domain, [])
        if not units:
            continue
        lines.append(f"## {domain} ({len(units)} units)\n\n")
        for u in units:
            abstract = u["abstract"]
            lines.append(f"- `{u['id']}` — {abstract}\n")
        lines.append("\n")

    content = "".join(lines)
    if not dry_run:
        INDEXES_DIR.mkdir(parents=True, exist_ok=True)
        TOP_INDEX_PATH.write_text(content)
    else:
        print("--- indexes/INDEX.md (dry-run) ---")
        print(content[:500], "..." if len(content) > 500 else "")


def update_symptoms_md(by_domain: dict[str, list[dict]], dry_run: bool) -> None:
    """Rewrite the Units column in indexes/SYMPTOMS.md from unit tags."""
    if not SYMPTOMS_PATH.exists():
        print(f"  WARN: {SYMPTOMS_PATH} not found — skipping symptoms update")
        return

    # Build tag → unit_id mapping
    tag_to_units: dict[str, list[str]] = defaultdict(list)
    for units in by_domain.values():
        for u in units:
            for tag in u["tags"]:
                tag_to_units[tag].append(u["id"])

    # Build row_pattern → unit_ids
    row_pattern_to_units: dict[str, set[str]] = defaultdict(set)
    for tag, unit_ids in tag_to_units.items():
        pattern = TAG_TO_ROW_PATTERN.get(tag)
        if pattern:
            row_pattern_to_units[pattern].update(unit_ids)

    original = SYMPTOMS_PATH.read_text()
    lines = original.splitlines(keepends=True)
    new_lines: list[str] = []
    in_table = False

    for line in lines:
        # Detect table start (the header row)
        if re.match(r"\| Symptom signature", line):
            in_table = True
            new_lines.append(line)
            continue
        # Detect table end (blank line or non-table line after table started)
        if in_table and not line.startswith("|"):
            in_table = False
            new_lines.append(line)
            continue

        if in_table and line.startswith("|") and not re.match(r"\|[-| ]+\|", line):
            # Data row — find which row_pattern matches this symptom signature
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cols) >= 4:
                symptom_sig = cols[0]
                matched_pattern = None
                for pattern in row_pattern_to_units:
                    if pattern.lower() in symptom_sig.lower():
                        matched_pattern = pattern
                        break
                if matched_pattern:
                    unit_ids = sorted(row_pattern_to_units[matched_pattern])
                    units_str = " ".join(f"`{uid}`" for uid in unit_ids)
                else:
                    # Preserve existing content if no units match yet
                    units_str = cols[3] if cols[3] else "TBD"

                new_line = f"| {cols[0]} | {cols[1]} | {cols[2]} | {units_str} |\n"
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    new_content = "".join(new_lines)
    if not dry_run:
        SYMPTOMS_PATH.write_text(new_content)
    else:
        print("--- indexes/SYMPTOMS.md table (dry-run, first 1000 chars) ---")
        print(new_content[:1000])


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild perf-context index files")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Print only, no writes")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    if not CORPUS_ROOT.is_dir():
        print(f"ERROR: corpus directory not found: {CORPUS_ROOT}", file=sys.stderr)
        return 1

    print("Scanning corpus units...")
    by_domain = scan_corpus()
    total = sum(len(v) for v in by_domain.values())
    print(f"  Found {total} units across {len(by_domain)} domains")

    print("Building domain INDEX.md files...")
    for domain in DOMAIN_ORDER:
        units = by_domain.get(domain, [])
        if not units:
            continue
        build_domain_index(domain, units, args.dry_run)
        if args.verbose:
            print(f"  {domain}: {len(units)} unit(s)")

    print("Building indexes/INDEX.md...")
    build_top_index(by_domain, args.dry_run)

    print("Updating indexes/SYMPTOMS.md Units column...")
    update_symptoms_md(by_domain, args.dry_run)

    if args.dry_run:
        print("Dry-run complete — no files written.")
    else:
        print("Done.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
