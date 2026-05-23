# Answer format contract (L5)

Agent answers use **GitHub-flavored Markdown** with fixed sections:

## Summary
Headline finding in 1–2 sentences.

## Key figures
Bullets with **bold labels** and formatted numbers (`$`, `%`).

## Notes
Optional context (period, filters).

## Caveats
Required when v1.2 disclaimers apply (run-rate, config target, pattern match, BI-only).

Charts are **not** embedded in markdown — `pipeline/chart_selector.py` builds `chart_spec` separately.

## UI rendering

- While streaming: plain text tokens (no partial markdown).
- After `done`: `AnswerMarkdown` renders full markdown via `react-markdown` + `remark-gfm`.
