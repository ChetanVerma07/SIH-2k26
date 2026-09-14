# Frontend Merge Audit

## Frameworks & Architecture
| Feature | Phase 2 (`phase2/`) | Phase 9 (`frontend/`) | Keep | Reason |
|---------|---------------------|-----------------------|------|--------|
| **Framework** | React 18, Vite | React 18, Vite | Phase 9 | Standardized build pipeline |
| **Routing** | React Router v6 | React Router v6 | Phase 9 | Consistent with backend data flow |
| **State Management** | Context API (`DesignContext`) | Context API (`AnalysisContext`) | Phase 9 | Context aligns with FastAPI objects (Project, Design, Simulation) |
| **API Architecture** | None (Mock data files only) | Fetch wrapper (`client.ts`) -> FastAPI | Phase 9 | Must connect to real backend |

## Pages & Routing
| Feature | Phase 2 | Phase 9 | Keep | Reason |
|---------|---------|---------|------|--------|
| **Dashboard** | `Overview.tsx` (Step-by-step guide) | `Dashboard.tsx` (Project listing/setup) | Merged | Phase 9 dashboard structure is better for multiple projects, but Phase 2's visual step guide is a great onboarding UI. |
| **Setup/Design** | `ShelterDesign.tsx` (Interactive params + 3D) | `NewAnalysis.tsx` (Form) | Merged | Phase 2's 3D CSS `ShelterVisualization` is highly engaging. Must integrate into Phase 9's form. |
| **Climate** | `Climate.tsx` (Mock data selection) | `Climate.tsx` (API integration) | Phase 9 | Relies on backend `/climate/presets` |
| **Materials** | `Materials.tsx` (Mock selection) | `Materials.tsx` (API integration) | Phase 9 | Relies on backend `/materials` |
| **Simulation Tracking**| `Simulation.tsx` (Mock timer) | `Simulation.tsx` (API polling) | Phase 9 | Uses real FastAPI endpoints |
| **Analysis/Results** | `Compare.tsx` (Simple charts) | `Results.tsx`, `Comparison.tsx`, `Optimization.tsx` | Phase 9 | Much more comprehensive analytics matching the backend engine capabilities |

## UI & Design System
| Feature | Phase 2 | Phase 9 | Keep | Reason |
|---------|---------|---------|------|--------|
| **Styling Concept** | Custom "Drafting/Blueprint" aesthetic (`text-ink`, `.tick-panel`, `text-trace`) | Standard SaaS UI (`bg-white`, `shadow-sm`, `text-slate`) | Merged | Unify around Phase 9's clean standard UI but incorporate Phase 2's distinct visual cues (monospaced labels, precise borders) for engineering feel. |
| **Cards/Panels** | `Panel.tsx` (Drafting style) | `Card.tsx` (SaaS style) | Phase 9 (`Card`) | Adapt `Card` to have some of `Panel`'s crispness. |
| **Inputs** | `NumberField`, `SliderField` | `TextInput`, `Select` | Merged | Phase 2's `SliderField` is great for geometry adjustments. |
| **Visualizations** | `ShelterVisualization.tsx` (CSS 3D) | None | Phase 2 | Massive UX upgrade for the New Analysis page. |

## Action Plan for Merge
1. **Migrate Visualizer**: Move `phase2/src/components/ShelterVisualization.tsx` into `frontend/src/components/`.
2. **Update NewAnalysis**: Embed the `ShelterVisualization` inside `NewAnalysis.tsx` so users see their shelter geometry change as they type.
3. **Migrate UI Components**: Port useful form controls (like `SliderField.tsx`) from Phase 2 into `frontend/src/components/ui/` and unify styling.
4. **Refine Dashboard**: Bring Phase 2's `Overview.tsx` step-by-step visual cards into `frontend/src/pages/Dashboard.tsx` if it makes sense, or keep Phase 9's project list.
5. **Enforce Canonical Backend**: Ensure no mocked Phase 2 API calls overwrite Phase 9's `api/` layer.
6. **Testing & Validation**: Run `npm run test` and `npm run build` in `frontend/`, resolving any TS/dependency issues.
7. **Cleanup**: Delete `phase2/` only after verification is complete.
