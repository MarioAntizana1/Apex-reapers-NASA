# 05. Methodology

## Evidence-led approach

The planned method combines a lightweight development lifecycle, short task cycles, exploratory research and independent validation. It is adapted to a short event, not a claim of formal Scrum certification or a completed controlled study.

```text
Discover → define → prototype → test → review → publish
```

| Phase | Artifact | Acceptance condition |
|---|---|---|
| Research | Source catalog, literature records and questions | Primary source identified; limitations recorded |
| Definition | Requirement, owner and scope | Traceable to R1–R8 |
| Design | Data contracts and interface flow | Coordinates, assumptions and empty/error states explicit |
| Implementation | Small integrated changes | Connected behavior and failures considered |
| Validation | Software results plus separate data/science review | Evidence distinguishes executed checks from planned checks |
| Publication | README, procedures, bibliography, disclosure | Claims match the actual deliverable |

## Research procedure

1. Use OpenAlex/NTRS to discover candidate work [S81–S82].
2. Triangulate important claims against original mission/data publications.
3. Audit acquisition, metadata, units, CRS, coverage and rights.
4. Compare existing tools and identify a narrow useful workflow.
5. Seek subject-matter feedback where available; record whether it actually occurred.
6. Test comprehension with new users and record failures.

The review is exploratory, not a systematic review with independent double screening.

## Team execution

Use short standups: completed work, next deliverable and blocker. Each task has one accountable owner and a testable outcome. Escalate a blocker rather than spending the entire event silently stuck. Integrate small data samples early; polish only after the core flow works.

The planned design process separates discovery, definition, prototyping and validation. Historical pre-event activities are recorded as research/planning; implementation timing follows the team's event records and official guidance [S03].

## Quality gates

- **Data:** product identity, completeness, metadata and limitations are documented.
- **Design:** scope and coordinate contracts are agreed; unsupported states are visible.
- **Software:** applicable tests/build pass; stale/error responses do not silently become valid results.
- **Science:** claims, interpretations and assumptions are separately reviewed.
- **Release:** links, credits, AI disclosure, deployed version and unimplemented features are checked.

Performance/usability targets in [09](09_Plan_de_Validacion.md) are proposed criteria until measured.

## Ethics and AI

Cite external material, respect licenses, avoid false precision and do not imply NASA endorsement. Generative AI may assist research organization, development and writing; humans remain responsible for checking outputs. A model-generated statement is not evidence.

See the [detailed workflows and disclosure](25_Workflows_Tools_AI_and_Impact.md) and use the [templates](13_Checklist_y_Plantillas.md).
