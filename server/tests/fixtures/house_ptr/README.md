# Official House PTR sample for #27

Bounded measurement, inspected 2026-10-04. These are immutable public House Clerk
PDFs, retained solely as isolated test evidence. Tests inject them into temporary
databases, never the real application database. Download paths use
`https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{year}/{id}.pdf`.
The 2025/2026 locators came from the local V1 disclosure records; 2018/2021
locators came from the official annual indexes. The additionally inspected
2012 index contained no `FilingType=P` entries; no 2012 locator was inferred.

| PDF | Pages | Native text | Observed transaction rows | Result |
|---|---:|---|---:|---|
| 2018-20010021.pdf | 2 | Yes | 5 | Complete electronic table; owner codes, wrapped amounts, three equal Disney rows |
| 2018-9113416.pdf | 1 | No (0 characters) | Unresolved | Rotated scanned handwritten form; unsupported without OCR |
| 2021-20018021.pdf | 1 | Yes | 1 | Electronic table; spouse owner, wrapped amount |
| 2025-20030387.pdf | 41 | Yes | 296 starts | Partial: two asset/amount continuation fragments at pages 16/18 |
| 2025-20030699.pdf | 5 | Yes | 33 | Electronic table; repeated headers and supplementary text across pages |
| 2026-20034556.pdf | 2 | Yes | 5 | Electronic table; literal source row ID and `S (partial)` |

Transaction counts were cross-checked independently against native text lines
containing transaction and notification dates, and representative pages were
rendered for visual comparison. This is not a validation of every House filing
or chamber readiness. The two source dates are not public-availability times.

The electronic layouts share eight labeled, shaded header cells. Column widths
and positions vary. Transaction fields wrap, and supplementary text occupies
separate bands. Repeated headers can overlap body border segments on continuation
pages. Newer decorative small-cap labels sometimes decode to NUL characters;
transaction values in the inspected samples remain readable. Text-layer
checkbox glyphs are retained as literal text, not interpreted as booleans.

`house-ptr-native-table@1` uses the eight native header cells and source-drawn
side-border bands. Identity is artifact version plus ordered source position
(page/table/band and bounding box), never row-value equality. Native page text,
word positions, literal cells and unresolved fragments are retained. The
representation is committed before normalization. `house-ptr-fields@1` only
normalizes explicit calendar dates, known transaction direction codes and
well-formed closed amount ranges. It resolves no member, security, Event,
amendment, eligibility or correspondence.

Image-only, encrypted/unreadable and unrecognized layouts remain explicitly
unsupported/failed; mixed documents and unresolved continuations remain partial.
No OCR is introduced. A continuation fragment is not counted as another row;
the potentially incomplete previous occurrence is marked partial. Blank fields
remain blank. Source IDs and "Amended" text are retained without interpreting
relationships. Partial extraction does not establish complete filing coverage.

Reprocessing supports only the implemented method/version pair (1/1), resumes
materialization from a retained extraction after interruption, and is idempotent.
An older `none@1` result is preserved alongside the new native extraction.
Unknown versions are rejected, not accepted as caller-supplied labels.

SHA-256 of unmodified fixture bytes:

```text
2018-20010021.pdf f3a1c8471c966a464081f9a2af94dac3e2a51a4234ffc590bdba4b1579f8ece2
2018-9113416.pdf 4d0dd27bee198e990a38754ac8eed00410dd7678bdc1968f4a2f27b6c99986da
2021-20018021.pdf 071aab65d8223132ac372501605fadc98948e3c8f0faa006931ea3902c86d7c2
2025-20030387.pdf f96b24ba647c43bed680b256edc545059a62274d4785abe3ba36c94d653ce220
2025-20030699.pdf ac87f8583b66599886a5e6e8f7d8161f01f1d7b169013c906b17bec3f9a8ac00
2026-20034556.pdf f019e347ac3f85903d590ff6d742f79cecfb4a9ece6eaa78e7a62e4d76167790
```
