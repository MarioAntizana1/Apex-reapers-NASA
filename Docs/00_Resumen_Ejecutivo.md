# 00. Executive summary

**Project:** Apex-Mars (formerly Ares Atlas). **Team:** Apex-Reapers.

## Problem

The Martian Map challenge asks for an integrated view of Mars data that can support thinking about a Marswalk [S01]. A useful exploration tool should connect a location or route with scientific interest, terrain, resource assumptions and return constraints—not simply display attractive imagery.

## Proposal

Use Jezero Crater as a focused case study. The concept asks:

1. **Can we go?** Inspect terrain, coverage, distance and explicit assumptions.
2. **What could we learn?** Connect geology, mineral detections and science stops to sources.
3. **How would we return?** Make the return path and resource margins understandable.

Jezero provides orbital and rover observations, a geological mapping literature and a documented delta/lake interpretation [S14–S17, S35–S39]. These are reasons for a research case study, not evidence of suitability for a crewed landing.

## Current delivery versus intended MVP

The repository contains a React/TypeScript map with provenance cards, a hypothetical base and stops, illustrative mission estimates, experimental terrain routing and partial HiRISE-based 3D exploration.

The full proposal additionally calls for validated science/return alternatives, dated conditions, broader EVA constraints and an exportable brief. Those are not all complete. See [scope](06_Propuesta_Solucion.md) and [traceability](17_Matriz_de_Trazabilidad.md).

## Intended audiences and benefits

Educators and public users could explore Mars science with clearer provenance. Researchers could use the prototype to discuss planning trade-offs. The team gains a reproducible data-to-map workflow.

These are **potential benefits**. No operational safety, mission-cost reduction or learning improvement has been measured. EVA-planning literature motivates the direction [S27–S33]; it does not validate our implementation.

## Team and execution

Mario Manuel Antizana Ponce de León leads integration and coordination, supported by Mauricio, Mauricio Sebastián Reátegui, Alessandro, Nicole and Valeria Rosado. Proposed specialist assignments and acceptance criteria are in [08](08_Equipo_y_Roles.md) and [20](20_Objetivos_y_Herramientas_Equipo.md); individual availability was not fully confirmed in the planning records.

The recorded event window is 2026-11-14–2026-11-15. Earlier work is documented as research, data-access checks and planning. Consult official guidance for authoritative requirements [S01–S03].

## Success criteria and risks

Success means an understandable, reproducible demonstration with honest sources and limits. Planned evaluation includes layer alignment, route behavior, user task completion and presentation clarity—not a claim that every target has been met.

Main risks: incompatible coordinate systems, insufficient terrain detail, assumed suit/routing parameters, scope growth, incomplete rights records and a deployment differing from local source. Prioritize a defensible core workflow over additional modes.

Generative AI assisted research organization, development and documentation. Human review remains necessary; see the [disclosure](25_Workflows_Tools_AI_and_Impact.md#generative-ai-disclosure).
