# Wording rules

Local snapshot from `agentic-research/skills/paper/polish/SKILL.md`: the shared
information-preserving invariant and the complete Wording section.
Source repository: https://ipads.sjtu.edu.cn:1312/scaleaisys/agentic-research.git
Repository HEAD at import: `44fcc885a65ce691a9bdde4efaf47e3063c13622`.
The interactive confirmation loop in `../SKILL.md` governs applying these rules.

A final pass fixes what is wrong without changing what the paper says. One
invariant holds across all three subquestions: information content stays the
same. No fact, number, claim, citation, term, paragraph, or point is added or
removed. Cut filler, not facts.

## Wording

Authority: Kaashoek's sentence-level style, restricted by an
information-preserving invariant.

### Invariant across polish

- Every fact, number, unit, date, name, and identifier — character for character.
- Every claim, including hedges ("may", "can", "up to" — keep them).
- Every citation, reference, footnote anchor, and figure / table / equation /
  section cross-reference.
- Every defined term and its first-use definition; no silent renames.
- Paragraph count and boundaries, paragraph order, and section order — unless
  the user approves removing a fully redundant paragraph.
- The technical point of each paragraph; do not switch which idea it carries.
- LaTeX commands, math, code spans, URLs, Markdown links, and labels — never
  broken to satisfy line length.

### Allowed

- Typo, spelling, capitalization, tense, agreement, and punctuation fixes;
  consistent capitalization of system, product, and paper names.
- Word choice: replace a vague or imprecise word with a more accurate one, when
  technical meaning is unchanged.
- Sentence-internal rewriting: clause order, voice, phrasing, simplification.
- Merging two adjacent sentences, or splitting one, when clearer and meaning is
  preserved.
- Sentence-order changes within a paragraph, only to move the paragraph's
  existing point to the first sentence. The point itself does not change.
- Removing softeners and content-free filler: "we believe", "it is important to
  note that", "in some sense", "to the best of our knowledge", "needless to say".
- Replacing an adjective-only description with a noun- or data-driven one, only
  when the noun or datum is already present in the paragraph.
- Proposing removal of a redundant restatement — a point, fact, or explanation
  already stated elsewhere in the range. Removing a true redundancy preserves
  information content (the point still stands elsewhere), but it deletes text:
  never remove it silently; delete only after the user approves.

### Style Rules (Kaashoek subset, sentence level)

- Short, simple, accurate sentences — one idea each; collapse three-deep nested
  clauses. When a sentence can be simplified without losing meaning or
  precision, simplify it.
- No softeners (list above) unless they carry real epistemic weight.
- Data and nouns beat adjectives; never invent numbers — surface only ones
  already in the text or an adjacent sentence.
- Match noun and verb strength to what they name:
  - "idea" / "intuition" for an adopted technique → "technique" / "design" /
    "method" / "family".
  - "approach" for a single algorithm → "algorithm" / "method".
  - "look at" / "consider" for actual measurement → "measure" / "evaluate".
  - "framework" for a small tool → "library" / "tool".
  - "solve" / "eliminate" for a partial improvement → "reduce" / "mitigate" /
    "address case X".
  - "optimal" / "always" without proof → state the bound the text already gives.
- Avoid clumsy repetition of an ordinary word within a sentence or across
  adjacent sentences; replace one occurrence with a near-synonym. Exception:
  technical and defined terms repeat verbatim — synonyms for them create
  ambiguity about whether the same thing is meant.
- For captions with multiple subfigures or subtables, preserve existing panel
  labels exactly. Normalize only local punctuation and spacing, e.g.,
  `(a) ... . (b) ... .` or `(Left) ... . (Right) ... .`. Do not invent,
  reorder, or rename panel labels, because they may be referenced by the
  figure, text, or LaTeX labels.

This subquestion does **not** enforce the "shorter overall" rule of
`kaashoek-style-writing`: final polish cannot drop content.

