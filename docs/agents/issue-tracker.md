# Issue tracker: GitHub

Issues and proposed specs live in GitHub Issues for
`AviSharma01/signal-workspace`. Use the `gh` CLI from this clone.
Creating or opening an issue does not establish approval; follow AGENTS.md
for specification authority and recorded architectural decisions.
A Wayfinder decision becomes authoritative only after explicit resolution
under the project's approval and supersession rules.

## Conventions

- Create: `gh issue create --title "..." --body-file <file>`.
- Read: `gh issue view <number> --comments`; fetch labels as needed.
- List: `gh issue list --state open`, with appropriate filters.
- Comment: `gh issue comment <number> --body-file <file>`.
- Apply/remove labels: `gh issue edit <number> --add-label "..."`
  or `--remove-label "..."`.
- Close: `gh issue close <number>`.

Use a temporary UTF-8 file for multiline bodies, preserving literal
text and newlines. Infer the repository from the Git remote.

## Pull requests as a triage surface

**PRs as a request surface: no.**

## Skill operations

“Publish to the issue tracker” means create a GitHub issue.
“Fetch the relevant ticket” means read the issue and its comments.

## Wayfinding operations

- Map: one issue labelled `wayfinder:map`, containing Notes,
  Decisions-so-far, and Fog.
- Child tickets: GitHub sub-issues labelled `wayfinder:<type>`
  (`research`, `prototype`, `grilling`, or `task`). If sub-issues
  are unavailable, use a task list in the map and a `Part of #<map>`
  reference in each child.
- Blocking: use native GitHub issue dependencies where available;
  otherwise record `Blocked by: #<number>` references in the child.
  A ticket is unblocked when all blockers are closed.
- Frontier: select the first open, unassigned child in map order
  with no open blockers.
- Claim: assign the ticket to the driving developer.
- Resolve: comment with the result, close the ticket, and append
  a concise result and link to the map's Decisions-so-far.
