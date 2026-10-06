# Approved empty episode bootstrap treatment (#33)

Status: **Approved by Avi on 2026-10-06**, explicitly in the #33 implementation
conversation. This supplements the approved [#26](https://github.com/AviSharma01/signal-workspace/issues/26)
§7 procedure and [#33](https://github.com/AviSharma01/signal-workspace/issues/33)
acceptance contract solely for sampled weeks containing no episodes.

The previous implementation rule that any empty draw suppresses the entire
episode interval was not specified by #26 and is superseded by this approval.
It remains archived only to reproduce previously retained `cohort-analysis@1`
runs. New runs use `cohort-analysis@2` and the following procedure.

1. An empty sampled replicate has no defined episode estimator. Assign no zero
   or other synthetic value, and include no value for that draw in percentiles.
2. Record the empty/invalid draw explicitly. Continue the same deterministic
   PRNG stream until exactly **10,000 valid episode-estimate replicates** exist.
   Redraw only because the sampled weeks contain zero episodes; never condition
   validity on signs, sizes, zero-valued outcomes or any other outcome values.
3. Retain requested valid count, total attempts, valid count, empty count,
   deterministic seed and derivation inputs in run provenance. The implementation
   also records one-based empty-attempt indices and the attempt limit.
4. Reproduction must regenerate the same draw sequence, counts, estimates and
   empirical 2.5th/97.5th-percentile interval using retained method/version and
   inputs. The method version is part of seed derivation; v1 and v2 seeds can
   differ for the same cohort. Each version remains reproducible.
5. Use an explicit bounded execution safeguard. If it is exhausted before
   10,000 valid estimates, retain all attempt counts and mark the episode interval
   unavailable with a stable operational reason. Never invent an interval from
   an incomplete set of valid replicates.

The production safeguard is **50,000 total draw attempts per episode interval**,
recorded in the method contract. Exhaustion uses
`episode_bootstrap_draw_attempt_limit_reached`. A smaller retained limit can be
passed at the pure statistical seam for bounded-failure regression tests; HTTP
execution exposes no limit override. Reproduction uses the recorded limit.

This approval changes no weighting, cohort population, episode grouping,
calendar-week/block procedure, primary estimand, member-bootstrap procedure or
inferential threshold. Intervals still require at least **30 reporting members**;
episode intervals additionally require **30 episodes and 12 distinct anchor
months**. Supported point estimates remain visible when thresholds or execution
limits prevent an interval. No #32 market outcomes are recalculated or modified.
