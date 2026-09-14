import React from 'react';
import { Routes, Route } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import Dashboard from './pages/Dashboard';
import NewAnalysis from './pages/NewAnalysis';
import SimulationPage from './pages/Simulation';
import Results from './pages/Results';
import Comparison from './pages/Comparison';
import Optimization from './pages/Optimization';
import Recommendation from './pages/Recommendation';
import Materials from './pages/Materials';
import TerrainIntelligence from './pages/TerrainIntelligence';
import ReportPage from './pages/Report';

export default function App() {
  return (
    <MainLayout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/terrain" element={<TerrainIntelligence />} />
        <Route path="/new-analysis" element={<NewAnalysis />} />
        <Route path="/simulation" element={<SimulationPage />} />
        <Route path="/results" element={<Results />} />
        <Route path="/designs" element={<Comparison />} />
        <Route path="/optimization" element={<Optimization />} />
        <Route path="/recommendation" element={<Recommendation />} />
        <Route path="/materials" element={<Materials />} />
        <Route path="/report" element={<ReportPage />} />
      </Routes>
    </MainLayout>
  );
}
