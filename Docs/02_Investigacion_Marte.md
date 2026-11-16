# 02. Mars and Jezero research

**Purpose:** scientific context for a public exploration prototype. Sources are listed in [11 — Bibliography](11_Bibliografia.md). Confidence below concerns the broad interpretation, not the accuracy of a particular map pixel.

## Environment and implications

| Topic | Evidence-backed context | Mapping implication |
|---|---|---|
| Atmosphere and temperature | Mars has a thin atmosphere and a harsh, variable thermal environment [S06, S40–S41] | Show observation date, units, location and sensor; do not imply Earth-like exposure conditions |
| Dust | Dust affects atmospheric and surface conditions [S06, S40, S44] | Separate archived measurements and climatology from a forecast |
| Radiation | Curiosity RAD measured surface radiation; exposure varies with environment and solar activity [S42–S43] | A constant research assumption is not a personalized dose prediction |
| Regolith/perchlorates | Perchlorates have important chemical/biological implications [S46] | Do not present local soil as automatically safe or usable |
| Water and minerals | Hydrated mineral detections and subsurface-ice research are different evidence types [S22, S39, S47] | Mineral signatures do not establish accessible water or resource reserves |
| Terrain | Image scale and DTM resolution constrain slope/obstacle interpretation [S34, S49] | Regional MOLA relief cannot resolve human-scale hazards |
| Communication | Mars relay operations depend on network geometry and scheduling [S09] | A real communication window needs ephemerides and mission constraints |

## Why Jezero

Jezero has a well-studied field site, orbital maps and Perseverance observations [S35–S39, S60]. Published work supports an ancient delta/lake interpretation and flood deposits [S37], aqueous alteration in sampled igneous rocks [S38] and regional olivine/carbonate investigations [S39].

**Confidence: high** for these broad published geological interpretations; **not established** for any unsourced POI, precise mineral abundance or resource-access claim in our prototype.

NASA human-exploration studies also used Jezero as an example in exploration-zone discussions [S17, S21]. That precedent motivates a case study; it does not certify a crewed landing site.

## Human exploration context

- DRA 5.0 describes a mission architecture, not a validated four-hour walk or a model of our prototype [S18].
- Exploration zones organize regions of interest around a notional base; regional campaign scale and individual EVA scale must remain distinct [S17, S21].
- Surface science includes planning, sampling, documentation, contamination control and return logistics [S19–S20, S54].
- BASALT-related research emphasizes science-driven, geospatial and temporal EVA planning [S27–S29, S33].
- Resource support tools such as PersEIDS motivate explicit consumable and timing trade-offs [S32].

## Scientific opportunities and resource limits

Potential educational themes include delta deposits, alteration history, carbonate-bearing units, geological context and the difference between observation and interpretation [S35–S39]. Any specific science stop needs a location, source, uncertainty statement and scientific question.

MOXIE demonstrates an oxygen-ISRU technology context [S45], not an available oxygen service at the hypothetical base. Regional ice or mineral evidence must not be converted into guaranteed accessible resources [S22, S47]. Planetary-protection constraints require expert consideration [S54].

## Planning assumptions

The initial proposal considered a short illustrative EVA with configurable resource rates. These parameters are **ASSUMPTIONS**, not suit qualification data. Current straight-line estimates and movement-meter defaults are documented separately in [app/README.md](../app/README.md).

Do not equate:

```text
observation ≠ interpretation ≠ planning assumption ≠ validated operational decision
```

## Questions requiring review

1. Are the selected products correctly aligned and suitable for the intended scale?
2. Which mineral claims are supported locally, and at what confidence?
3. Which environmental readings are quality-controlled and temporally relevant?
4. What suit, return, radiation and communications models could be defended?
5. What contamination and sampling restrictions would apply?

No external expert sign-off is claimed in this edition.
