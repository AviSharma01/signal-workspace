# Bounded OpenFIGI META/METV identity-enrichment experiment

Observation date: **2026-10-09**. Execution of the [proposed tiny experiment](historical-security-identity-screen-2026-10-09.md#single-smallest-next-experiment). Research only: no integration, issue changes (including #31), Git operations, price requests or universe download.

**Result: distinct current composite and share-class FIGIs are useful enrichment candidates. The dated evidence keeps the 2021 ETF separate from later Meta Platforms Class A. Retain OpenFIGI as a conditional identity-enrichment research component; this does not approve integration or historical-identity readiness.** The company's candidate matches the evidenced issuer/class. The ETF candidate is consistent with the evidenced fund, but exact historical-to-current fund name/class continuity remains unresolved within this evidence set.

## Request and retained observation

One unauthenticated HTTP POST to `https://api.openfigi.com/v3/mapping`, with `Content-Type: application/json` and no API key:

```json
[
  {"idType":"TICKER","idValue":"META","exchCode":"US","includeUnlistedEquities":true},
  {"idType":"TICKER","idValue":"METV","exchCode":"US","includeUnlistedEquities":true}
]
```

The initial sandbox invocation failed DNS resolution before sending any HTTP request (curl exit 6, zero upload/download). The permitted network invocation sent the sole HTTP request: **200 OK**, no redirects or configured retries, 177 request-body bytes, 553 response-body bytes, 1.106949 seconds total transfer time. Both jobs returned one candidate, with no job errors/warnings.

- Local retrieval started **2026-10-09T06:24:22Z** and completed **2026-10-09T06:24:23Z** (11:54:22–11:54:23 IST), recorded at whole-second precision.
- Server `Date`: `Fri, 09 Oct 2026 06:24:22 GMT`; request ID: `a0580694-49fa-497f-9be9-e6fd675faabb`. These are observation/request metadata, not historical publication or identity-validity times.
- Retained exact [request body](artifacts/openfigi-meta-metv-2026-10-09/request.json), [raw response body](artifacts/openfigi-meta-metv-2026-10-09/response.json), [response headers](artifacts/openfigi-meta-metv-2026-10-09/response.headers), [start time](artifacts/openfigi-meta-metv-2026-10-09/retrieval-started-utc.txt), and [completion time](artifacts/openfigi-meta-metv-2026-10-09/retrieval-completed-utc.txt). The published packet includes a [sanitized transfer receipt](artifacts/openfigi-meta-metv-2026-10-09/transfer.sanitized.json) and an updated [SHA-256/byte manifest](artifacts/openfigi-meta-metv-2026-10-09/hashes.json).
- Response-body SHA-256: `4a526f649ec4f14dcd1049ed521f1262a302ebc0f3482a612a4e3fd0fa4bad68`.
- Header SHA-256: `4a16558149a2e442a0b8de6e6ab5f16c001f5d3fdca12ee719867aae0fbc59fa`.

Publication review, **2026-10-15**: the original `transfer.json` remains locally
held, unchanged and excluded from the proposed commit. It includes network
addresses/ports, a certificate chain and local runtime/path metadata unnecessary
for this result. The explicitly labeled allowlist derivative preserves only
the HTTP/request, size, timing and TLS-verification facts used here, records
every omitted field and the original receipt's digest/length, and is not claimed
to be original bytes. The manifest covers only published artifacts; its five
unchanged original files and one sanitized derivative can be verified without
the excluded receipt. No raw request, response or header was redacted.

The headers include `cache-control: private, no-cache, no-store, must-revalidate`. This is retained verbatim; HTTP caching policy is not a separate historical-data reuse license. The prior screen's OpenFIGI rights assessment remains the stated basis for the isolated research retention; this experiment does not expand that assessment to other sources.

## Every returned candidate

All values below are copied from the retained response, without normalization. Both candidates have `exchCode=US` and `marketSector=Equity`; each `figi` equals its `compositeFIGI`. These are not evidence of a specific primary exchange or listing interval.

| Request / returned ticker | Raw name | figi / compositeFIGI | shareClassFIGI | securityType | securityType2 | securityDescription |
|---|---|---|---|---|---|---|
| META / META | META PLATFORMS INC-CLASS A | BBG000MM2P62 | BBG001SQCQC5 | Common Stock | Common Stock | META |
| METV / METV | ROUNDHILL METAVERSE ETF-USDI | BBG011J1MN62 | BBG011J1MP12 | ETP | Mutual Fund | METV |

Distinctness is observed at both identifier levels. OpenFIGI describes FIGIs as permanent and nonrecycled, while descriptive metadata can change. This supports using them as stable labels after independent identity reconciliation; one observation does not empirically test their behavior through a rename. [OpenFIGI overview](https://www.openfigi.com/about/overview), [allocation rules](https://www.openfigi.com/about/allocation-rules).

## Reconciliation against the already-documented dated evidence

**ETF relationship, established independently of the API:** the issuer release dated **June 30, 2021** identifies **Roundhill Ball Metaverse ETF, NYSE:META**. The SEC supplement dated **January 14, 2022** explicitly changes that same fund's ticker **META → METV upon the open of trading January 31, 2022**. This supports the fund's rename relationship, rather than a ticker-only join. [Dated launch release](https://www.roundhillinvestments.com/assets/pdfs/meta_press_release.pdf), [SEC supplement](https://www.sec.gov/Archives/edgar/data/1683471/000089418922000256/meta497etickerchange.htm).

The METV candidate's Roundhill/metaverse ETF description and fund/ETP types are consistent with this relationship. **BBG011J1MN62 / BBG011J1MP12 are candidate enrichment for the evidenced ETF relationship**, not a fully verified historical class crosswalk. Its current name omits “Ball” and adds “-USDI”; the cited sources do not explain that current description or establish every intervening fund-name/class change. Exact SEC series/class IDs and historical-to-current class continuity remain unresolved. No additional lookup was made to close this gap.

**Company relationship, established independently of the API:** the SEC-filed issuer release dated **May 31, 2022** identifies **Meta Platforms, Inc. Class A common stock**, changing Nasdaq **FB → META prior to market open June 9, 2022**, with unchanged CUSIP. Nasdaq's **June 3, 2022** alert independently confirms the company/class and June 9 marketplace effective date. [SEC-filed release](https://www.sec.gov/Archives/edgar/data/1326801/000132680122000070/may312022-exhibit991.htm), [Nasdaq alert](https://www.nasdaqtrader.com/TraderNews.aspx?id=ECA2022-125).

The META candidate explicitly names the same company and Class A common stock. **BBG000MM2P62 / BBG001SQCQC5 are matching current enrichment for the separately evidenced company relationship.** They do not establish when these identifiers were assigned, their historical metadata vintage, or a complete 2021–2026 continuity chain.

**Historical separation:** a July 2021 META reference independently evidenced as the Roundhill ETF stays attached to the historical fund relationship. It cannot become Meta Platforms because today's META job returns that company. The company's later META assignment is supported by its own June 9, 2022 transition. The two relationships and distinct current ID pairs remain separate; the unresolved ETF class crosswalk does not justify merging them.

## Ambiguity, limits and recommendation

- No candidate multiplicity was observed: one candidate per job. No extra unmatched candidate was returned. This says nothing about exhaustive historical coverage.
- The META job did **not** return the old ETF under its former alias. This single response demonstrates no old-alias recovery for this query; it does not establish universal API behavior.
- ETF exact historical-to-current name/class continuity is unresolved. An unsupported historical reference or missing identity match must remain unresolved, even when a current ticker has one plausible candidate.
- Neither response supplies historical validity bounds, primary-listing chronology, historical public availability, or correction history. No intervals, exclusive gap between META occupants, or historical FIGI assignment dates were derived. `includeUnlistedEquities=true` is a request option, not proof of historical completeness or delisted coverage.

**Recommendation:** retain OpenFIGI as an optional, conditional identity-enrichment component for further research. This bounded run supplies distinct stable-ID candidates and supports separation of the evidenced ETF and company. It does not replace the dated SEC/exchange evidence, clear the ETF class-continuity gap, resolve unsupported identities, or certify #31. No implementation or issue-readiness state changes are warranted by this experiment.

Verification: parsed both jobs, counted every candidate, checked HTTP success/no redirects and response byte count, and hashed the retained files. No further mapping request was made.
