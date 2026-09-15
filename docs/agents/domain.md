# Domain docs

## Layout and reading order

This is a single-context repository.

Before exploring, read root `AGENTS.md` and `CONTEXT.md`, then
relevant approved decisions in `docs/adr/` and applicable
directory-specific instructions.

If domain documents are absent, proceed without suggesting
placeholder documents. An absent document does not authorize
choosing unresolved methodology.

## Authority

Follow the precedence and documentation classes in root AGENTS.md.
CONTEXT.md defines shared language, not implementation or methodology.
Only explicitly approved current ADRs/specs establish decisions.

Implementation-status, measured-data, frontend-note, archive, and
historical V1 documents retain the authority classification defined
by root AGENTS.md. They cannot establish current requirements by themselves.

Keep `docs/adr/` reserved for durable approved decisions. Create its
first tracked file when there is a real decision, not a placeholder.
Record approval and explicit supersession where applicable.

## Vocabulary

Use terms as defined in CONTEXT.md in issues, proposals, hypotheses,
and tests. Reconsider invented synonyms; note real vocabulary gaps
for the domain-modeling skill.

## Conflicts

Surface conflicts with invariants or approved ADRs/specs explicitly.
Do not silently override them or infer supersession from recency.
