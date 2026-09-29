import pytest

from src.retrieval.units import (
    RetrievalUnit,
    RetrievalUnitSet,
    load_frozen_units,
    parse_citation,
    render_passages,
    tokens,
)


def make_unit(chunk_id, text, source_entity_id="", entity_ids=(), document_id=None):
    document_id = document_id or chunk_id.rsplit("-C", 1)[0]
    index = int(chunk_id.rsplit("-C", 1)[1])
    return RetrievalUnit(
        chunk_id=chunk_id,
        document_id=document_id,
        chunk_index=index,
        text=text,
        source_entity_id=source_entity_id,
        entity_ids=list(entity_ids),
        version_status="current",
    )


class TestTokens:
    def test_lowercases_and_splits_word_chars(self):
        assert tokens("Tax at First LOGIN?") == ["tax", "at", "first", "login"]

    def test_keeps_apostrophes(self):
        assert tokens("doesn't work") == ["doesn't", "work"]

    def test_drops_punctuation(self):
        assert tokens("a—b,c;d:") == ["a", "b", "c", "d"]


class TestCitation:
    def test_citation_from_chunk(self):
        unit = make_unit("DOC-PRD-A-01-v2-C0", "hello")
        assert unit.citation == "DOC-PRD-A-01-v2#C0"

    def test_parse_citation_roundtrip(self):
        document_id, index = parse_citation("DOC-PRD-A-01-v2#C0")
        assert (document_id, index) == ("DOC-PRD-A-01-v2", 0)

    def test_parse_citation_rejects_bad_forms(self):
        for bad in ["no-hash", "DOC#Cx", "#C0", "DOC-1#C"]:
            with pytest.raises(ValueError):
                parse_citation(bad)


class TestPassages:
    def test_render_has_number_id_status(self):
        unit = make_unit("DOC-PRD-A-01-v2-C0", "Body line")
        passage = render_passages([unit])[0]
        text = passage.render()
        assert text.startswith("Passage 1\nPassage ID: DOC-PRD-A-01-v2#C0\nStatus: current\n")
        assert "Body line" in text

    def test_render_shows_superseded_target(self):
        unit = make_unit("DOC-PRD-A-01-C0", "Old", )
        from dataclasses import replace
        unit = replace(unit, version_status="superseded", superseded_by="DOC-PRD-A-01-v2")
        text = render_passages([unit])[0].render()
        assert "superseded (replaced by DOC-PRD-A-01-v2)" in text


class TestFrozenUnitsFile:
    def test_loads_frozen_chunks_from_disk(self):
        units = load_frozen_units()
        assert len(units.units) == 272
        assert units.by_document  # every document has at least one unit

    def test_chunk_id_order_is_deterministic(self):
        first = load_frozen_units()
        second = load_frozen_units()
        assert first.chunk_id_order == second.chunk_id_order

    def test_relevant_chunk_ids_follow_frozen_order(self):
        units = load_frozen_units()
        target = [units.documents[0], units.documents[1]]
        ids = units.relevant_chunk_ids(target)
        assert ids == [u.chunk_id for u in units.units if u.document_id in target]

    def test_entity_cover_excludes_blank(self):
        unit = make_unit("X-C0", "", source_entity_id="", entity_ids=["y"])
        assert unit.entity_cover() == {"y"}

    def test_frozen_units_roundtrip_citation(self):
        units = load_frozen_units()
        for unit in units.units[:20]:
            document_id, index = parse_citation(unit.citation)
            assert document_id == unit.document_id
            assert index == unit.chunk_index