# Excluded assessment source material

Some files in this project directory are intentionally **not** tracked by git. They
remain on the Desktop as the primary record, but are never pushed to GitHub.

## What is excluded, and why

| File | Contains | Why excluded |
|---|---|---|
| `Practicum_CA1 submission.pdf` | Student name, student ID `24323870`, student email `X24323870@student.ncirl.ie`, Academic Integrity Certificate Verification Code | Academic Integrity Certificate code is the credential used to confirm a submission is the candidate's own work. Publishing it would be a genuine academic-integrity risk. |
| `Practicum CA2 Submission.docx` | Same identifiers | Same reason |
| `21 Sept-Practicum - Weekly Activity Report Template.docx` | Student name, student ID, course code | Personal information, not needed for reproducibility |
| `architecture diagram.drawio.pdf` | — | Superseded by the maintained architecture description; no academic identifiers, but kept local for consistency with the rest of the submission set |
| `From-Problem-to-Prototype.pptx` | — | Kept local; the content is captured in `DATA_DESIGN.md` and `PROJECT_SPECIFICATION.md` |

These exclusions are enforced by `.gitignore` and were applied **before the first
push**. The initial commit history was rewritten so that these files never appear in
any commit, rather than being added and later deleted — a deleted file is still
recoverable from git history, and a rewritten history is not.

## Why this matters for the research

Reproducibility normally means the corpus, query set, ground truth, and results are all
version-controlled. That principle still holds here, and `.gitignore` deliberately does
**not** exclude `data/` or `results/` — only caches, secrets, and these assessment
documents.

What is excluded is source material that is *evidence of assessment*, not *input to the
experiment*. Losing git history for those files costs nothing scientifically. Publishing
an academic integrity code would cost something real.

## If a supervisor needs the submitted documents

They are on the Desktop at `~/Desktop/RAG-Practicum/`. If they need to be shared, share
the files directly rather than adding them to this repository.

## Verification

To confirm nothing sensitive is tracked:

```bash
git ls-files | grep -Ei "\.docx|\.pptx|\.pdf|CA1|CA2"
```

Expected output: empty.
