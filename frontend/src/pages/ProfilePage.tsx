import React, { useState } from 'react';
import {
  User,
  Mail,
  Phone,
  Shield,
  Bell,
  Palette,
  Download,
  Trash2,
  LogOut,
  ChevronRight,
  Save,
  CheckCircle2,
  Settings,
  Link2,
} from 'lucide-react';
import { Card, SectionHeading, Button, TextInput, Field, Badge } from '../components/ui';
import { useAuth } from '../hooks/AuthContext';
import { useNavigate } from 'react-router-dom';

export default function ProfilePage() {
  const { user, isAuthenticated, signOut, updateProfile } = useAuth();
  const navigate = useNavigate();
  const [editName, setEditName] = useState(user?.name || '');
  const [editEmail, setEditEmail] = useState(user?.email || '');
  const [editPhone, setEditPhone] = useState(user?.phone || '');
  const [saved, setSaved] = useState(false);
  const [notifPrefs, setNotifPrefs] = useState({
    simulation: true,
    design: true,
    optimization: true,
    reports: false,
  });

  if (!isAuthenticated || !user) {
    return (
      <div className="space-y-6">
        <SectionHeading title="Profile" description="Manage your account and preferences." />
        <Card>
          <div className="text-center py-12">
            <div className="h-16 w-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-4">
              <User size={32} className="text-slate-300" />
            </div>
            <h3 className="text-lg font-semibold text-slate-800 mb-2">Not Signed In</h3>
            <p className="text-sm text-slate-500 mb-4">Sign in to manage your profile and save your analysis data.</p>
            <p className="text-xs text-slate-400">Click the user icon in the top right to sign in.</p>
          </div>
        </Card>
      </div>
    );
  }

  const handleSave = () => {
    updateProfile({ name: editName, email: editEmail, phone: editPhone || undefined });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleSignOut = () => {
    signOut();
    navigate('/');
  };

  const providerLabel: Record<string, string> = {
    email: 'Email & Password',
    google: 'Google Account',
    facebook: 'Facebook Account',
    phone: 'Phone Number',
  };

  return (
    <div className="space-y-6 max-w-3xl pb-12">
      <SectionHeading title="Profile" description="Manage your account settings and preferences." />

      {/* Profile Info */}
      <Card title="Personal Information" subtitle="Update your profile details.">
        <div className="flex items-start gap-6 mb-6">
          <div className="shrink-0">
            <div className="h-20 w-20 rounded-full bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center text-white text-2xl font-bold shadow-lg">
              {user.avatar || user.name.charAt(0).toUpperCase()}
            </div>
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-slate-800">{user.name}</h3>
            <p className="text-sm text-slate-500">{user.email}</p>
            <div className="flex items-center gap-2 mt-2">
              <Badge tone="blue">{providerLabel[user.provider]}</Badge>
              <Badge tone="green">Active</Badge>
            </div>
            <p className="text-xs text-slate-400 mt-2">
              Member since {new Date(user.createdAt).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
            </p>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-4 mb-4">
          <Field label="Full Name" htmlFor="profile-name">
            <TextInput
              id="profile-name"
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
            />
          </Field>
          <Field label="Email Address" htmlFor="profile-email">
            <TextInput
              id="profile-email"
              type="email"
              value={editEmail}
              onChange={(e) => setEditEmail(e.target.value)}
            />
          </Field>
          <Field label="Phone Number" htmlFor="profile-phone">
            <TextInput
              id="profile-phone"
              type="tel"
              value={editPhone}
              onChange={(e) => setEditPhone(e.target.value)}
              placeholder="+91 98765 43210"
            />
          </Field>
        </div>

        <div className="flex items-center gap-3">
          <Button onClick={handleSave}>
            {saved ? (
              <><CheckCircle2 size={16} /> Saved!</>
            ) : (
              <><Save size={16} /> Save Changes</>
            )}
          </Button>
        </div>
      </Card>

      {/* Account Security */}
      <Card title="Account Security" subtitle="Manage your sign-in methods and security settings.">
        <div className="space-y-3">
          <div className="flex items-center justify-between py-3 border-b border-slate-100">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-slate-100">
                <Shield size={18} className="text-slate-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-800">Password</p>
                <p className="text-xs text-slate-500">Last changed: Never (demo)</p>
              </div>
            </div>
            <Button variant="secondary" className="text-xs">
              Change Password
            </Button>
          </div>

          <div className="flex items-center justify-between py-3 border-b border-slate-100">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-slate-100">
                <Link2 size={18} className="text-slate-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-800">Linked Accounts</p>
                <p className="text-xs text-slate-500">
                  {user.provider === 'google' && 'Connected via Google'}
                  {user.provider === 'facebook' && 'Connected via Facebook'}
                  {user.provider === 'phone' && 'Connected via Phone'}
                  {user.provider === 'email' && 'Email sign-in only'}
                </p>
              </div>
            </div>
            <Badge tone="green">Connected</Badge>
          </div>

          <div className="flex items-center justify-between py-3">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-slate-100">
                <Phone size={18} className="text-slate-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-800">Two-Factor Authentication</p>
                <p className="text-xs text-slate-500">Add extra security to your account</p>
              </div>
            </div>
            <Button variant="secondary" className="text-xs">
              Enable 2FA
            </Button>
          </div>
        </div>
      </Card>

      {/* Notification Preferences */}
      <Card title="Notification Preferences" subtitle="Control what notifications you receive.">
        <div className="space-y-3">
          {[
            { key: 'simulation' as const, label: 'Simulation Updates', desc: 'When simulations complete or fail' },
            { key: 'design' as const, label: 'Design Recommendations', desc: 'When AI generates new designs' },
            { key: 'optimization' as const, label: 'Optimization Progress', desc: 'Progress updates during optimization' },
            { key: 'reports' as const, label: 'Report Generation', desc: 'When reports are ready for download' },
          ].map((item) => (
            <label
              key={item.key}
              className="flex items-center justify-between py-3 border-b border-slate-50 last:border-0 cursor-pointer group"
            >
              <div className="flex items-center gap-3">
                <Bell size={16} className="text-slate-400" />
                <div>
                  <p className="text-sm font-medium text-slate-800 group-hover:text-brand-700 transition-colors">{item.label}</p>
                  <p className="text-xs text-slate-500">{item.desc}</p>
                </div>
              </div>
              <div className="relative">
                <input
                  type="checkbox"
                  checked={notifPrefs[item.key]}
                  onChange={(e) => setNotifPrefs((prev) => ({ ...prev, [item.key]: e.target.checked }))}
                  className="sr-only peer"
                />
                <div className="w-10 h-6 rounded-full bg-slate-200 peer-checked:bg-brand-600 transition-colors" />
                <div className="absolute top-1 left-1 w-4 h-4 rounded-full bg-white shadow transition-transform peer-checked:translate-x-4" />
              </div>
            </label>
          ))}
        </div>
      </Card>

      {/* Data Management */}
      <Card title="Data Management" subtitle="Export or manage your stored analysis data.">
        <div className="space-y-3">
          <button className="w-full flex items-center justify-between py-3 border-b border-slate-100 text-left hover:bg-slate-50 rounded-lg px-3 -mx-3 transition-colors group">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-50">
                <Download size={18} className="text-blue-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-800">Export All Data</p>
                <p className="text-xs text-slate-500">Download all analyses, simulations, and results as JSON</p>
              </div>
            </div>
            <ChevronRight size={16} className="text-slate-400 group-hover:text-slate-600 transition-colors" />
          </button>
          <button className="w-full flex items-center justify-between py-3 text-left hover:bg-red-50 rounded-lg px-3 -mx-3 transition-colors group">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-red-50">
                <Trash2 size={18} className="text-red-500" />
              </div>
              <div>
                <p className="text-sm font-medium text-red-600">Delete All Data</p>
                <p className="text-xs text-slate-500">Permanently remove all locally stored data</p>
              </div>
            </div>
            <ChevronRight size={16} className="text-slate-400 group-hover:text-red-400 transition-colors" />
          </button>
        </div>
      </Card>

      {/* Sign Out */}
      <div className="flex justify-end">
        <Button variant="danger" onClick={handleSignOut}>
          <LogOut size={16} /> Sign Out
        </Button>
      </div>
    </div>
  );
}
