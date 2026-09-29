"""
Build and verify the reproducibility manifest (docs/reproducibility.md).

Run:  python3 -m src.manifest.manifest            # build data/manifest/FREEZE.json
      python3 -m src.manifest.manifest --verify   # recompute and compare
      python3 -m src.manifest.manifest --status   # what exists, what is missing

Every digest is SHA-256. Nothing is ever edited in place: a changed frozen artefact means a
new manifest version plus a recorded protocol deviation.

The final corpus does not exist yet, so most artefacts are reported MISSING. That is the
correct state before the freeze, and --status distinguishes "missing" from "failing".
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(".")
MANIFEST_DIR = ROOT / "data" / "manifest"
FREEZE_JSON = MANIFEST_DIR / "FREEZE.json"
FREEZE_MD = MANIFEST_DIR / "FREEZE.md"
HASH_REPO = "https://github.com/Rashmi-Belimagga-Manjunath/rag-product-backlog-practicum"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def sha256_tree(directory: Path, base: Path = None) -> tuple:
    """Aggregate digest over a directory: hash the sorted list of per-file digests.

    Sorting makes the value independent of filesystem iteration order, which would
    otherwise make the same tree hash differently on two machines.

    `base` is the directory paths are recorded relative to. It defaults to the repository
    root, because the recorded names must be repo-relative to be comparable. It is
    overridable so the function can be exercised on a tree outside the repository.
    """
    base = base if base is not None else ROOT
    # Note: Path(".DS_Store").suffix is "", so a suffix test would NOT exclude it.
    # Filter on the filename itself.
    junk_names = {".DS_Store", "Thumbs.db"}
    files = sorted(p for p in directory.rglob("*") if p.is_file()
                   and "__pycache__" not in p.parts and p.name not in junk_names)
    per_file = {p.relative_to(base).as_posix(): sha256_file(p) for p in files}
    h = hashlib.sha256()
    for name in sorted(per_file):
        h.update(name.encode())
        h.update(per_file[name].encode())
    return h.hexdigest(), per_file


def git(*args) -> str:
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:
        return ""


def tree_clean() -> bool:
    return git("status", "--porcelain") == ""


@dataclass(frozen=True)
class Artefact:
    key: str
    what: str
    path: str
    scope: str = "file"
    committed: bool = True


# The frozen artefact list. Order is the manifest order.
ARTEFACTS: tuple = (
    Artefact("structured_source_of_truth",
             "Structured source of truth (single JSON serialisation of the entity model)",
             "data/corpus/v1/source_model.json"),
    Artefact("final_rendered_corpus",
             "Final rendered corpus (aggregate over sorted per-file digests)",
             "data/corpus/v1/rendered/", scope="tree"),
    Artefact("query_benchmark",
             "Query benchmark machine specification (authoritative) + generated document",
             "src/benchmark/query_spec.py", scope="multi",
             ),
    Artefact("ground_truth_specification",
             "Ground-truth schema, selectors and validator",
             "src/ground_truth/schema.py", scope="multi"),
    Artefact("final_chunked_corpus",
             "Final chunked corpus + frozen chunking decision",
             "data/corpus/v1/chunks/chunks.json", scope="multi"),
    Artefact("embedding_matrix",
             "Embedding matrix (raw array bytes; no dated model snapshot is published)",
             "data/embeddings/v1-corpus/embeddings.npy"),
    Artefact("embedding_metadata",
             "Embedding metadata, including the positional chunk_id_order",
             "data/embeddings/v1-corpus/embeddings.meta.json"),
    Artefact("experiment_configuration",
             "Frozen experiment configuration (embedding, RAG, BM25)",
             "experiments/configs/embedding_config.json", scope="multi"),
    Artefact("rag_prompt",
             "Frozen RAG system prompt (hashed separately: it is prose and is edited most)",
             "experiments/configs/rag_prompt.txt"),
    Artefact("git_commit",
             "Source-code commit SHA (content-addressed already; recorded, not committed)",
             "<git HEAD>", scope="git"),
    Artefact("environment_lockfile",
             "Dependency/environment lockfile + resolved pip freeze",
             "uv.lock", scope="lockfile"),
    Artefact("environment_record",
             "Python version, OS, package versions, exact gpt-4o-mini model string",
             "data/manifest/environment.json"),
    Artefact("validation_reports",
             "C1-C8 coherence, ground-truth validation and spec-sync reports",
             "data/manifest/validation/", scope="tree"),
    Artefact("run_outputs",
             "Per-system retrieval logs and generated responses (retrieval logged separately)",
             "experiments/runs/", scope="tree"),
)

# Extra paths for scope="multi" entries.
MULTI = {
    "query_benchmark": ["src/benchmark/query_spec.py", "src/benchmark/render_spec_doc.py",
                        "src/benchmark/selectors.py", "docs/query_specification.md"],
    "ground_truth_specification": ["src/ground_truth/schema.py",
                                   "src/benchmark/selectors.py",
                                   "src/benchmark/validate_ground_truth.py"],
    "final_chunked_corpus": ["data/corpus/v1/chunks/chunks.json", "CHUNKING_DECISION.md"],
    "experiment_configuration": ["experiments/configs/embedding_config.json",
                                "experiments/configs/rag_config.json",
                                "experiments/configs/bm25_config.json"],
}


def digest_for(artefact: Artefact) -> tuple:
    """Returns (status, value, detail). status is 'ok', 'missing' or 'absent'."""
    if artefact.scope == "git":
        sha = git("rev-parse", "HEAD")
        return ("ok" if sha else "missing"), sha, {"branch": git("rev-parse",
                          "--abbrev-ref", "HEAD"),
                          "working_tree_clean": tree_clean()}
    if artefact.scope == "lockfile":
        lock = Path("uv.lock") if Path("uv.lock").exists() else Path("requirements.txt")
        if not lock.exists():
            return "missing", "", {"note": "no lockfile present"}
        extra = git_hash_freeze()
        return "ok", sha256_file(lock), {"lockfile": str(lock), "pip_freeze_sha256": extra}
    if artefact.scope == "tree":
        d = ROOT / artefact.path
        if not d.exists():
            return "missing", "", {"path": artefact.path}
        agg, per_file = sha256_tree(d)
        return "ok", agg, {"file_count": len(per_file), "path": artefact.path}
    if artefact.scope == "multi":
        paths = MULTI[artefact.key]
        h = hashlib.sha256()
        present = 0
        for rel in paths:
            p = ROOT / rel
            if not p.exists():
                return "missing", "", {"missing_path": rel, "expected": paths}
            h.update(rel.encode())
            h.update(sha256_file(p).encode())
            present += 1
        return "ok", h.hexdigest(), {"files": paths, "count": present}
    p = ROOT / artefact.path
    if not p.exists():
        return "missing", "", {"path": artefact.path}
    return "ok", sha256_file(p), {"path": artefact.path}


def git_hash_freeze() -> str:
    try:
        out = subprocess.run([sys.executable, "-m", "pip", "freeze"],
                             capture_output=True, text=True, check=True).stdout
        return hashlib.sha256(out.encode()).hexdigest()
    except Exception:
        return ""


def build_entries() -> list:
    entries = []
    for a in ARTEFACTS:
        status, value, detail = digest_for(a)
        entries.append({
            "artefact": a.key,
            "what": a.what,
            "path": a.path,
            "algorithm": "sha256",
            "scope": a.scope,
            "committed_to_git": a.committed,
            "status": status,
            "value": value,
            "detail": detail,
        })
    return entries


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build(version: int = 1) -> int:
    entries = build_entries()
    payload = {
        "manifest_version": version,
        "captured_at": _timestamp(),
        "repository": HASH_REPO,
        "git_commit": git("rev-parse", "HEAD"),
        "working_tree_clean": tree_clean(),
        "complete": all(e["status"] == "ok" for e in entries),
        "artefacts": entries,
    }
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    FREEZE_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    lines = [f"# Reproducibility manifest v{version}", "",
             f"Captured: {payload['captured_at']}", "",
             f"Git commit: `{payload['git_commit']}`  ",
             f"Working tree clean: **{payload['working_tree_clean']}**  ",
             f"Complete: **{payload['complete']}**", "",
             "| Artefact | Algorithm | Status | Committed |", "|---|---|---|---|"]
    for e in entries:
        lines.append(f"| {e['artefact']} | {e['algorithm']} | {e['status']} | "
                     f"{'yes' if e['committed_to_git'] else 'recorded only'} |")
    lines += ["", "Digests are in `FREEZE.json`, which is authoritative.", ""]
    FREEZE_MD.write_text("\n".join(lines))
    missing = [e["artefact"] for e in entries if e["status"] != "ok"]
    print(f"wrote {FREEZE_JSON} and {FREEZE_MD}")
    print(f"artefacts ok: {len(entries) - len(missing)}/{len(entries)}")
    if missing:
        print("not yet present (expected before the final freeze):")
        for m in missing:
            print(f"  - {m}")
    if not payload["working_tree_clean"]:
        print("WARNING: working tree is not clean; a freeze taken now is not reproducible.")
    return 0


def commit_is_ancestor(commit: str, ref: str) -> bool:
    """True when `commit` is an ancestor of (or equal to) `ref`."""
    if not commit:
        return False
    try:
        return subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, ref],
            capture_output=True,
        ).returncode == 0
    except Exception:
        return False


def verify() -> int:
    if not FREEZE_JSON.exists():
        print(f"FAIL: {FREEZE_JSON} does not exist. Nothing to verify.")
        return 1
    recorded = json.loads(FREEZE_JSON.read_text())
    failures = []
    for e in recorded["artefacts"]:
        if e["status"] != "ok":
            continue
        if e["artefact"] == "git_commit":
            # The recorded git_commit is the freeze commit; the manifest itself is
            # committed afterwards (a later commit cannot change its own SHA), so it is
            # verified by the commit-semantics checks below, not by head comparison.
            continue
        artefact = next(a for a in ARTEFACTS if a.key == e["artefact"])
        status, value, _ = digest_for(artefact)
        if status != "ok":
            failures.append(f"{e['artefact']}: was recorded but is now MISSING")
        elif value != e["value"]:
            failures.append(f"{e['artefact']}: CHANGED\n    recorded {e['value']}\n    now      {value}")
    recorded_commit = str(recorded.get("git_commit") or "")
    if not recorded_commit:
        failures.append("manifest records no git_commit")
    elif not commit_is_ancestor(recorded_commit, "HEAD"):
        failures.append(
            f"recorded freeze commit {recorded_commit} is not an ancestor of HEAD; "
            "the frozen state is no longer part of this history")
    elif not commit_is_ancestor(recorded_commit, "origin/main"):
        failures.append(f"recorded freeze commit {recorded_commit} is not in origin/main")
    print(f"manifest v{recorded['manifest_version']} captured {recorded['captured_at']}")
    print(f"git commit recorded: {recorded_commit}")
    print(f"git commit now:      {git('rev-parse', 'HEAD')}")
    if not failures:
        print("VERIFY: OK - every recorded digest matches and the freeze commit is in the pushed history.")
        return 0
    print("VERIFY: FAILED")
    for f in failures:
        print(f"  - {f}")
    return 1


def status() -> int:
    print(f"{'artefact':34} {'scope':10} {'status':8} committed")
    print("-" * 68)
    for a in ARTEFACTS:
        st, value, _ = digest_for(a)
        print(f"{a.key:34} {a.scope:10} {st:8} {'yes' if a.committed else 'no'}")
    return 0


if __name__ == "__main__":
    if "--verify" in sys.argv:
        sys.exit(verify())
    if "--status" in sys.argv:
        sys.exit(status())
    sys.exit(build())
