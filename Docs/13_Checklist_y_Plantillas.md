# 13. Checklists and reusable templates

Use these compact records alongside the [validation plan](09_Plan_de_Validacion.md). Unknown values stay explicitly unknown; never fill them with invented precision.

## Data card

1. **Name / product ID:** unique identifier and variable.
2. **Mission / instrument:** producer and acquisition mode.
3. **Resolution:** native spacing, derivative spacing and accuracy if independently known.
4. **Date:** observation/sol, release and access dates where available.
5. **CRS and units:** body model, latitude/longitude convention, projection, vertical reference.
6. **Coverage:** extent and no-data areas.
7. **Source:** original URL/DOI, source ID and local file.
8. **Usage terms:** required credit, license/terms and unresolved rights.
9. **Processing:** scripts, transformations, interpolation and checksum.
10. **Limitations / confidence:** artifacts, intended scale and unsupported interpretations.

## Science objective card

- Name, ID and coordinates/coverage.
- Scientific question and why the stop matters.
- Observation versus interpretation versus hypothesis.
- Original source `[Sxx]`, product and date.
- Confidence, uncertainty and sampling/planetary-protection limits.
- Expected dwell-time assumption.
- Reviewer and actual review status.

## Test record

- ID and linked requirement.
- Artifact/version, environment and input data.
- Preconditions and exact steps.
- Expected result and acceptance criterion.
- Actual result: pass, fail, blocked or not executed.
- Evidence path, reviewer and date.
- Remaining limitation; distinguish synthetic from real-data checks.

## ADR template

```text
ADR-xxx: title
Date / owner / status:
Context:
Alternatives and trade-offs:
Decision and reason:
Consequences and limits:
Evidence / affected requirements:
```

## Standup

```text
Date/time:
Completed:
Next deliverable:
Blocked by:
Help/decision needed:
```

## AI-use record

```text
Date and responsible person:
Tool/provider/model/version (if known):
Task and affected artifacts:
AI contribution:
Human verification actually performed:
Sources consulted independently:
Remaining uncertainty:
Public disclosure location:
```

Do not publish private prompts, credentials or conversation exports. Do not invent a model/version history when it is unknown.

## Data release checklist

- [ ] Product identity, original source and dates retained.
- [ ] Download is complete; `.part` files excluded.
- [ ] CRS/body model, units, vertical reference and no-data inspected.
- [ ] Layer extent comes from real georeferencing, not guessed screenshot coordinates.
- [ ] Derivative processing and original resolution documented.
- [ ] Required credit/rights reviewed.
- [ ] Scientific claims do not exceed evidence.
- [ ] Assumptions and partial coverage visible.
- [ ] Checksum/inventory scope explained.

## Software/demo checklist

- [ ] Applicable unit tests, browser tests and build executed with results recorded.
- [ ] Empty, error, stale-response and missing-data states checked.
- [ ] Base/stops and 2D/3D correspondence checked in supported coverage.
- [ ] Keyboard focus, contrast, labels, pointer-lock exit and fallback reviewed.
- [ ] No console/network failures hidden by a successful click.
- [ ] Planned features are not presented as delivered.
- [ ] Public demo checked separately from source push.

## Submission checklist

- [ ] Actual event rules, deadline and mandatory fields verified.
- [ ] Team/roles confirmed.
- [ ] Public English description, video/captions and links checked.
- [ ] Original sources, third-party credits and AI disclosure included.
- [ ] No secrets, private history or raw multi-gigabyte downloads staged.
- [ ] Human verifies actual submission confirmation.

## Reference template

`[Sxx] Author/organization. Title. Year if established. Original URL/DOI. Product/version. Access date if recorded. Role and limitations.`

## Retrospective

Record what shipped, what failed, what evidence is missing, what users misunderstood, what to remove and the next smallest useful improvement. Distinguish lessons learned from results not yet measured.
