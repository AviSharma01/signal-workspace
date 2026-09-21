# Expected Consensus: bounded candidate-method evidence

Research for [Define Expected and Excess Consensus baselines](https://github.com/AviSharma01/signal-workspace/issues/16),
2026-09-17. This note compares three method families; it selects no model,
lookback, reference length, adjustment set, threshold, or implementation.

## Result and boundary

**Each family can express part of the intended question, but none has demonstrated
support in Signal's data.** The existing
[Raw Consensus feasibility note](raw-consensus-window-feasibility-2026-09-17.md)
reports missing publication, identity, provenance, and correction evidence in the
inspected local representation. That finding is not reverified here. Even a
successful small supported-sample prerequisite would establish computability,
not necessarily enough history to estimate and validate a baseline.

The user's current agreement defines expected distinct Other Reporting Members
under comparable disclosure conditions, with security popularity, member activity,
direction, and observation opportunity/coverage accounted for where defensible.
Excess is observed Other Reporting Members minus Expected Consensus, on the
reporting-member count scale. Missing support makes both unavailable. This note
does not authorize silent fallback to a weaker baseline.

Reference/fitting evidence must precede the assessed lookback start; prespecified
target-window context may be eligible at the target contextual cutoff, excluding
assessed participation and market outcomes. The user also confirmed that
reference interpretations use only correction and identity evidence strictly
before the lookback start. An old publication corrected during the assessed
window therefore keeps its earlier supported interpretation for fitting, while
observed peer counting can use the correction when eligible at the target
contextual cutoff. Publication eligibility alone is insufficient: interpretation
evidence has its own cutoff.

## Three candidates, not a ranking

The applications and requirements below are research inferences for Signal,
grounded in the cited methodological facts; the sources do not validate these
methods for Congressional disclosures.

| Family | Alignment with the intended expectation | Required support and principal limitation |
|---|---|---|
| Historical comparable-window empirical mean | Average distinct peer counts in earlier comparable windows, matching or explicitly weighting approved security, direction, roster/activity, and coverage context. Whole windows retain the co-participation actually observed within them. | Needs supported counts including supported zeros, sufficient comparable windows, target-member exclusion, and a declared weighting/sampling unit. A security-only historical average does not automatically account for member propensity or changing coverage. Fine matching may leave no comparators; pooled matching needs an approved comparability rationale. Overlapping windows are not independent replicates. |
| Member-level binary participation model, aggregated | Estimate each eligible peer's probability of at least one qualifying disclosure in a window; sum probabilities. Potential covariates can represent historical security popularity, member propensity, direction, and eligible opportunity/coverage. | Needs an explicit historical member opportunity panel, credible observed absence as well as participation, repeat support, and a fitted mean structure. Unseen members/securities, sparse combinations, regularization or pooling, and changing rosters require decisions. Summing valid marginal probabilities does not assume peer independence; fitting and validating those probabilities still require defensible dependence handling. |
| Constrained historical resampling expectation | Generate eligible hypothetical windows from pre-window historical material under an explicit null, then average distinct peers. Historical member/security activity and coverage strata can be preserved by selected constraints. | Requires a justified exchangeability/resampling unit, sufficient historical blocks, explicit preserved and randomized features, and evidence that the resulting null answers the intended question. Constraints do not establish validity merely by being numerous. Using assessed-window member/security participation totals as fixed margins would let the cluster set its own baseline and violate the agreed boundary. |

For the first family, the mean is a proposed empirical estimate of ordinary
participation, not a guarantee that historical windows remain comparable.
Its weighting also matters: sampling every eligible Event overweights periods
with many disclosed occurrences relative to calendar-window sampling. Which
comparison population answers the intended question remains unresolved.

For the second family, let each peer indicator equal one if that member has any
qualifying participation. The count is the sum of those indicators, so its
conditional expectation is the sum of their conditional probabilities, without
requiring independence. This follows from linearity of expectation; it does not
justify an independent-Bernoulli count distribution, variance, or tail score.
[Stanford CS109A notes, sections IV–V](https://web.stanford.edu/class/cs109a/109asp22notes3.pdf)
provide the underlying indicator and linearity identities.

Dependence-aware estimation is not automatic: for example, statsmodels' GEE
documentation allows correlation within clusters but assumes observations are
uncorrelated across clusters. Choosing member clusters alone would therefore
need justification when members share disclosure periods or security conditions.
This is a limitation to evaluate, not a recommendation to use GEE.
[Official statsmodels GEE documentation](https://www.statsmodels.org/stable/gee.html).

For the third family, permutation validity depends on preserving the joint
distribution under the chosen null; restricted exchangeability can apply within
blocks or to whole blocks. That general result does not establish exchangeability
for these filings. Blindly shuffling individual rows could destroy filing batches,
temporal dependence, or coverage structure. The null's constraints would need a
separate substantive justification, even if only its mean is ultimately reported.
[Winkler et al., 2014, original research](https://pmc.ncbi.nlm.nih.gov/articles/PMC4010955/).

## Shared evidence requirements

These are consequences of the agreed estimand and temporal rules, not new
approved methodology:

- Declare the opportunity population independently of who happens to appear in
  the observed window. Retain historically supported identities, eligibility,
  chamber/source coverage and its time scope. Missing source coverage is not an
  observed zero. A supported zero means no qualifying disclosure within the
  explicitly supported observation scope, not no underlying trading activity.
- Exclude the target reporting member from both the observed peer count and the
  expected counted population for the entire assessed window. For historical
  comparators, do not subtract an arbitrary one from total counts: that member
  may not have participated. Whether that member's older history may help fit
  shared background parameters is a separate choice, not settled by excluding
  the member from the predicted count.
- Preserve publication uncertainty, correction and identity provenance, and
  reason-specific unavailability. An incomplete roster or unsupported history
  cannot silently become a reduced population with a fully supported total.
- Distinguish coverage/opportunity covariates from participation-derived proxies.
  Calling a target-window disclosure total an “opportunity” variable does not
  make it permissible context under the agreed prohibition.

## Historical schemes and permitted validation

An expanding reference uses all eligible earlier history; a rolling reference
uses a prespecified trailing portion. Both must finish before the assessed
window starts and obey the approved reference-vintage rule. Expanding history
may add support while mixing older conditions; rolling history may track changes
while discarding support. Neither is empirically preferred here. Rolling-origin
evaluation is a documented way to keep training observations earlier than each
validation observation; Signal additionally needs full reference-window
separation and evidence eligibility at every origin.
[Hyndman and Athanasopoulos, time-series cross-validation](https://otexts.com/fpp3/tscv.html).

Once a supported panel exists, an approved disclosure-only evaluation could audit
temporal leakage and correction replay; quantify supported versus unavailable
comparisons by chamber/time; check mean count calibration and, for binary models,
probability calibration on later disclosure windows; examine errors across
approved coverage/activity strata; and assess stability under prespecified
rolling/expanding schemes. Dependence from overlapping windows, shared filings,
members and securities must be addressed in the validation design. These checks
could expose an unusable expectation; they cannot establish predictive market
information, economic importance, or significance of a particular excess value.

None was run. Historical support, zero reliability, fit identifiability,
calibration, temporal stability, resampling validity, and sufficiency of any
adjustment remain unmeasured. No market outcomes may choose these settings.

For reproducibility, retain immutable evidence/input identifiers, eligibility and
method versions, deterministic ordering, fitting settings and software versions.
Any resampling adds an explicit algorithm, seed, stream/draw order and environment
record; a seed alone is insufficient. NumPy's own stream guarantee depends on
the same generator, seed, calls, arguments, build, environment and machine.
[Official NumPy compatibility policy](https://numpy.org/doc/stable/reference/random/compatibility.html).

## Scope and unresolved decisions

Read repository guidance, glossary and the prior feasibility note; verified the
five primary teaching/method/software sources linked above. No local database,
enriched dataset, project market results, model fitting, simulation, or source
acquisition was performed. Methodological pages include unrelated illustrative
datasets; these were not analyzed or used to compare Signal settings.

Still open: the comparison/opportunity population; calendar-window versus
Event-weighted reference sampling; supported
adjustments and any pooling; handling of unfamiliar members/securities; reference
scheme and length; validation/support criteria; and final family/model selection.
Exact Raw Consensus lookbacks also remain pending. This note supplies options
for those decisions, not evidence that any candidate is ready to compute.
