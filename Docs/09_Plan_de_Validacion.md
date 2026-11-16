# 09. Validation plan

**Important:** this is a test plan. A listed test or target is not a passing result. Software tests with synthetic fixtures do not validate actual Mars data, scientific claims or operational suitability.

## Strategy and responsibilities

| Area | Review | Proposed responsibility | Evidence |
|---|---|---|---|
| Data | CRS, units, date, coverage, completeness and alignment | Mario, Mauricio, Mauricio Sebastián | Metadata, comparison results and screenshots |
| Science | Claims, interpretations and uncertainty | Alessandro with Valeria | Cited cards and review notes |
| Usability | Understanding and task completion | Nicole with Valeria | New-user observations |
| Software | Algorithms, errors, responsiveness and compatibility | Developers and QA | Automated results/build/logs |
| Presentation | Clarity, timing and honest scope | Team | Rehearsal/recording and checklist |

## Data checks — proposed tolerances

These initial tolerances are educational screening criteria, not sufficient navigation accuracy. Justify them against each actual product.

| ID | Check | Proposed method / criterion |
|---|---|---|
| D01 | Jezero coordinates | Compare original sources; initial tolerance <0.01° |
| D02 | Elevation | Compare three reference points; initial tolerance <50 m |
| D03 | Traverse | Compare overlay against original geometry |
| D04 | Minerals | Confirm spatial/contextual agreement with source |
| D05 | CRS | Round-trip transformation; initial numerical error <1 m |
| D06 | Dates | Observation and access metadata coherent |
| D07 | Units | No undocumented unit mixing |
| D08 | Missing values | No unhandled critical null/no-data |

## Scientific review — not completed by this plan

| ID | Claim to review | Source |
|---|---|---|
| C01 | Ancient Jezero delta/lake interpretation | [S37] |
| C02 | Regional carbonate interpretation | [S39] |
| C03 | Hydrated-mineral evidence and limits | [S47] |
| C04 | Ice as a potential resource, not a local reserve claim | [S22] |
| C05 | Perchlorate implications | [S46] |
| C06 | Radiation risk and model limits | [S42–S43] |
| C07 | Communication delay/context | [S09] |
| C08 | Exploration-zone concept and scale | [S17] |
| C09 | Appropriate terrain-dependent speed modeling | [S72] |

The current constant-speed resource estimate is not an implemented calibration of [S72].

## Usability tasks — proposed targets

Plan for five new users where feasible; do not claim the study happened without records.

| ID | Task | Target |
|---|---|---|
| U01 | Open map and identify relevant layer/control | <30 s |
| U02 | Create a route/stops toward a target | <2 min |
| U03 | Locate return/turn-around information | <1 min; planned functionality |
| U04 | Add a science stop | <1 min |
| U05 | Inspect dated conditions | <30 s; planned functionality |
| U06 | Export a brief | <1 min; planned functionality |
| U07 | Explain the displayed risk/assumptions | <1 min |
| U08 | Compare return/science alternatives | <1 min; planned functionality |

Record success/failure, elapsed time, errors and misunderstandings. Do not test a missing feature as though it exists.

## Technical checks — targets, not benchmarks achieved

| ID | Check | Original target |
|---|---|---|
| T01 | Initial load | <3 s on a defined 4G profile |
| T02 | Interaction | 60 FPS target; 3D has separate provisional target |
| T03 | Layers | 8–10 without errors |
| T04 | Route response | <1 s on a defined device |
| T05 | Offline | Map/brief workflow; not implemented |
| T06 | Cross-browser | Chrome, Edge and Firefox |
| T07 | Mobile | Usable responsive layout |
| T08 | Accessibility | Lighthouse/axe review; original score target ≥90 |
| T09 | Console | No unexplained application errors |
| T10 | Deployment | Public URL returns successfully and matches intended version |

Unit tests currently address layer contracts, mission/simulation helpers, terrain coverage and experimental routing. Browser tests exercise interaction, error paths and stale worker responses. Run the suites before recording actual results.

## Presentation checks

| ID | Check | Criterion |
|---|---|---|
| P01 | Pitch | Clear narrative within three minutes |
| P02 | Demo | Core flow without blocking errors |
| P03 | Video | 60–90 s planning target; confirm official requirements |
| P04 | Q&A | Explain assumptions, sources and missing features |
| P05 | Submission | Mandatory fields, English, links, citations and AI disclosure |

## Release procedure

From `app/`: `npm test`, `npm run build`, then `npm run test:e2e` with the required browser installed. Use [application instructions](../app/README.md).

Store command/version, date, result, failures and relevant artifacts. Record data restoration omissions separately from corruption. Confirm the public deployment independently of the source push.

Triage blocking failures first, core-task defects next, secondary issues if time permits, cosmetics last. An unresolved scientific/rights concern must remain visible even if software checks pass.
