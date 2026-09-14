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
import Climate from './pages/Climate';
import ReportPage from './pages/Report';

export default function App() {
  return (
    <MainLayout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/new-analysis" element={<NewAnalysis />} />
        <Route path="/simulation" element={<SimulationPage />} />
        <Route path="/results" element={<Results />} />
        <Route path="/designs" element={<Comparison />} />
        <Route path="/optimization" element={<Optimization />} />
        <Route path="/recommendation" element={<Recommendation />} />
        <Route path="/materials" element={<Materials />} />
        <Route path="/climate" element={<Climate />} />
        <Route path="/report" element={<ReportPage />} />
      </Routes>
    </MainLayout>
  );
}
