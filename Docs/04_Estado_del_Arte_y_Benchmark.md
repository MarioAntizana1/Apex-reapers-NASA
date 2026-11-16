# 04. Related work and benchmark

## Existing tools

| Tool / work | Strength | Implication for Apex-Mars |
|---|---|---|
| Mars Trek [S14] | Multi-mission imagery, terrain and scientific context | Reuse original data services; do not pretend layered Mars maps are new |
| JMARS [S56] | Planetary GIS analysis | Benchmark scientific workflows rather than recreate a professional GIS |
| MMGIS [S13, S52] | Mission-oriented mapping | Study provenance and operational context; no backend integration is claimed |
| OpenPlanetaryMap [S55] | Planetary basemap work | Reference for map design and alternative data presentation |
| Virtual hiking map of Jezero [S31] | Public terrain/imagery exploration | Attractive 3D alone is not differentiation |
| PersEIDS [S32] | Decision support under communication latency | Resource/time alternatives motivate the concept, not a claim of equivalent capability |

## Literature lessons

- Science objectives should drive EVA planning and station selection [S27–S29].
- Latency changes collaboration and operational planning [S33].
- Consumables and timing belong in a clearly defined model [S32].
- Regional and local terrain serve different purposes [S30, S34, S49].
- A planetary map needs legend, scale, projection, provenance and uncertainty [S50–S51].
- Minimum-time walkback and geologically useful traverses need not be identical [S72].

## Positioning

The proposed distinction is a clear **data → route → assumptions → return → brief** workflow for a focused public case study. Apex-Mars is not a replacement for Mars Trek, a certified operations system or a full Mars digital twin.

The present prototype only implements part of that workflow. An exportable brief and validated science/return comparison remain planned.

## Competitive records

The original dossier recorded five other-team repositories. They are listed as benchmark C01–C05 in [11 — Bibliography](11_Bibliografia.md), not scientific evidence. Their current availability, affiliation and feature claims have not been independently audited here. No code reuse is claimed from these benchmark entries.

## Build versus reuse

Reuse established libraries and original archives; build the focused interaction, explicit metadata contracts and understandable explanations. Avoid a new GIS engine, unsupported “real-time” promises, unvalidated science scores and visual complexity that hides missing evidence.

Potential impact must be evaluated through user and scientific review rather than inferred from competing projects or prior award winners [S05].
