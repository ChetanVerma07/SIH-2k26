import React, { ReactNode, useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FilePlus2,
  LayoutGrid,
  Boxes,
  CloudSun,
  Activity,
  Sparkles,
  FileText,
  Menu,
  X,
  Bell,
  User,
  Building2,
} from 'lucide-react';

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/terrain', label: '3D Terrain Map', icon: CloudSun },
  { to: '/new-analysis', label: 'New Analysis', icon: FilePlus2 },
  { to: '/designs', label: 'Designs', icon: LayoutGrid },
  { to: '/materials', label: 'Materials', icon: Boxes },
  { to: '/simulation', label: 'Simulations', icon: Activity },
  { to: '/optimization', label: 'Optimization', icon: Sparkles },
  { to: '/report', label: 'Reports', icon: FileText },
];

export default function MainLayout({ children }: { children: ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen flex bg-slate-50">
      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-30 w-64 bg-slate-900 text-slate-200 transform transition-transform lg:translate-x-0 lg:static lg:z-auto ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        aria-label="Primary"
      >
        <div className="h-16 flex items-center gap-2 px-5 border-b border-slate-800">
          <div className="h-8 w-8 rounded-md bg-brand-600 flex items-center justify-center font-bold text-white text-sm">
            TS
          </div>
          <div>
            <p className="text-sm font-semibold text-white leading-tight">ThermalShelter AI</p>
            <p className="text-[11px] text-slate-400 leading-tight">Passive Design Platform</p>
          </div>
          <button
            className="ml-auto lg:hidden text-slate-400"
            onClick={() => setMobileOpen(false)}
            aria-label="Close navigation"
          >
            <X size={18} />
          </button>
        </div>
        <nav className="p-3 space-y-1" aria-label="Main sections">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-brand-600 text-white'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              <item.icon size={17} />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="absolute bottom-0 inset-x-0 p-4 border-t border-slate-800 text-[11px] text-slate-500">
          SIH 2026 Prototype — Phase 9 Frontend Demo
        </div>
      </aside>

      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-20 lg:hidden"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Main column */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top nav */}
        <header className="h-16 bg-white border-b border-slate-200 flex items-center px-4 lg:px-6 gap-4 sticky top-0 z-10">
          <button
            className="lg:hidden text-slate-600"
            onClick={() => setMobileOpen(true)}
            aria-label="Open navigation"
          >
            <Menu size={20} />
          </button>
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <Building2 size={16} className="text-slate-400" />
            <span className="font-medium text-slate-800">Current Project:</span>
            <span>Leh Winter Shelter v3</span>
          </div>
          <div className="ml-auto flex items-center gap-4">
            <span className="hidden sm:inline-flex items-center gap-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              Demo Mode — Mock Data
            </span>
            <button className="relative text-slate-500 hover:text-slate-800" aria-label="Notifications">
              <Bell size={18} />
              <span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-red-500" />
            </button>
            <button
              className="flex items-center gap-2 text-sm text-slate-700"
              aria-label="User menu"
            >
              <span className="h-8 w-8 rounded-full bg-slate-200 flex items-center justify-center">
                <User size={16} />
              </span>
              <span className="hidden md:inline font-medium">SIH Team</span>
            </button>
          </div>
        </header>

        <main className="flex-1 p-4 lg:p-6 max-w-[1400px] w-full mx-auto">{children}</main>
      </div>
    </div>
  );
}
