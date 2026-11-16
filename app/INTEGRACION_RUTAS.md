# Experimental terrain-planner integration

## Scope and origin

The local integration preserves the existing interface while incorporating Brandon's routing module from [PR #1](https://github.com/MarioAntizana1/Apex-reapers-NASA/pull/1), commit `14317771763ced63e8d927c35b84a9920e8c3269`.

The original integration scope corrected paths crossing blocked cells, rejected stale worker responses, labelled ascent as approximate and added straight-line distance beside the 3D direction arrow. That earlier task excluded publication/merge; the later owner-approved repository-publication task is separate.

## Decisions

- Keep A* edges instead of unchecked smoothing/simplification. Angular paths are preferable to cutting across blocked cells.
- Reject blocked endpoints rather than snap to another point and draw an invalid connector.
- Invalidate requests as soon as points/parameters change, including before the next 80 ms scheduling delay expires.
- Preserve the current base and stop ordering, including return to base.
- Display the terrain route separately from existing straight-line resource estimates.
- Keep 3D guidance as horizontal straight-line direction/distance to the next stop; it is not A* path length or vertical distance.

## Data and limits

Routing grids and their generators originate from the cited contribution. `public/terrain/terrain.json` documents color-to-index mapping and **assumed 2,000 m total relief**. Neither slope indices nor ascent metres are independently validated measurements.

They are labelled `SUPUESTO` (ASSUMPTION) in the interface. This grid is separate from the partial scientific HiRISE terrain used by the visual scene. An apparently plausible route does not establish safe real-world travel.

## Verification procedure

1. Unit cases for a narrow barrier and blocked endpoint.
2. Browser cases delaying a worker response while points are deleted or parameters change.
3. UI checks for return-to-base calculation, visible assumptions and distance beside the 3D arrow.
4. Run the complete unit suite, Playwright suite and TypeScript/Vite build.

Use [application procedures](README.md) and record actual results rather than treating this checklist as a passing execution.
