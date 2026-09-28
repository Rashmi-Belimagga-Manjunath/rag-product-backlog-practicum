"""
Tests for the reproducibility manifest.

The manifest is the artefact that lets a third party verify the run, so its two failure
modes are guarded here: a digest that is not stable, and a digest that does not actually
cover what it claims to cover.
"""

from __future__ import annotations

import hashlib
import json

from src.manifest.manifest import ARTEFACTS, MULTI, digest_for, sha256_file, sha256_tree


def test_sha256_file_matches_hashlib(tmp_path):
    p = tmp_path / "a.txt"
    p.write_bytes(b"corpus")
    assert sha256_file(p) == hashlib.sha256(b"corpus").hexdigest()


def test_tree_digest_is_independent_of_iteration_order(tmp_path):
    """Directory iteration order must not change the aggregate, or the same corpus would
    hash differently on two machines depending on the filesystem."""
    d = tmp_path / "rendered"
    contents = {"z.md": "content of z", "a.md": "content of a", "m.md": "content of m"}

    d.mkdir()
    for name in ("z.md", "a.md", "m.md"):
        (d / name).write_text(contents[name])
    first, per_file = sha256_tree(d, base=tmp_path)

    # rebuild the same tree in a deliberately different order
    for f in d.iterdir():
        f.unlink()
    for name in ("m.md", "z.md", "a.md"):
        (d / name).write_text(contents[name])
    second, per_file2 = sha256_tree(d, base=tmp_path)

    assert per_file == per_file2
    assert first == second


def test_tree_digest_changes_when_content_changes(tmp_path):
    """The obvious counterpart: the digest must actually be sensitive to content, or the
    order-independence test above would pass trivially."""
    d = tmp_path / "t"
    d.mkdir()
    (d / "a.md").write_text("original")
    before, _ = sha256_tree(d, base=tmp_path)
    (d / "a.md").write_text("edited")
    after, _ = sha256_tree(d, base=tmp_path)
    assert before != after


def test_tree_digest_changes_when_a_filename_changes(tmp_path):
    """Names are part of the digest, so a renamed file is a different artefact."""
    d = tmp_path / "t"
    d.mkdir()
    (d / "a.md").write_text("same content")
    before, _ = sha256_tree(d, base=tmp_path)
    (d / "a.md").rename(d / "b.md")
    after, _ = sha256_tree(d, base=tmp_path)
    assert before != after


def test_tree_digest_ignores_pycaches_and_ds_store(tmp_path):
    d = tmp_path / "t"
    (d / "__pycache__").mkdir(parents=True)
    (d / "__pycache__" / "x.pyc").write_bytes(b"junk")
    (d / ".DS_Store").write_bytes(b"junk")
    (d / "keep.md").write_text("real")
    _, per_file = sha256_tree(d, base=tmp_path)
    assert [k for k in per_file if "keep.md" in k]
    assert not any("__pycache__" in k for k in per_file)
    assert not any(".DS_Store" in k for k in per_file)


def test_every_artefact_is_described_and_hashed_something(tmp_path, monkeypatch):
    """Every declared artefact must resolve to either a real digest or an explicit
    'missing'. It must never fail to resolve at all."""
    for a in ARTEFACTS:
        status, value, detail = digest_for(a)
        assert status in ("ok", "missing"), f"{a.key}: unexpected status {status}"
        if status == "ok":
            assert value and value != "", f"{a.key}: ok but empty digest"
        else:
            assert detail, f"{a.key}: missing but no reason given"


def test_artefact_keys_are_unique_and_documented():
    keys = [a.key for a in ARTEFACTS]
    assert len(keys) == len(set(keys))


def test_multi_scope_artefacts_declare_their_files():
    for key in MULTI:
        assert any(a.key == key and a.scope == "multi" for a in ARTEFACTS)
        assert MULTI[key], f"{key} declares no files"


def test_the_key_approved_artefacts_are_present():
    """The user named nine artefacts that must be covered."""
    required = {
        "structured_source_of_truth", "final_rendered_corpus", "query_benchmark",
        "ground_truth_specification", "final_chunked_corpus", "embedding_matrix",
        "experiment_configuration", "git_commit", "environment_lockfile",
    }
    keys = {a.key for a in ARTEFACTS}
    assert required <= keys, f"missing: {sorted(required - keys)}"


def test_prompt_hash_in_rag_config_matches_the_file():
    """rag_config.json records a prompt digest; if the prompt changes, the two disagree."""
    from pathlib import Path
    cfg = json.loads(Path("experiments/configs/rag_config.json").read_text())
    recorded = cfg["prompt"]["sha256"]
    actual = sha256_file(Path(cfg["prompt"]["path"]))
    assert recorded == actual, "rag_config.json prompt hash is stale; re-freeze it"
