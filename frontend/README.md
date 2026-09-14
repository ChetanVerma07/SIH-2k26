# Phase 9 — Passive Shelter Design Platform (Frontend)

**AI-Based Software Model for Designing Energy-Efficient Passive Shelters for Different Climatic Conditions**
SIH 2026 Prototype — Phase 9: Frontend / UI only.

This phase delivers a **standalone, runnable React + TypeScript frontend** for a passive-shelter
thermal design and optimization dashboard. It uses deterministic local mock data and does **not**
include a backend, database, real weather APIs, ANSYS integration, or the actual AI optimizer —
those are out of scope for this phase and will be provided by a separate FastAPI service.

---

## 1. Project Purpose

The application lets an engineer or evaluator:

1. Select a location/climate (presets or custom).
2. Enter shelter requirements (comfort range, occupants, floor area, budget).
3. Configure design parameters and materials (or let the optimizer auto-select them).
4. Run a (simulated) thermal analysis.
5. View thermal performance results and charts.
6. Compare baseline, candidate, and recommended designs.
7. Inspect optimization convergence and sensitivity analysis.
8. Read a plain-language explanation of the recommended design.
9. Export/print a structured engineering report.

All data in this phase is deterministic, mock, and clearly labelled as **DEMO SIMULATION** /
**Demo Mode — Mock Data** in the UI.

---

## 2. Frontend Architecture

```
phase9_frontend/
├── src/
│   ├── api/          # Mock API layer (FastAPI-ready function signatures)
│   ├── components/   # Reusable UI primitives (Card, Badge, Tabs, StatCard, etc.)
│   ├── hooks/         # React context for current analysis state (+ localStorage)
│   ├── layouts/       # Sidebar + top navigation shell
│   ├── mock/          # Deterministic mock datasets (climate, materials, designs, optimization)
│   ├── pages/         # One file per route/page
│   ├── types/         # Centralized TypeScript interfaces (shared contract with backend)
│   ├── App.tsx        # Route definitions
│   ├── main.tsx       # Entry point
│   └── index.css      # Tailwind entry
├── tests/             # Vitest + Testing Library tests
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

State management uses React Context (`useAnalysisContext`) rather than Redux, since a single
current-analysis draft is sufficient for this phase. The draft is persisted to `localStorage` so
refreshing the browser does not immediately lose in-progress form data.

---

## 3. Page Structure

| Route              | Page              | Purpose                                              |
|---------------------|-------------------|-------------------------------------------------------|
| `/`                 | Dashboard         | KPIs, recent analyses, climate summary, latest design |
| `/new-analysis`     | New Analysis      | Multi-section form (location, climate, requirements, design, materials) |
| `/simulation`       | Simulation        | Simulated progress through 6 analysis stages          |
| `/results`          | Results           | Thermal performance charts and summary stats          |
| `/designs`          | Design Comparison | Baseline vs candidates vs recommended, with chart      |
| `/optimization`     | Optimization      | Convergence chart, top 5 designs, sensitivity analysis |
| `/recommendation`   | Recommendation    | Final recommended design + "why this design?" + trade-offs |
| `/materials`        | Materials         | Searchable/filterable material library                |
| `/climate`          | Climate           | Current conditions + 24-hour climate profiles          |
| `/report`           | Report            | Structured report with JSON/CSV export and print       |

Navigation flow: `Dashboard → New Analysis → Simulation → Results → Optimization → Compare → Recommendation → Report`.

---

## 4. Component Structure

- `components/ui.tsx` centralizes shared primitives (`Card`, `Badge`, `ProgressBar`, `StatCard`,
  `Tabs`, `EmptyState`, `ErrorState`, `LoadingState`, `Field`, `TextInput`, `Select`, `Button`,
  `Tooltip`, `SectionHeading`) so every page shares consistent styling and accessibility behavior.
- `layouts/MainLayout.tsx` renders the sidebar (8 sections), top bar (project name, demo-mode
  badge, notifications, user menu), and a responsive mobile drawer.
- Charts are built directly in each page with **Recharts**, all with titles, axis labels, units,
  legends, and tooltips.

---

## 5. Mock API Architecture

Mock data is never hard-coded inside UI components. Pages call functions in `src/api/*`, which
currently return mock data (via `src/mock/*`) wrapped in a simulated network delay
(`delay()` in `src/api/client.ts`). This keeps the **call signatures** identical to what a real
FastAPI backend will expose:

```
getClimate(presetId)          -> GET /climate?presetId=
getClimateProfile(presetId)   -> GET /climate/profile?presetId=
getMaterials(category?)       -> GET /materials?category=
createAnalysis(payload)       -> POST /analyses
runSimulation(analysisId)     -> POST /simulations
getSimulationStatus(sim)      -> GET /simulations/:id
getSimulationResults(id)      -> GET /simulations/:id/results
getOptimizationResults(id)    -> GET /optimization/:analysisId
getComparison(id)             -> GET /comparison/:analysisId
getRecommendation(id)         -> GET /recommendation/:analysisId
getReport(id)                 -> GET /reports/:analysisId
```

## 6. Data Models

All shared types live in `src/types/index.ts`: `ClimateData`, `ClimateProfile`, `ShelterDesign`,
`Material`, `Simulation`, `SimulationResult`, `OptimizationResult`, `ScenarioResult`,
`Recommendation`, `AnalysisProject`, `Report`. These are the contract the FastAPI backend should
implement — response payloads should match these interfaces (or a documented subset) so the API
layer in `src/api/` can be swapped from mock to real `fetch` calls with minimal page-level changes.

---

## 7. How to Run

Requires Node.js 18+.

```bash
npm install
npm run dev
```

Then open the printed local URL (typically `http://localhost:5173`). No API keys or environment
variables are required — everything runs on local mock data.

Build for production:

```bash
npm run build
npm run preview
```

---

## 8. How to Test

```bash
npm run test
```

Tests (Vitest + React Testing Library) cover:

- Sidebar navigation between pages
- Materials search/filter behavior
- Climate preset switching
- New Analysis form validation (invalid inputs blocked with clear messages)
- Design parameter mode toggling (Auto Optimize vs Manual)

---

## 9. How the Mock APIs Will Be Replaced by FastAPI

Each function in `src/api/*.ts` currently resolves mock data through `delay()`. To connect a real
backend:

1. Implement FastAPI routes matching the paths documented in section 5, returning JSON shaped like
   the interfaces in `src/types/index.ts`.
2. Replace the body of each function (e.g. `getClimate`) with a `fetch` call to
   `${BASE_URL}/climate?presetId=...` (see the commented `apiGet` helper in `src/api/client.ts`).
3. Set `VITE_API_BASE_URL` in a `.env` file to point at the FastAPI server.
4. No changes are required in pages/components, since they only depend on the function
   signatures and returned data shapes, not on how the data is fetched.

## 10. How the Frontend Will Communicate with the Final Backend

The frontend is designed to talk to FastAPI over plain REST/JSON:

- `GET` endpoints for climate, materials, results, optimization output, and reports.
- `POST /analyses` to create a new analysis from the New Analysis form payload.
- `POST /simulations` to trigger a real thermal simulation (backed by the actual AI optimizer /
  ANSYS pipeline in later phases), with `GET /simulations/:id` polled for progress instead of the
  simulated progress used in this phase.
- Authentication, environments, and real climate datasets can be layered in without restructuring
  the frontend, since all backend access is already isolated inside `src/api/`.

---

## Notes

- All charts, tables, and figures in this phase use deterministic mock data for a Ladakh
  (High Altitude Cold) scenario, clearly labelled as demo data in the UI.
- Accessibility: semantic HTML, labelled form inputs, keyboard-navigable tabs/buttons, ARIA roles
  on progress bars/dialogs/tooltips, and sufficient color contrast.
- Responsive: sidebar collapses into a mobile drawer below the `lg` breakpoint; grids reflow for
  tablet and mobile widths.
