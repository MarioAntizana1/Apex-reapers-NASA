# 14. Glossary

| Term | Meaning in this project |
|---|---|
| ADR | Architecture Decision Record: context, alternatives, decision and consequences |
| A* | Graph-search method used by the experimental routing planner; correctness depends on the input/cost model |
| ASSUMPTION / SUPUESTO | Unvalidated project value or model; Spanish UI/source records may use `SUPUESTO` |
| Basemap | Reference imagery or map underneath other information |
| Climatology | Statistical/model context over time, not live weather |
| CRISM | MRO imaging spectrometer; used for mineralogical research [S47, S61] |
| CRS | Coordinate reference system, including the relevant planetary body/model conventions |
| CTX | MRO Context Camera; regional imagery and stereo products [S61] |
| DEM / DTM | Digital elevation/terrain model; inspect actual product definitions and metadata |
| Derivative | Output transformed from an original dataset; preserve the processing history |
| Detection | Signal supported by an observation, distinct from a broader interpretation |
| DOI | Persistent identifier resolving to a publication or dataset record |
| EVA | Extravehicular activity; a crew activity outside a spacecraft/habitat |
| EZ | Exploration zone containing regions of interest around a notional site [S17] |
| GeoJSON | JSON format for geographic features; planetary coordinate conventions still need documentation |
| Georeferencing | Mapping image/data coordinates to a defined spatial reference |
| GCR / SEP | Galactic cosmic rays / solar energetic particles; radiation context [S43] |
| GIS | Geographic information system |
| Hillshade | Synthetic illumination derived from elevation, not a photograph |
| HiRISE | MRO high-resolution camera and associated stereo terrain products [S49, S61] |
| HRSC | Mars Express High Resolution Stereo Camera [S66] |
| ISRU | In-situ resource utilization; not an available resource merely because a mineral is detected |
| Jezero | Mars crater and Perseverance field-site case study [S35–S39] |
| MEDA | Mars Environmental Dynamics Analyzer on Perseverance [S40] |
| Mission brief | Proposed portable plan with route, assumptions, sources and limits; export remains pending |
| MOLA | Mars Orbiter Laser Altimeter; regional/global topographic context [S71] |
| MRO | Mars Reconnaissance Orbiter [S61] |
| MVP | Minimum viable product; proposal scope is distinct from actual delivery |
| No-data | Missing or invalid measurements; never silently treat as valid terrain |
| NTRS | NASA Technical Reports Server [S81] |
| Orthomosaic | Geometrically corrected image mosaic; quality depends on its source/model |
| PDS | NASA Planetary Data System [S58] |
| POI / ROI | Point of interest / region of interest |
| proj4 | Projection-transformation library used with explicit Mars definitions |
| PWA | Progressive web application; planned offline support is not implemented merely by using static assets |
| Quantization | Discrete numeric storage; 0.1 m encoding does not imply 0.1 m measurement accuracy |
| RAD / REMS | Curiosity radiation/environment instruments [S41–S42] |
| Raster | Grid of pixels/cells with spatial metadata |
| Resolution | Sampling spacing, not automatically accuracy |
| SHA-256 | Content digest useful for byte comparison; not independent proof of authenticity |
| Sol | Martian solar day; always retain the mission/date context |
| THEMIS | Mars Odyssey thermal-imaging instrument [S62] |
| TRN | Terrain Relative Navigation; named products differ from regional science mosaics |
| Turn-around | Planned point/time to begin return under a specified model |
| Walkback | Return traverse; minimum-time return need not maximize science value [S72] |
| WebGL | Browser graphics capability needed for the 3D demonstration |

## Language to avoid

Avoid “safe route,” “NASA-certified,” “live weather,” “available water,” “exact simulation” or “AI-validated science” unless the specific claim has appropriate independent evidence. Prefer “experimental route,” “archived observation,” “mineral detection,” “illustrative model” and “requires review.”
