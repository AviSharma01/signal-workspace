# Independent event references for the bounded Stooq screen

Checked on 2026-10-07. This note verifies sample event facts against issuers and exchanges; it does not establish any Stooq data property or production readiness. No Stooq prices are used as ground truth here. Sources are currently accessible references, not historical point-in-time snapshots.

## Corporate actions and identities

| Case | Independently established fact | Primary reference |
| --- | --- | --- |
| AAPL cash dividend | Declared 2024-05-02; $0.25 per share; record date 2024-05-13; payable 2024-05-16. Apple's table says its dividend amounts are not split adjusted. | [Apple dividend history](https://investor.apple.com/dividend-history/default.aspx) |
| AAPL split | Four-for-one split; record date 2020-08-24; first split-adjusted trading date 2020-08-31. The legal/effective split date is distinct: Apple's FAQ says 2020-08-28. | [Apple dividend history and footnote](https://investor.apple.com/dividend-history/default.aspx), [Apple split FAQ](https://investor.apple.com/investor-relations/faq/default.aspx), [Apple original announcement](https://www.apple.com/newsroom/2020/07/apple-reports-third-quarter-results/) |
| NVDA split | Ten-for-one split; holders of record at close 2024-06-06 receive nine additional shares after close 2024-06-07; first split-adjusted trading expected at open 2024-06-10. | [NVIDIA official split FAQ, pages 1–2](https://investor.nvidia.com/files/doc_downloads/2024/06/nvidia-2024-stock-split_faq_investors.pdf) |
| NVDA cash dividend | The same FAQ explicitly identifies 2024-06-11 as the ex-dividend date, $0.01 per share on the post-split basis, and payment on 2024-06-28. | [NVIDIA official split FAQ, page 2](https://investor.nvidia.com/files/doc_downloads/2024/06/nvidia-2024-stock-split_faq_investors.pdf) |
| FB → META | Meta Platforms Class A changed ticker effective before market open 2022-06-09. Company name rebranding was announced 2021-10-28. CUSIP remained unchanged; this is continuity of one security. | [Meta issuer announcement](https://investor.atmeta.com/investor-news/press-release-details/2022/Meta-Platforms-Inc.-to-Change-Ticker-Symbol-to-META-on-June-9/default.aspx), [Nasdaq ECA2022-125](https://www.nasdaqtrader.com/TraderNews.aspx?id=ECA2022-125) |
| Reused FB: ProShares ETF | ProShares' current issuer page identifies FB as its S&P 500 Dynamic Buffer ETF, CUSIP 74349Y613, inception 2025-06-24. Its page warns that listing date is typically one or more days after inception, so inception must not silently become the first exchange trading date. Cboe lists FB as this ETF. Combined with the prior Facebook FB identity above, this establishes concrete reuse of FB by a different security. | [ProShares official FB fund page](https://www.proshares.com/our-etfs/strategic/fb), [Cboe FB listing](https://www.cboe.com/us/equities/listings/listed_products/symbols/FB) |
| Roundhill META → METV; reused META symbol | Roundhill's Metaverse ETF launched 2021-06-30, and its symbol changed from META to METV at trading open 2022-01-31. Combined with Meta Platforms' June change, this establishes two distinct U.S. securities that used META during the sample period. Current issuer page identifies the ETF as NYSE Arca, CUSIP 53656F417, ISIN US53656F4173. These are current identifiers, not proof of their historical validity intervals. | [Roundhill fund page](https://www.roundhillinvestments.com/etf/metv/), [OCC symbol-change memo 49960](https://infomemo.theocc.com/infomemos?number=49960) |
| TWTR terminal event | NYSE's Form 25 states merger effective 2022-10-27, shares exchanged for $54.20 cash subject to withholding, trading suspended before market open 2022-10-28, and removal from listing at opening of business 2022-11-08. Thus 2022-10-27 is the last possible ordinary exchange trading date, an inference from the suspension rather than independently checked OHLCV. | [NYSE-signed Form 25, issuer filing copy, pages 1–2](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001418091/8f906d28-b15e-432d-b2ee-4744709b40cf.pdf) |

Apple's issuer history does not provide the AAPL dividend ex-date. [Nasdaq's AAPL dividend-history page](https://www.nasdaq.com/market-activity/stocks/aapl/dividend-history?_wrapper_format=html) returned unavailable data in this check. Accordingly, the May AAPL ex-date is not marked primary-source verified here. NVIDIA's explicitly documented ex-date offers a primary-verified dividend sample without inferring ex-date from settlement rules.

The reuse case tests whether a current `META` price lookup can safely identify the issuer on an earlier date. A pre-2022-06-09 Meta Platforms history under today's ticker may be legitimate backfilled FB continuity, but cannot by itself establish a historical ticker-to-security mapping. Nor does a successful METV history prove that the provider exposes the former META ETF identity safely.

The additional FB reuse case is particularly useful for testing a historical disclosure carrying the old Facebook ticker. A current bare-FB lookup can legitimately identify ProShares' ETF instead. The issuer and exchange references verify that distinct identity; the main screening artifacts must separately establish which identity Stooq returns. Neither the ETF's inception date nor the old ticker string alone supplies a safe historical security resolver.

## Exchange calendar reference

Dates below are full-day NYSE Group cash-equity closures, with all early closes at 13:00 Eastern Time. Regular core hours are 09:30–16:00 Eastern Time according to [NYSE trading hours](https://www.nyse.com/trade/hours-calendars). These exchange hours establish the reference session, not what a Stooq daily bar includes.

| Year | Full-day closures | Early closes |
| --- | --- | --- |
| 2021 | 01-01, 01-18, 02-15, 04-02, 05-31, 07-05, 09-06, 11-25, 12-24 | 11-26 |

2021 dates: [ICE/NYSE December 2020 calendar announcement](https://ir.theice.com/press/news-details/2020/NYSE-Group-Announces-2021-2022-and-2023-Holiday-and-Early-Closings-Calendar/default.aspx).

| Year | Full-day closures | Early closes |
| --- | --- | --- |
| 2022 | 01-17, 02-21, 04-15, 05-30, 06-20, 07-04, 09-05, 11-24, 12-26 | 11-25 |
| 2023 | 01-02, 01-16, 02-20, 04-07, 05-29, 06-19, 07-04, 09-04, 11-23, 12-25 | 07-03, 11-24 |

2022–2023 dates: [ICE/NYSE December 2021 calendar announcement](https://ir.theice.com/press/news-details/2021/NYSE-Group-Announces-2022-2023-and-2024-Holiday-and-Early-Closings-Calendar/default.aspx). This later announcement includes Juneteenth, which was absent from the original December 2020 announcement. No New Year's holiday was observed for Saturday 2022-01-01: 2021-12-31 was not an exchange holiday.

| Year | Full-day closures | Early closes |
| --- | --- | --- |
| 2024 | 01-01, 01-15, 02-19, 03-29, 05-27, 06-19, 07-04, 09-02, 11-28, 12-25 | 07-03, 11-29, 12-24 |
| 2025 | 01-01, **01-09**, 01-20, 02-17, 04-18, 05-26, 06-19, 07-04, 09-01, 11-27, 12-25 | 07-03, 11-28, 12-24 |
| 2026 | 01-01, 01-19, 02-16, 04-03, 05-25, 06-19, 07-03, 09-07, 11-26, 12-25 | 11-27, 12-24 |

2024–2026 scheduled dates: [ICE/NYSE November 2023 calendar announcement](https://ir.theice.com/press/news-details/2023/NYSE-Group-Announces-2024-2025-and-2026-Holiday-and-Early-Closings-Calendar/default.aspx). Special 2025-01-09 closure: [NYSE/ICE Carter mourning announcement](https://ir.theice.com/press/news-details/2024/The-New-York-Stock-Exchange-Will-Close-Markets-on-January-9-to-Honor-the-Passing-of-Former-President-Jimmy-Carter-on-National-Day-of-Mourning/default.aspx), corroborated by [Nasdaq's closure announcement](https://www.nasdaq.com/press-release/nasdaq-announces-closure-its-us-markets-honor-national-day-mourning-former-president). Future November/December 2026 dates are schedule references only and must not be treated as completed sessions in the October experiment.

Calendar-aligned dates and an absence of holiday rows cannot establish regular-session OHLCV semantics. Early-close daily rows can establish date presence, but their inclusion of pre-market/after-hours trades requires independent field semantics or suitable intraday/trade evidence. This note does not claim a comprehensive audit of all Nasdaq historical schedules or unscheduled interruptions.
