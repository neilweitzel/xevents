"""WS9 public-only invariant core. No private credentials or code execution."""

import fnmatch
import json
from pathlib import PurePosixPath
import re
import subprocess
from urllib.parse import unquote, urlsplit

REPO = "neilweitzel/xevents"
ADR_PATH = "docs/adr/0012-aggregation-boundary-transport.md"
WRITE_SET = ("data/aggregates/", "evidence-manifest.jsonl", "coverage-boundary-statement.md")


def require(value, code="invalid_contract"):
    if not value:
        raise ValueError(code)


def decode(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate_json_key")
            result[key] = value
        return result

    def nonfinite(_):
        raise ValueError("nonfinite_json")
    return json.loads(data, object_pairs_hook=unique, parse_constant=nonfinite)


def declaration(text):
    parts = text.split("### Boundary write set\n")
    require(len(parts) == 2, "boundary_section_missing_or_duplicate")
    section = parts[1].split("\n### ", 1)[0]
    paths = re.findall(r"^- `([^`]+)`", section, re.M)
    require(len(paths) == len(set(paths)) == 3 and set(paths) == set(WRITE_SET),
            "boundary_declaration_drift")
    return tuple(paths)


def safe_path(path):
    require(isinstance(path, str) and bool(path) and not path.startswith("/")
            and "\\" not in path and not any(ord(c) < 32 or ord(c) == 127 for c in path)
            and all(p not in ("", ".", "..") for p in path.split("/")), "invalid_path")
    return path


def touches(path, write_set=WRITE_SET):
    safe_path(path)
    return any(path == p.rstrip("/") or (p.endswith("/") and path.startswith(p))
               for p in write_set)


def permitted(path, write_set=WRITE_SET):
    safe_path(path)
    return any(path == p if not p.endswith("/") else
               path.startswith(p) and path.endswith(".jsonl") for p in write_set)


def changed_paths(files):
    require(isinstance(files, list) and 0 < len(files) < 3000, "invalid_file_count")
    names, result = set(), set()
    for row in files:
        require(isinstance(row, dict), "invalid_file_row")
        path = safe_path(row["filename"])
        require(path not in names, "duplicate_changed_file")
        names.add(path)
        require(row["status"] in ("added", "modified", "removed", "renamed", "copied", "changed"),
                "unknown_change_status")
        result.add(path)
        if row["status"] in ("renamed", "copied"):
            result.add(safe_path(row["previous_filename"]))
        else:
            require("previous_filename" not in row, "unexpected_previous_filename")
    return result


def boundary_related(files, branch, write_set=WRITE_SET):
    require(isinstance(branch, str) and bool(branch), "missing_branch")
    paths = changed_paths(files)
    return branch.startswith("boundary/") or any(touches(p, write_set) for p in paths)


def diff_gate(files, branch, adr):
    allowed = declaration(adr)
    paths = changed_paths(files)
    if boundary_related(files, branch, allowed):
        require(all(permitted(p, allowed) for p in paths), "outside_boundary_write_set")
    return True


def g5_gate(files, branch, adr):
    allowed = declaration(adr)
    if boundary_related(files, branch, allowed):
        # Deliberately no report parsing, private fetch, or success fallback.
        raise ValueError("public-proof-contract-not-implemented")
    return True


def api(path):
    result = subprocess.run(
        ["gh", "api", "--hostname", "github.com", f"repos/{REPO}/{path}"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60, check=False)
    require(result.returncode == 0, "public_api_failed")
    return decode(result.stdout)


def read_pr(number, expected_head, read=api):
    require(type(number) is int and 0 < number < 10**10, "invalid_pr_number")
    require(re.fullmatch(r"[0-9a-f]{40}", expected_head), "invalid_expected_head")
    before = read(f"pulls/{number}")
    require(before["state"] == "open" and before["base"]["ref"] == "main"
            and before["base"]["repo"]["full_name"] == REPO, "wrong_pr_target")
    require(before["head"]["sha"] == expected_head, "head_mismatch")
    count = before["changed_files"]
    require(type(count) is int and 0 < count < 3000, "unsupported_file_count")
    files = []
    for page in range(1, (count + 99) // 100 + 1):
        rows = read(f"pulls/{number}/files?per_page=100&page={page}")
        require(isinstance(rows, list) and len(rows) == min(100, count - len(files)),
                "incomplete_diff")
        files.extend(rows)
    after = read(f"pulls/{number}")
    for field in ("state", "base", "head", "changed_files"):
        require(before[field] == after[field], "pr_changed_during_check")
    changed_paths(files)
    require(re.fullmatch(r"[0-9a-f]{40}", before["base"]["sha"]), "invalid_base_sha")
    return before, files


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=60, check=False)
    require(result.returncode == 0, "git_read_failed")
    return result.stdout


def snapshot(root, revision):
    require(re.fullmatch(r"[0-9a-f]{40}", revision), "invalid_revision")
    result, total = {}, 0
    for entry in git(root, "ls-tree", "-rz", revision).split(b"\0"):
        if not entry:
            continue
        metadata, name = entry.split(b"\t", 1)
        mode, kind, oid = metadata.split()
        path = safe_path(name.decode("utf-8"))
        require(mode in (b"100644", b"100755") and kind == b"blob",
                "nonregular_tree_entry")
        data = git(root, "cat-file", "blob", oid.decode("ascii"))
        total += len(data)
        require(len(data) <= 5 * 1024 * 1024 and total <= 50 * 1024 * 1024
                and len(result) < 5000, "snapshot_limit")
        result[path] = data
    return result


def text(tree, path):
    return tree[path].decode("utf-8")


def metadata_status(body):
    # Only the preamble before the first second-level heading declares status.
    header = body.split("\n## ", 1)[0]
    matches = re.findall(r"^(?:- )?Status:\s*(.+)$", header, re.M)
    require(len(matches) == 1, "status_missing_or_duplicate")
    return matches[0].replace("*", "").strip().lower()


def historical_body(body):
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    header, sep, tail = body.partition("\n## ")
    header = re.sub(r"^(?:- )?(?:Status|Date|Deciders|Superseded-by):[^\n]*(?:\n|$)",
                    "", header, flags=re.M)
    return (header.strip() + sep + tail).strip()


def nygard(base, head):
    errors = []
    for path in sorted(base):
        if not re.fullmatch(r"docs/adr/\d{4}-[^/]+\.md", path) or path.endswith("0000-template.md"):
            continue
        old = text(base, path)
        old_status = metadata_status(old)
        if not (old_status == "accepted" or old_status.startswith("superseded")):
            continue
        if path not in head:
            errors.append({"path": path, "code": "protected_adr_deleted"})
            continue
        new = text(head, path)
        try:
            new_status = metadata_status(new)
            require(historical_body(old) == historical_body(new), "historical_body_changed")
            if new_status != old_status:
                require(new_status.startswith("superseded"), "protected_status_downgraded")
                header = new.split("\n## ", 1)[0]
                ids = re.findall(r"(?:Superseded-by:\s*|superseded by ADR\s+)(\d{4})",
                                 header, re.I)
                require(len(set(ids)) == 1, "supersession_reference_missing")
                targets = [p for p in head if re.fullmatch(
                    rf"docs/adr/{ids[0]}-[^/]+\.md", p)]
                require(len(targets) == 1 and targets[0] != path
                        and metadata_status(text(head, targets[0])) == "accepted",
                        "supersession_target_not_accepted")
        except (ValueError, UnicodeError) as exc:
            errors.append({"path": path, "code": str(exc)})
    return errors


def jsonl(raw, profile="standard"):
    require(isinstance(raw, bytes) and 0 < len(raw) <= 10 * 1024 * 1024
            and raw.endswith(b"\n") and not raw.startswith(b"\xef\xbb\xbf"), "invalid_jsonl")
    rows = [decode(line) for line in raw.decode("utf-8").splitlines()]
    require(rows and all(isinstance(row, dict) for row in rows), "invalid_jsonl_rows")
    header = rows[0]
    # Preserve existing versioned contracts; do not rewrite pinned data to make
    # an overly generic header rule pass. Unknown denylist files use standard.
    fields = {"standard": ("file_purpose", "schema_version"),
              "static": ("file_purpose",),
              "homoglyphs": ("table_version", "note")}
    require(profile in fields, "unknown_header_profile")
    require(all(isinstance(header.get(k), str) and bool(header[k].strip())
                for k in fields[profile]), "missing_metadata_header")
    require(not {"entity_id", "canonical_name", "raw_form", "normalized_form",
                 "source_char", "target_char"} & header.keys(), "data_in_metadata_header")
    for key in ("schema_version", "table_version"):
        if key in header:
            require(isinstance(header[key], str) and bool(header[key].strip()),
                    "invalid_header_version")
    return header, rows[1:]


def jsonl_audit(tree, private=False):
    patterns = ["evidence-manifest.jsonl", "data/aggregates/*.jsonl"]
    if private:
        patterns.append("denylist/*.jsonl")
    names = sorted(p for p in tree if any(fnmatch.fnmatchcase(p, pattern) for pattern in patterns))
    require("evidence-manifest.jsonl" in names, "manifest_missing")
    if private:
        require({"denylist/static.jsonl", "denylist/homoglyphs.jsonl"} <= set(names),
                "denylist_inputs_missing")
    for name in names:
        profile = {"denylist/static.jsonl": "static",
                   "denylist/homoglyphs.jsonl": "homoglyphs"}.get(name, "standard") if private else "standard"
        jsonl(tree[name], profile)
    return names


def prose(body):
    # Keep line numbers stable for human review.
    blank = lambda m: "\n" * m.group(0).count("\n")
    body = re.sub(r"```[^\n]*\n.*?```", blank, body, flags=re.S)
    return re.sub(r"<!--.*?-->", blank, body, flags=re.S)


def semantic_units(body):
    """Yield line-addressable prose blocks without joining unrelated list/table rows.

    This is a bounded Markdown reader, not a CommonMark parser or policy oracle.
    Wrapped list text stays with its item. Every nested item and table row starts
    a new unit; adjacent prose remains together so wrapped decision references
    still work. Reference existence is checked separately over the whole text.
    """
    start, lines = 1, []
    for number, line in enumerate(body.splitlines(), 1):
        boundary = re.match(r"^\s*(?:[-*+] |\d+[.)] |#{1,6} |\|)", line)
        if not line.strip() or boundary:
            if lines:
                yield start, "\n".join(lines)
                lines = []
        if line.strip():
            if not lines:
                start = number
            lines.append(line)
    if lines:
        yield start, "\n".join(lines)


def decision_words(unit):
    """Remove only explicit token examples and superseded/past-tense fragments.

    Active prose in the same unit remains checked. Nothing here exempts paths,
    ADR references, entire documents, or protected historical bodies.
    """
    token = (r'(?:"(?:TBD|UNDECIDED|proposed)"|“(?:TBD|UNDECIDED|proposed)”'
             r'|`(?:TBD|UNDECIDED|proposed)`)')
    words = re.sub(
        rf"\bdecision-consistency check \(no\s+{token}"
        rf"(?:\s*(?:,|/|\band\b)\s*(?:and\s+)?{token})*\s+language",
        "decision-consistency check (no placeholder language", unit, flags=re.I)
    words = re.sub(r"`[^`]*`", "", words)
    # A strikeout by itself is not a disposition. Require an immediately
    # following bold marker, optionally dated; unrelated/negated markers must
    # not hide another struck claim in the same unit.
    words = re.sub(
        r"~~(?:(?!~~).)*~~(?=\s+\*\*(?:DEFERRED|SUPERSEDED|LIFTED)"
        r"(?: \d{4}-\d{2}-\d{2})?\*\*)", "", words, flags=re.S)
    # The exact past-tense phrase does not reopen a previously settled rule.
    words = re.sub(r"\bwas a TBD\b", "was a settled question", words)
    # Quoting an active policy does not excuse it. Only a detector description
    # may quote these single-word tokens as its input vocabulary.
    words = re.sub(
        rf"\b(?:flags?|detects?|detecting)\s+{token}"
        rf"(?:\s*(?:,|/|\band\b)\s*(?:and\s+)?{token})*",
        "checks explicit tokens", words, flags=re.I)
    return words


def semantic_prose(body):
    """Remove preamble status values, preserving line numbers and other claims."""
    header, sep, tail = body.partition("\n## ")
    # Support the metadata spellings already used in repository documents.
    # Remove the declaration's value only, not the remainder of that line.
    header = re.sub(
        r"^(?:- )?(?:Status:|\*\*Status:\*\*|\*\*Status\*\*:)\s*"
        r"(?:\*\*)?(?:proposed|accepted|draft|superseded(?:-in-part)?)\b(?:\*\*)?",
        "", header, flags=re.M | re.I)
    return header + sep + tail


def docs_audit(tree, reference_tree=None):
    """Deterministic diagnostics, not a semantic truth oracle or debt allowlist."""
    references = {**(reference_tree or {}), **tree}
    adrs = {}
    for path in references:
        match = re.fullmatch(r"docs/adr/(\d{4})-[^/]+\.md", path)
        if match:
            adrs[match[1]] = path
    decisions = text(references, "docs/open-decisions.md") if "docs/open-decisions.md" in references else ""
    decided = {m.group(1) for m in re.finditer(
        r"^## (\d+)\.[^\n]*\n((?:(?!^## ).|\n)*?\bDECIDED\b[^\n]*)", decisions, re.M)}
    issues = []

    def finding(path, code, detail, line=1):
        row = {"path": path, "line": line, "code": code, "detail": detail}
        if row not in issues:
            issues.append(row)

    for path in sorted(tree):
        if not path.endswith(".md"):
            continue
        body = prose(text(tree, path))
        for match in re.finditer(r"\bADRs?\s+(\d{4})\b", body):
            number = match.group(1)
            if number not in adrs:
                finding(path, "unresolved_adr", number, body[:match.start()].count("\n") + 1)
        # Literal repo paths and local Markdown links. Templates/globs are
        # reported if unresolved, never silently treated as existing files.
        refs = {}
        for pattern in (r"`((?:docs/|tests/|scripts/|\.github/)[^`\n]+)`",
                        r"\[[^\]\n]+\]\(([^)\s]+)\)"):
            for match in re.finditer(pattern, body):
                refs.setdefault(match.group(1), body[:match.start()].count("\n") + 1)
        for ref in sorted(refs):
            parsed = urlsplit(ref)
            if parsed.scheme or parsed.netloc or ref.startswith("#"):
                continue
            name = unquote(parsed.path)
            if not name:
                continue
            if name.startswith(("docs/", "tests/", "scripts/", ".github/")):
                candidates = [name]
            else:
                candidates = [str(PurePosixPath(path).parent / name), name.lstrip("/")]
            # Resolve legitimate ../ links without permitting filesystem reads.
            normalized = []
            for candidate in candidates:
                parts = []
                for part in candidate.split("/"):
                    if part == "..":
                        if parts:
                            parts.pop()
                        else:
                            parts.append("..")
                    elif part not in ("", "."):
                        parts.append(part)
                normalized.append("/".join(parts))
            if not any(c in references or any(fnmatch.fnmatchcase(p, c) or
                                              fnmatch.fnmatchcase(p, c.rstrip("/") + "/*")
                                              for p in references) for c in normalized):
                finding(path, "unresolved_reference", ref, refs[ref])
        for line, unit in semantic_units(semantic_prose(body)):
            words = decision_words(unit)
            if not re.search(r"\b(?:TBD|UNDECIDED|proposed|to be decided)\b", words, re.I):
                continue
            ids = re.findall(r"\bADR\s+(\d{4})\b", words)
            accepted = [n for n in ids if n in adrs and
                        metadata_status(text(references, adrs[n])) == "accepted"]
            rulings = re.findall(r"(?:open-decisions\.md|decision)\s*#(\d+)", words, re.I)
            if accepted or set(rulings) & decided:
                finding(path, "possible_decision_language_drift",
                        ",".join(sorted(set(accepted)) + sorted(set(rulings) & decided)),
                        line)
    glossary_path = "docs/glossary.md"
    require(glossary_path in references, "glossary_missing")
    glossary = text(references, glossary_path)
    terms = re.findall(r"^- \*\*([^*]+)\*\*\s*[—:]", glossary, re.M)
    require(terms and len(terms) == len({t.casefold() for t in terms}), "invalid_glossary")
    usage = {term: sum(len(re.findall(r"(?<!\w)" + re.escape(term) + r"(?!\w)",
                                      prose(text(tree, p)), re.I))
                       for p in tree if p.endswith(".md")) for term in terms}
    return {"issues": issues, "glossary_terms": len(terms), "glossary_usage": usage}
