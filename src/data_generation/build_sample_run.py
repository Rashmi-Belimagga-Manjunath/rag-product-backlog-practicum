"""
Build the SMALL sample and print it for design review.

This is a review artefact, not a pipeline step. It exists so the schema, the rendered
documents, and the ground-truth derivation can be inspected before decisions D6
(corpus scale) and D7 (query distribution) are made.

Run:  python -m src.data_generation.build_sample
"""

from __future__ import annotations

import json
import pathlib

from .build_sample import build_sample_model
from .render import render_corpus, summarise
from .ground_truth import build_ground_truth, verify_traceable

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
SAMPLE_DIR = PROJECT_ROOT / "data" / "synthetic" / "v0-sample"


def main() -> None:
    model = build_sample_model()
    documents = render_corpus(model)

    # Persist the sample so it can be inspected as files, not just as console output.
    source_dir = SAMPLE_DIR / "source_model"
    document_dir = SAMPLE_DIR / "documents"
    source_dir.mkdir(parents=True, exist_ok=True)
    document_dir.mkdir(parents=True, exist_ok=True)

    model.save(source_dir / "source_model.json")
    for document in documents:
        (document_dir / f"{document.document_id}.md").write_text(
            document.body, encoding="utf-8"
        )

    (document_dir / "_index.json").write_text(
        json.dumps(
            [
                {
                    "document_id": d.document_id,
                    "doc_type": d.doc_type,
                    "title": d.title,
                    "source_entity_type": d.source_entity_type,
                    "source_entity_id": d.source_entity_id,
                    "product_id": d.product_id,
                    "created_date": d.created_date,
                    "version": d.version,
                    "superseded_by": d.superseded_by_document_id,
                    "referenced_entity_ids": d.referenced_entity_ids,
                    "word_count": len(d.body.split()),
                }
                for d in documents
            ],
            indent=2,
        ),
        encoding="utf-8",
    )

    stats = summarise(documents)
    print("=" * 78)
    print("SAMPLE SOURCE MODEL + RENDERED DOCUMENTS")
    print("=" * 78)
    print(f"model version : {model.model_version}")
    print(f"seed          : {model.seed}")
    print(f"entities      : {len(model.products)} products, {len(model.features)} "
          f"features, {len(model.requirements)} requirements, {len(model.pbis)} PBIs, "
          f"{len(model.components)} components")
    print(f"                {len(model.tickets)} tickets, {len(model.decisions)} "
          f"decisions, {len(model.meeting_notes)} notes, {len(model.runbooks)} runbooks")
    print(f"relationships : {len(model.dependencies)} dependencies, "
          f"{len(model.conflicts)} conflicts")
    print()
    print("DOCUMENT MIX")
    for doc_type, count in sorted(stats["by_doc_type"].items()):
        print(f"  {doc_type:<16} {count:>3}")
    print(f"  {'TOTAL':<16} {stats['total_documents']:>3}  "
          f"({stats['total_words']} words)")

    # Show the structural heterogeneity that the design depends on.
    lengths = sorted(len(d.body.split()) for d in documents)
    print()
    print(f"DOCUMENT LENGTH SPREAD: min {lengths[0]} words, "
          f"median {lengths[len(lengths)//2]}, max {lengths[-1]} words")
    print("  (this range is deliberate: it is what makes chunking behaviour visible)")

    # Demonstrate ground-truth derivation on two deliberately different query types.
    print()
    print("=" * 78)
    print("GROUND-TRUTH DERIVATION — two worked examples")
    print("=" * 78)

    examples = [
        {
            "query_id": "Q-EXAMPLE-1",
            "query": ("Which documents describe collecting tax details later in the "
                      "onboarding ramp rather than at first login?"),
            "query_type": "information_retrieval",
            "lexical_difficulty": "moderate",
            "target": "PBI-A-011",
            "include_referenced": False,
        },
        {
            "query_id": "Q-EXAMPLE-2",
            "query": ("What is blocking the bulk timesheet approval work, and which "
                      "systems does it need?"),
            "query_type": "dependency_identification",
            "lexical_difficulty": "hard",
            "target": "PBI-A-013",
            "include_referenced": True,
        },
    ]

    for example in examples:
        truth = build_ground_truth(
            query_id=example["query_id"],
            query=example["query"],
            query_type=example["query_type"],
            lexical_difficulty=example["lexical_difficulty"],
            target_entity_id=example["target"],
            model=model,
            documents=documents,
            include_referenced_as_relevant=example["include_referenced"],
        )
        problems = verify_traceable(truth, model, documents)

        print()
        print(f"{truth.query_id}  [{truth.query_type} / {truth.lexical_difficulty}]")
        print(f"  query            : {truth.query}")
        print(f"  target entity    : {truth.target_entity_id}")
        print(f"  relevant docs    : {truth.relevant_document_ids}")
        print(f"  distractors      : {truth.distractor_document_ids or 'none'}")
        print(f"  expected deps    : {truth.expected_dependencies or 'none'}")
        for dependency_id in truth.expected_dependencies:
            dependency = next(d for d in model.dependencies
                              if d.dependency_id == dependency_id)
            visibility = "explicit in docs" if dependency.is_explicit_in_docs \
                else "IMPLICIT (not written anywhere)"
            print(f"      {dependency_id}  {visibility}")
        print(f"  traceable        : {'OK' if not problems else problems}")

    # Show the lexical divergence control working, since it is the design's
    # validity-critical element and is easy to get wrong.
    print()
    print("=" * 78)
    print("LEXICAL DIVERGENCE — the validity control, in practice")
    print("=" * 78)
    print()
    print("A document can legitimately contain BOTH registers: real tickets cite the")
    print("feature name in triage while the customer describes the symptom in their own")
    print("words. So this reports which registers appear, not a single verdict.")
    print()

    for feature in model.features:
        product = model.get_product(feature.product_id)
        print(f"{feature.feature_id}  {feature.name}  "
              f"({product.name}, {product.documentation_maturity})")
        print(f"  formal term : {feature.formal_term}")
        print(f"  colloquial  : {', '.join(feature.colloquial_terms)}")
        print()
        for document in documents:
            if feature.feature_id not in document.referenced_entity_ids \
                    and document.source_entity_id != feature.feature_id:
                continue
            lowered = document.body.lower()
            formal_here = feature.formal_term.lower() in lowered
            colloquial_here = any(
                term.lower() in lowered for term in feature.colloquial_terms
            )
            if formal_here and colloquial_here:
                register = "both"
            elif formal_here:
                register = "formal only"
            elif colloquial_here:
                register = "colloquial only"
            else:
                register = "neither"
            print(f"    {document.document_id}  {document.doc_type:<14} {register}")
        print()

    # The check that actually matters for the experiment: does the QUERY wording share
    # vocabulary with the target document? If it does, BM25 gets a free pass and the
    # comparison is not testing what it claims to test.
    print("=" * 78)
    print("QUERY-TO-DOCUMENT VOCABULARY OVERLAP — the check that matters")
    print("=" * 78)
    print()
    print("Overlap is computed on content words after removing stopwords. A 'hard' query")
    print("should overlap very little; a high overlap means the query is too easy and the")
    print("lexical-difficulty label is wrong.")
    print()

    import re

    stopwords = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being", "of",
        "to", "in", "on", "at", "for", "with", "and", "or", "but", "if", "than", "then",
        "so", "as", "by", "from", "it", "its", "this", "that", "these", "those",
        "which", "what", "who", "whom", "how", "why", "when", "where", "do", "does",
        "did", "can", "could", "should", "would", "will", "shall", "may", "might",
        "i", "we", "they", "he", "she", "you", "not", "no", "any", "all", "more",
        "most", "some", "such", "only", "own", "same", "too", "very", "s", "t",
        "just", "now", "have", "has", "had", "having", "there", "their", "them",
    }

    def content_words(text: str) -> set[str]:
        words = re.findall(r"[a-z0-9\-]+", text.lower())
        return {w for w in words if w not in stopwords and len(w) > 2}

    for example in examples:
        query_words = content_words(example["query"])
        truth = build_ground_truth(
            query_id=example["query_id"],
            query=example["query"],
            query_type=example["query_type"],
            lexical_difficulty=example["lexical_difficulty"],
            target_entity_id=example["target"],
            model=model,
            documents=documents,
            include_referenced_as_relevant=example["include_referenced"],
        )
        print(f"{example['query_id']}  labelled: {example['lexical_difficulty']}")
        print(f"  query: {example['query']}")
        for document_id in truth.relevant_document_ids:
            document = next(d for d in documents if d.document_id == document_id)
            document_words = content_words(document.body)
            shared = query_words & document_words
            ratio = len(shared) / len(query_words) if query_words else 0.0
            print(f"    {document_id} ({document.doc_type}) "
                  f"overlap {ratio:.0%}  shared: {sorted(shared) or 'none'}")
        print()



if __name__ == "__main__":
    main()

print()
print("=" * 78)
print(f"Written to: {SAMPLE_DIR}")
print("=" * 78)
