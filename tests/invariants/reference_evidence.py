"""Offline shadow evidence: bindings are not approvals or passing Docs QA."""

import ast
from collections import Counter
from hashlib import sha256
import re

import checks
from reference_inventory import digest, fields, validate_inventory

INVENTORY = "docs/reference-findings.json"
POLICY = "docs/reference-evidence.json"


def hashed(data):
    return sha256(data).hexdigest()


def section_bytes(data, heading):
    checks.require(isinstance(heading, str) and
                   re.fullmatch(r"#{1,6} [^\r\n]+", heading), "section_invalid")
    lines = data.decode("utf-8").splitlines(keepends=True)
    matches = [i for i, line in enumerate(lines) if line.rstrip("\r\n") == heading]
    checks.require(len(matches) == 1, "section_missing_or_duplicate")
    start = matches[0]
    level = len(heading.split(" ", 1)[0])
    end = next((i for i in range(start + 1, len(lines))
                if re.match(r"^#{1," + str(level) + r"} ", lines[i])), len(lines))
    return "".join(lines[start:end]).encode()


def binding(tree, item):
    """Validate exact bytes and sections, never execute target content."""
    checks.require(isinstance(item, dict), "binding_invalid")
    if item.get("type") == "file":
        fields(item, {"type", "path", "sha256", "section"})
        path = checks.safe_path(item["path"])
        digest(item["sha256"], 64)
        checks.require(path in tree and isinstance(tree[path], bytes) and tree[path],
                       "target_missing_or_empty")
        checks.require(hashed(tree[path]) == item["sha256"], "target_hash_changed")
        if item["section"] is not None:
            fields(item["section"], {"heading", "sha256"})
            digest(item["section"]["sha256"], 64)
            checks.require(hashed(section_bytes(tree[path], item["section"]["heading"])) ==
                           item["section"]["sha256"], "section_hash_changed")
        return tree[path]
    fields(item, {"type", "path", "members"})
    checks.require(item["type"] == "directory", "binding_type_invalid")
    path = checks.safe_path(item["path"])
    members = item["members"]
    checks.require(isinstance(members, dict) and 0 < len(members) < 5000,
                   "directory_members_invalid")
    checks.require(path not in tree, "directory_is_file")
    actual = {p for p in tree if p.startswith(path + "/")}
    checks.require(actual == set(members), "directory_members_changed")
    for name, expected in members.items():
        checks.safe_path(name)
        checks.require(name.startswith(path + "/"), "directory_member_outside")
        digest(expected, 64)
        checks.require(isinstance(tree[name], bytes) and tree[name] and
                       hashed(tree[name]) == expected, "directory_member_changed")
    return None


def test_binding(tree, item):
    fields(item, {"file", "class", "method"})
    data = binding(tree, item["file"])
    checks.require(item["file"]["type"] == "file" and
                   item["file"]["path"].endswith(".py"), "test_file_invalid")
    for name in (item["class"], item["method"]):
        checks.require(isinstance(name, str) and name.isidentifier(), "test_name_invalid")
    parsed = ast.parse(data)
    classes = [n for n in parsed.body if isinstance(n, ast.ClassDef) and
               n.name == item["class"]]
    checks.require(len(classes) == 1, "test_class_missing_or_duplicate")
    methods = [n for n in classes[0].body if isinstance(n, ast.FunctionDef) and
               n.name == item["method"]]
    checks.require(len(methods) == 1 and item["method"].startswith("test_"),
                   "test_method_missing_or_duplicate")


def template_binding(tree, row, rule):
    fields(rule, {"kind", "placeholder", "directory", "contract", "ids", "files"})
    checks.require(rule["placeholder"] in (
        "<batch-id>", "<fixture-id>", "${{ inputs.batch_id }}"), "placeholder_invalid")
    directory = rule["directory"]
    checks.require(isinstance(directory, dict) and directory.get("type") == "directory",
                   "template_directory_invalid")
    prefix = checks.safe_path(directory["path"])
    checks.require(row["finding"]["detail"] == prefix + "/" + rule["placeholder"] + "/",
                   "template_literal_mismatch")
    ids, files = rule["ids"], rule["files"]
    checks.require(isinstance(ids, list) and ids and
                   all(isinstance(i, str) and re.fullmatch(r"[0-9]{2}-[a-z0-9]+(?:-[a-z0-9]+)*", i)
                       for i in ids) and len(ids) == len(set(ids)), "template_ids_invalid")
    checks.require(isinstance(files, list) and files and
                   all(isinstance(f, str) and "/" not in f and checks.safe_path(f)
                       for f in files) and len(files) == len(set(files)), "template_files_invalid")
    contract = checks.decode(binding(tree, rule["contract"]))
    checks.require(isinstance(contract.get("roles"), dict) and
                   set(contract["roles"]) == set(ids), "template_contract_mismatch")
    expected = {f"{prefix}/{i}/{f}" for i in ids for f in files}
    checks.require(set(directory["members"]) == expected, "template_expansion_mismatch")
    binding(tree, directory)


def evaluate(row, rule, trees):
    checks.require(isinstance(rule, dict), "evidence_rule_invalid")
    kind, owner = row["kind"], row["owner"]
    if owner == "private" and "private" not in trees:
        fields(rule, {"kind"})
        checks.require(rule["kind"] == "owner-deferred", "private_rule_in_public")
        return "private-not-checked"
    tree = trees.get(owner)
    if kind == "external_public":
        fields(rule, {"kind", "repository", "path"})
        checks.require(rule["kind"] == "external" and isinstance(rule["repository"], str)
                       and re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", rule["repository"]),
                       "external_rule_invalid")
        checks.safe_path(rule["path"])
        checks.require(rule["path"] == row["finding"]["detail"], "external_path_mismatch")
        return "external-not-checked"
    checks.require(tree is not None, "owner_tree_missing")
    if kind == "planned":
        fields(rule, {"kind", "target", "deliverable", "milestone", "criteria"})
        checks.require(rule["kind"] == "planned" and
                       rule["target"] == row["finding"]["detail"] and
                       rule["milestone"] == row["milestone"], "planned_rule_mismatch")
        checks.safe_path(rule["target"])
        checks.require(isinstance(rule["deliverable"], str) and
                       re.fullmatch(r"[a-z][a-z0-9-]+", rule["deliverable"]),
                       "deliverable_invalid")
        checks.require(isinstance(rule["criteria"], list) and rule["criteria"] and
                       all(isinstance(c, str) and
                           re.fullmatch(r"AC" + row["milestone"][1:] + r"\.[0-9]+", c)
                           for c in rule["criteria"]) and
                       len(set(rule["criteria"])) == len(rule["criteria"]), "criteria_invalid")
        # No approved milestone registry or completion-proof contract yet.
        # Even an added target cannot manufacture completed acceptance.
        return ("planned-target-present-state-unknown" if rule["target"] in tree
                else "planned-target-absent-state-unknown")
    if kind == "preserved_history":
        fields(rule, {"kind", "decision", "authority"})
        checks.require(rule["kind"] == "history" and
                       rule["decision"] == row["finding"]["detail"], "history_rule_mismatch")
        authority = rule["authority"]
        checks.require(authority.get("path") == "docs/open-decisions.md" and
                       isinstance(authority.get("section"), dict), "history_authority_invalid")
        data = binding(tree, authority)
        heading = authority["section"]["heading"]
        checks.require(heading.startswith("## " + rule["decision"] + ". "),
                       "history_decision_mismatch")
        checks.require(re.search(
            rb"^- \*\*DECIDED [0-9]{4}-[0-9]{2}-[0-9]{2} by the user(?:[:* (])",
            section_bytes(data, heading), re.M) is not None, "history_ruling_missing")
        return "historical-ruling-bound"
    if kind == "example":
        fields(rule, {"kind", "test"})
        checks.require(rule["kind"] == "example", "example_rule_invalid")
        test_binding(tree, rule["test"])
        return "example-test-bound-not-executed"
    if kind == "bounded_template":
        checks.require(rule.get("kind") == "template", "template_rule_invalid")
        template_binding(tree, row, rule)
        return "template-targets-bound"
    if kind == "private_owned":
        fields(rule, {"kind", "target", "tests"})
        checks.require(rule["kind"] == "target", "target_rule_invalid")
        checks.require(rule["target"]["path"] == row["finding"]["detail"].rstrip("/"),
                       "target_path_mismatch")
        binding(tree, rule["target"])
        checks.require(isinstance(rule["tests"], list) and rule["tests"], "target_tests_missing")
        for test in rule["tests"]:
            test_binding(tree, test)
        return "owner-target-and-tests-bound-not-executed"
    fields(rule, {"kind", "target", "authority", "test"})
    checks.require(kind == "historical_target" and rule["kind"] == "mapping",
                   "mapping_rule_invalid")
    checks.require(row["finding"]["detail"] not in tree, "historical_target_now_exists")
    binding(tree, rule["target"])
    binding(tree, rule["authority"])
    checks.require(rule["test"]["file"] == rule["target"], "mapping_test_mismatch")
    test_binding(tree, rule["test"])
    return "execution-mapping-bound-receipt-required"


def inventory_and_rules(candidate, trusted, scope, reference_tree=None):
    checks.require(candidate.get(INVENTORY) == trusted.get(INVENTORY) and
                   candidate.get(POLICY) == trusted.get(POLICY), "candidate_policy_changed")
    inventory = checks.decode(trusted[INVENTORY])
    raw = checks.docs_audit(candidate, reference_tree)["issues"]
    validate_inventory(inventory, candidate, raw, scope)
    policy = checks.decode(trusted[POLICY])
    expected = {"schema_version", "mode", "scope", "inventory_sha256", "rules"}
    if scope == "private":
        expected |= {"public_inventory_sha256", "public_rules"}
    fields(policy, expected)
    checks.require(type(policy["schema_version"]) is int and policy["schema_version"] == 1
                   and policy["mode"] == "shadow-only" and policy["scope"] == scope,
                   "evidence_policy_invalid")
    digest(policy["inventory_sha256"], 64)
    checks.require(policy["inventory_sha256"] == hashed(trusted[INVENTORY]),
                   "inventory_binding_changed")
    checks.require(isinstance(policy["rules"], dict) and
                   set(policy["rules"]) == {r["id"] for r in inventory["records"]},
                   "evidence_coverage_mismatch")
    return inventory, policy, raw


def results(inventory, rules, trees):
    rows = []
    for row in inventory["records"]:
        try:
            status = evaluate(row, rules[row["id"]], trees)
        except (ValueError, TypeError, KeyError, SyntaxError, AttributeError, UnicodeError):
            # Never echo arbitrary candidate content or exception details.
            status = "evidence-invalid-or-stale"
        rows.append({"id": row["id"], "status": status})
    return rows


def report(scope, rows, raw_count):
    return {"mode": "shadow-only", "scope": scope, "raw_findings": raw_count,
            "resolved_findings": 0, "strict_failure_preserved": True,
            "counts": dict(sorted(Counter(r["status"] for r in rows).items())),
            "records": rows}


def audit_public(candidate, trusted):
    inventory, policy, raw = inventory_and_rules(candidate, trusted, "public")
    rows = results(inventory, policy["rules"], {"public": candidate})
    return report("public", rows, len(raw))


def audit_private(private, public, private_trusted, public_trusted):
    pub_inv, pub_policy, pub_raw = inventory_and_rules(public, public_trusted, "public")
    inv, policy, raw = inventory_and_rules(private, private_trusted, "private", public)
    digest(policy["public_inventory_sha256"], 64)
    checks.require(policy["public_inventory_sha256"] == hashed(public_trusted[INVENTORY]),
                   "public_inventory_binding_changed")
    owner_ids = {r["id"] for r in pub_inv["records"] if r["owner"] == "private"}
    checks.require(isinstance(policy["public_rules"], dict) and
                   set(policy["public_rules"]) == owner_ids, "private_overlay_scope_invalid")
    trees = {"public": public, "private": private}
    rows = results(pub_inv, {**pub_policy["rules"], **policy["public_rules"]}, trees)
    rows += results(inv, policy["rules"], trees)
    answer = report("private", rows, len(raw))
    answer["public_raw_findings"] = len(pub_raw)
    return answer
