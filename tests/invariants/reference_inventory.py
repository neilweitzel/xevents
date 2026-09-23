"""Review-inventory validation only; never a Docs QA waiver or target verifier.

The caller supplies an audited snapshot and that snapshot's raw diagnostics.
No checkout, filesystem, network, milestone completion, or approval is inferred.
"""

from collections import Counter
from hashlib import sha256
import re

from checks import require, safe_path


KINDS = frozenset({
    "preserved_history", "external_public", "private_owned", "planned",
    "bounded_template", "example", "historical_target",
})
TOP = frozenset({"schema_version", "status", "scope", "baseline_sha",
                 "public_baseline_sha", "records"})
ROW = frozenset({"id", "prior_id", "finding", "source_sha256", "kind",
                 "owner", "milestone", "action", "authority"})
FINDING = frozenset({"path", "line", "code", "detail"})


def fields(value, expected):
    require(isinstance(value, dict) and set(value) == expected,
            "inventory_fields_invalid")


def nonempty(value):
    require(isinstance(value, str) and bool(value.strip()),
            "inventory_text_invalid")


def digest(value, length):
    require(isinstance(value, str) and
            re.fullmatch(rf"[0-9a-f]{{{length}}}", value) is not None,
            "inventory_digest_invalid")


def identity(finding):
    fields(finding, FINDING)
    safe_path(finding["path"])
    require(finding["path"].endswith(".md"), "inventory_source_not_markdown")
    require(type(finding["line"]) is int and finding["line"] > 0,
            "inventory_line_invalid")
    require(finding["code"] in (
        "unresolved_reference", "possible_decision_language_drift"),
        "inventory_code_invalid")
    nonempty(finding["detail"])
    return tuple(finding[k] for k in ("path", "line", "code", "detail"))


def validate_inventory(inventory, tree, raw_issues, scope):
    """Validate a proposal's shape, source anchors and exact diagnostic coverage.

    Baseline SHAs are provenance labels, not attestations: a trusted caller must
    load the claimed commits separately. Hashes bind each entire source document
    in the supplied tree. Output explicitly leaves every raw finding unresolved.
    """
    fields(inventory, TOP)
    require(type(inventory["schema_version"]) is int and
            inventory["schema_version"] == 1, "inventory_version_invalid")
    require(inventory["status"] == "proposal-only", "inventory_not_proposal")
    require(scope in ("public", "private") and inventory["scope"] == scope,
            "inventory_scope_mismatch")
    digest(inventory["baseline_sha"], 40)
    if scope == "public":
        require(inventory["public_baseline_sha"] is None,
                "inventory_public_ref_unexpected")
    else:
        digest(inventory["public_baseline_sha"], 40)
    require(isinstance(raw_issues, list), "inventory_issues_invalid")
    actual = [identity(i) for i in raw_issues]
    require(len(set(actual)) == len(actual), "inventory_duplicate_diagnostic")
    require(isinstance(inventory["records"], list), "inventory_rows_invalid")
    ids, prior_ids, covered = set(), set(), set()
    for row in inventory["records"]:
        fields(row, ROW)
        prefix = "P" if scope == "public" else "I"
        require(isinstance(row["id"], str) and
                re.fullmatch(prefix + r"R-[0-9]{2}", row["id"]),
                "inventory_id_invalid")
        require(isinstance(row["prior_id"], str) and
                re.fullmatch(prefix + r"[0-9]{2}", row["prior_id"]),
                "inventory_prior_id_invalid")
        require(row["id"] not in ids and row["prior_id"] not in prior_ids,
                "inventory_duplicate_id")
        ids.add(row["id"])
        prior_ids.add(row["prior_id"])
        key = identity(row["finding"])
        require(key not in covered, "inventory_duplicate_finding")
        covered.add(key)
        path = row["finding"]["path"]
        digest(row["source_sha256"], 64)
        require(path in tree and isinstance(tree[path], bytes),
                "inventory_source_missing")
        require(sha256(tree[path]).hexdigest() == row["source_sha256"],
                "inventory_source_changed")
        require(row["finding"]["line"] <= len(tree[path].splitlines()),
                "inventory_line_out_of_bounds")
        require(isinstance(row["kind"], str) and row["kind"] in KINDS,
                "inventory_kind_invalid")
        require(row["owner"] in ("public", "private", "external-public"),
                "inventory_owner_invalid")
        nonempty(row["action"])
        nonempty(row["authority"])
        if row["kind"] == "planned":
            require(isinstance(row["milestone"], str) and
                    re.fullmatch(r"M[1-8]", row["milestone"]),
                    "inventory_milestone_required")
        else:
            require(row["milestone"] is None, "inventory_milestone_unexpected")
        if row["kind"] in ("private_owned", "historical_target", "bounded_template"):
            require(row["owner"] == "private", "inventory_owner_kind_mismatch")
        elif row["kind"] == "external_public":
            require(row["owner"] == "external-public", "inventory_owner_kind_mismatch")
        elif row["kind"] == "preserved_history":
            require(row["owner"] == "public", "inventory_owner_kind_mismatch")
        if row["kind"] == "preserved_history":
            require(row["finding"]["code"] == "possible_decision_language_drift",
                    "inventory_kind_code_mismatch")
        else:
            require(row["finding"]["code"] == "unresolved_reference",
                    "inventory_kind_code_mismatch")
    require(covered == set(actual), "inventory_coverage_mismatch")
    return {
        "inventory_valid": True,
        "scope": scope,
        "proposal_only": True,
        "raw_findings": len(actual),
        "resolved_findings": 0,
        "counts_by_kind": dict(sorted(Counter(
            r["kind"] for r in inventory["records"]).items())),
    }
