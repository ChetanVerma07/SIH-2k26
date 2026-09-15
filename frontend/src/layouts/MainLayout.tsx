import React, { ReactNode, useState, useRef, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
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
  LogOut,
  Settings,
  ChevronRight,
} from 'lucide-react';
import { NotificationPanel } from '../components/NotificationPanel';
import { AuthModal } from '../components/AuthModal';
import { useAuth } from '../hooks/AuthContext';

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/new-analysis', label: 'New Analysis', icon: FilePlus2 },
  { to: '/materials', label: 'Materials', icon: Boxes },
  { to: '/terrain', label: '3D Terrain Map', icon: CloudSun },
  { to: '/designs', label: 'Designs', icon: LayoutGrid },
  { to: '/simulation', label: 'Simulations', icon: Activity },
  { to: '/optimization', label: 'Optimization', icon: Sparkles },
  { to: '/report', label: 'Reports', icon: FileText },
];

export default function MainLayout({ children }: { children: ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const { user, isAuthenticated, signOut } = useAuth();
  const navigate = useNavigate();

  // Close dropdowns on outside click
  const profileRef = useRef<HTMLDivElement>(null);
  const notifRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

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

            {/* Notification bell */}
            <div className="relative" ref={notifRef}>
              <button
                className="relative text-slate-500 hover:text-slate-800 p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
                aria-label="Notifications"
                onClick={() => { setNotifOpen(!notifOpen); setProfileOpen(false); }}
              >
                <Bell size={18} />
                <span className="absolute -top-0.5 -right-0.5 h-4 min-w-[16px] flex items-center justify-center rounded-full bg-red-500 text-white text-[9px] font-bold px-1">
                  3
                </span>
              </button>
              <NotificationPanel
                open={notifOpen}
                onClose={() => setNotifOpen(false)}
              />
            </div>

            {/* Profile / User menu */}
            <div className="relative" ref={profileRef}>
              <button
                className="flex items-center gap-2 text-sm text-slate-700 p-1 rounded-lg hover:bg-slate-100 transition-colors"
                aria-label="User menu"
                onClick={() => { setProfileOpen(!profileOpen); setNotifOpen(false); }}
              >
                <span className="h-8 w-8 rounded-full bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center text-white text-xs font-bold shadow">
                  {isAuthenticated && user ? user.name.charAt(0).toUpperCase() : <User size={16} />}
                </span>
                <span className="hidden md:inline font-medium">
                  {isAuthenticated && user ? user.name : 'Sign In'}
                </span>
              </button>

              {/* Profile dropdown */}
              {profileOpen && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setProfileOpen(false)}
                    aria-hidden="true"
                  />
                  <div className="absolute right-0 top-full mt-2 w-64 bg-white rounded-xl shadow-2xl border border-slate-200 z-50 overflow-hidden" style={{ animation: 'modal-in 0.15s ease-out' }}>
                    {isAuthenticated && user ? (
                      <>
                        {/* User info header */}
                        <div className="px-4 py-4 bg-slate-50 border-b border-slate-100">
                          <div className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center text-white font-bold shadow">
                              {user.avatar || user.name.charAt(0).toUpperCase()}
                            </div>
                            <div className="min-w-0">
                              <p className="text-sm font-semibold text-slate-800 truncate">{user.name}</p>
                              <p className="text-xs text-slate-500 truncate">{user.email}</p>
                            </div>
                          </div>
                        </div>
                        <div className="py-1">
                          <button
                            onClick={() => { setProfileOpen(false); navigate('/profile'); }}
                            className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
                          >
                            <User size={16} className="text-slate-400" />
                            My Profile
                            <ChevronRight size={14} className="ml-auto text-slate-400" />
                          </button>
                          <button
                            onClick={() => { setProfileOpen(false); navigate('/profile'); }}
                            className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
                          >
                            <Settings size={16} className="text-slate-400" />
                            Settings
                            <ChevronRight size={14} className="ml-auto text-slate-400" />
                          </button>
                        </div>
                        <div className="border-t border-slate-100 py-1">
                          <button
                            onClick={() => { setProfileOpen(false); signOut(); }}
                            className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 transition-colors"
                          >
                            <LogOut size={16} />
                            Sign Out
                          </button>
                        </div>
                      </>
                    ) : (
                      <div className="p-4 text-center">
                        <div className="h-12 w-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-3">
                          <User size={24} className="text-slate-300" />
                        </div>
                        <p className="text-sm font-semibold text-slate-800 mb-1">Welcome!</p>
                        <p className="text-xs text-slate-500 mb-4">Sign in to save your analyses and preferences.</p>
                        <button
                          onClick={() => { setProfileOpen(false); setAuthModalOpen(true); }}
                          className="w-full py-2.5 rounded-lg bg-brand-600 text-white text-sm font-semibold hover:bg-brand-700 transition-colors"
                        >
                          Sign In / Sign Up
                        </button>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        </header>

        <main className="flex-1 p-4 lg:p-6 max-w-[1400px] w-full mx-auto">{children}</main>
      </div>

      {/* Auth Modal */}
      <AuthModal open={authModalOpen} onClose={() => setAuthModalOpen(false)} />

      <style>{`
        @keyframes modal-in {
          from { opacity: 0; transform: scale(0.95) translateY(4px); }
          to { opacity: 1; transform: scale(1) translateY(0); }
        }
      `}</style>
    </div>
  );
}
