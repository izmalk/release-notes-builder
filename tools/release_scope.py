"""Validate an exhaustive release component list and audit a review page.

This is a scope guard, not a multi-repository release-notes orchestrator. An
agent still has to resolve names, refs, and compatibility from source material.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re


REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
NAMESPACE = re.compile(r"[A-Za-z0-9_.\-/]+\Z")


@dataclass(frozen=True)
class Component:
    name: str
    repo: str | None = None
    tag_namespace: str | None = None


def parse_components(text: str) -> list[Component]:
    """Read one name, owner/repo, or name | owner/repo | tag namespace per line."""
    components: list[Component] = []
    names: set[str] = set()
    for line_number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) > 3 or any(not part for part in parts):
            raise ValueError(f"line {line_number}: expected name [| owner/repo [| tag namespace]]")
        if len(parts) == 1:
            repo = parts[0] if REPO.fullmatch(parts[0]) else None
            name = repo.split("/", 1)[1] if repo else parts[0]
            namespace = None
        else:
            name, repo = parts[:2]
            namespace = parts[2] if len(parts) == 3 else None
            if not REPO.fullmatch(repo):
                raise ValueError(f"line {line_number}: repository must be owner/repo")
        if not name or name.startswith("#") or "\n" in name or "\r" in name:
            raise ValueError(f"line {line_number}: invalid component name")
        if namespace and not NAMESPACE.fullmatch(namespace):
            raise ValueError(f"line {line_number}: invalid tag namespace")
        key = name.casefold()
        if key in names:
            raise ValueError(f"line {line_number}: duplicate component name {name!r}")
        names.add(key)
        components.append(Component(name, repo.lower() if repo else None, namespace))
    if not components:
        raise ValueError("exhaustive component list is empty")
    return components


def choose_scope(file_text: str | None, inline_text: str | None) -> dict:
    """The explicitly supplied file always wins, including when it is invalid."""
    if file_text is None and inline_text is None:
        raise ValueError("supply an exhaustive file or inline list")
    source = "file" if file_text is not None else "inline"
    selected = parse_components(file_text if file_text is not None else inline_text or "")
    discrepancy = None
    if file_text is not None and inline_text is not None:
        try:
            inline = parse_components(inline_text)
            if inline != selected:
                discrepancy = [asdict(c) for c in inline]
        except ValueError as exc:
            discrepancy = {"invalid_inline_list": str(exc)}
    return {"source": source, "components": [asdict(c) for c in selected],
            "ignored_inline": discrepancy}


def audit_document(text: str, selected: list[Component], candidates: list[str] = ()) -> dict:
    """Find selected and known-unselected names in component headings/table rows.

    Candidate names come from previously published notes and template rows;
    unknown synonyms and prose cannot be identified by this syntactic check.
    """
    labels: set[str] = set()
    known = {item.name.casefold() for item in selected} | {item.casefold() for item in candidates}
    # Review comments can deliberately name missing components; they are not
    # published content and must not satisfy the scope audit.
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    in_fence = False
    in_compatibility = False
    in_changelog = False
    saw_first_heading = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence and not in_compatibility:
            continue
        heading = re.fullmatch(r"#{2,3}\s+(.+?)\s*#*\s*", line)
        if heading:
            label = heading.group(1).strip().casefold()
            if line.startswith("## "):
                in_compatibility = label == "compatibility"
                if label in {"known issues", "acknowledgements", "security"}:
                    in_changelog = False
                elif not saw_first_heading and not in_compatibility:
                    in_changelog = True
                    saw_first_heading = True
            if not in_fence and (in_changelog or in_compatibility) and label in known:
                labels.add(label)
        elif in_compatibility and line.startswith("|"):
            cells = line.split("|")
            if len(cells) > 2:
                label = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", cells[1]).strip()
                if label.casefold() in known:
                    labels.add(label.casefold())
    expected = {item.name.casefold() for item in selected}
    extra = {name for name in candidates if name.casefold() in labels and name.casefold() not in expected}
    return {"missing": [item.name for item in selected if item.name.casefold() not in labels],
            "unexpected": sorted(extra, key=str.casefold)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, help="Explicit exhaustive component file")
    parser.add_argument("--inline-file", type=Path, help="Temp file containing the prompt's inline list")
    parser.add_argument("--document", type=Path, help="Optional finished Markdown page to audit")
    parser.add_argument("--candidates-file", type=Path, help="Other known component names, one per line")
    args = parser.parse_args()
    try:
        scope = choose_scope(
            args.file.read_text(encoding="utf-8") if args.file else None,
            args.inline_file.read_text(encoding="utf-8") if args.inline_file else None,
        )
        if args.document:
            candidates = (args.candidates_file.read_text(encoding="utf-8").splitlines()
                          if args.candidates_file else [])
            scope["audit"] = audit_document(
                args.document.read_text(encoding="utf-8"),
                [Component(**item) for item in scope["components"]], candidates,
            )
        print(json.dumps(scope, indent=2, ensure_ascii=False))
        if args.document and (scope["audit"]["missing"] or scope["audit"]["unexpected"]):
            parser.exit(1, "[blocked] document scope requires review\n")
    except (ValueError, OSError, UnicodeError) as exc:
        parser.exit(2, f"[blocked] {exc}\n")


if __name__ == "__main__":
    main()