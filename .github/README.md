# 🚀 Apex-Mars

### Explore Jezero Crater, one layer at a time.

**Apex-Mars** is a prototype by **Apex-Reapers** for the NASA Space Apps
Challenge. It brings together orbital imagery and topographic layers to make
Mars exploration easier to explore and understand.

## 🪐 Explore the demo

**[Open Apex-Mars](https://marioantizana1.github.io/Apex-reapers-NASA/)**

## 🗺️ What you can do

- Explore Jezero in an interactive 2D map.
- Switch between orbital imagery, elevation, shaded relief and slopes.
- Overlay a view of Perseverance's traverse and geological context.
- Adjust layer visibility and opacity, and inspect sources and limitations.

The 3D view, route planning, mission brief and other features are still in
development. This is a demonstration, **not a navigation or safety system**.

## 🛠️ Run locally

Requires Node.js and npm:

```bash
cd app
npm ci
npm run dev
```

Open the local address shown in the terminal. For tests, data attribution,
coordinates and instructions for adding layers, see [app/README.md](../app/README.md).

## 🛰️ Data and credits

The demo uses derived CTX imagery and topography distributed by NASA/USGS,
and contextual information from [Mars Trek](https://trek.nasa.gov/mars/).
Each layer has a source and limitations in the application. Scientific
alignment, provenance and licensing require further review.

Built with React, TypeScript, Vite and OpenLayers. Raw research data is not
included in this repository.
