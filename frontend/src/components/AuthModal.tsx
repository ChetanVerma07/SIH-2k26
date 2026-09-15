import React, { useState } from 'react';
import { X, Mail, Lock, User, Phone, Loader2, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../hooks/AuthContext';

type AuthTab = 'signin' | 'signup';
type PhoneStep = 'number' | 'otp';

export function AuthModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { signIn, signUp, signInWithGoogle, signInWithFacebook, signInWithPhone } = useAuth();
  const [tab, setTab] = useState<AuthTab>('signin');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  // Sign-in / Sign-up form state
  const [name, setName] = useState('');
  const [email, setEmail] = useState('SIH Team');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Phone auth state
  const [showPhone, setShowPhone] = useState(false);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [otp, setOtp] = useState('');
  const [phoneStep, setPhoneStep] = useState<PhoneStep>('number');

  const resetForm = () => {
    setError('');
    setSuccess(false);
    setName('');
    setEmail('');
    setPassword('');
    setConfirmPassword('');
    setShowPhone(false);
    setPhoneNumber('');
    setOtp('');
    setPhoneStep('number');
  };

  const handleTabSwitch = (t: AuthTab) => {
    setTab(t);
    resetForm();
  };

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError('Please fill in all fields.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await signIn(email, password);
      setSuccess(true);
      setTimeout(() => { onClose(); resetForm(); }, 600);
    } catch {
      setError('Sign-in failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !email.trim() || !password.trim()) {
      setError('Please fill in all fields.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await signUp(name, email, password);
      setSuccess(true);
      setTimeout(() => { onClose(); resetForm(); }, 600);
    } catch {
      setError('Sign-up failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSocial = async (provider: 'google' | 'facebook') => {
    setLoading(true);
    setError('');
    try {
      if (provider === 'google') await signInWithGoogle();
      else await signInWithFacebook();
      setSuccess(true);
      setTimeout(() => { onClose(); resetForm(); }, 600);
    } catch {
      setError(`${provider} sign-in failed.`);
    } finally {
      setLoading(false);
    }
  };

  const handlePhoneSendOtp = (e: React.FormEvent) => {
    e.preventDefault();
    if (!phoneNumber.trim() || phoneNumber.length < 10) {
      setError('Please enter a valid phone number.');
      return;
    }
    setError('');
    setPhoneStep('otp');
  };

  const handlePhoneVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otp.trim() || otp.length < 4) {
      setError('Please enter a valid OTP.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await signInWithPhone(phoneNumber, otp);
      setSuccess(true);
      setTimeout(() => { onClose(); resetForm(); }, 600);
    } catch {
      setError('Phone verification failed.');
    } finally {
      setLoading(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => { onClose(); resetForm(); }}
        aria-hidden="true"
      />

      {/* Modal */}
      <div className="relative w-full max-w-md bg-white rounded-2xl shadow-2xl overflow-hidden" style={{ animation: 'modal-in 0.25s ease-out' }}>
        {/* Close button */}
        <button
          onClick={() => { onClose(); resetForm(); }}
          className="absolute top-4 right-4 p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors z-10"
          aria-label="Close"
        >
          <X size={18} />
        </button>

        {/* Header */}
        <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 px-6 py-8 text-center">
          <div className="h-12 w-12 rounded-xl bg-brand-600 flex items-center justify-center font-bold text-white text-lg mx-auto mb-3">
            TS
          </div>
          <h2 className="text-lg font-bold text-white">ThermalShelter AI</h2>
          <p className="text-sm text-slate-400 mt-1">Passive Design Platform</p>
        </div>

        {/* Success overlay */}
        {success && (
          <div className="absolute inset-0 z-20 bg-white/95 flex flex-col items-center justify-center">
            <CheckCircle2 size={48} className="text-emerald-500 mb-3" />
            <p className="text-lg font-semibold text-slate-800">Success!</p>
            <p className="text-sm text-slate-500 mt-1">You've been signed in.</p>
          </div>
        )}

        {/* Tabs */}
        <div className="flex border-b border-slate-200">
          {(['signin', 'signup'] as AuthTab[]).map((t) => (
            <button
              key={t}
              onClick={() => handleTabSwitch(t)}
              className={`flex-1 py-3 text-sm font-semibold transition-colors border-b-2 -mb-px ${
                tab === t
                  ? 'border-brand-600 text-brand-700 bg-brand-50/50'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              {t === 'signin' ? 'Sign In' : 'Sign Up'}
            </button>
          ))}
        </div>

        <div className="px-6 py-5">
          {/* Error */}
          {error && (
            <div className="mb-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          {/* Phone auth view */}
          {showPhone ? (
            <div>
              <button
                onClick={() => { setShowPhone(false); setError(''); setPhoneStep('number'); }}
                className="text-xs text-brand-600 hover:underline mb-4 inline-block font-medium"
              >
                ← Back to {tab === 'signin' ? 'Sign In' : 'Sign Up'}
              </button>

              {phoneStep === 'number' ? (
                <form onSubmit={handlePhoneSendOtp} className="space-y-4">
                  <div>
                    <label className="text-xs font-medium text-slate-600 mb-1 block">Phone Number</label>
                    <div className="relative">
                      <Phone size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                      <input
                        type="tel"
                        value={phoneNumber}
                        onChange={(e) => setPhoneNumber(e.target.value)}
                        placeholder="+91 98765 43210"
                        className="w-full pl-10 pr-3 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                      />
                    </div>
                  </div>
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-2.5 rounded-lg bg-brand-600 text-white text-sm font-semibold hover:bg-brand-700 disabled:opacity-50 transition-colors"
                  >
                    Send OTP
                  </button>
                </form>
              ) : (
                <form onSubmit={handlePhoneVerify} className="space-y-4">
                  <p className="text-sm text-slate-600">
                    OTP sent to <span className="font-semibold">{phoneNumber}</span>
                  </p>
                  <div>
                    <label className="text-xs font-medium text-slate-600 mb-1 block">Enter OTP</label>
                    <input
                      type="text"
                      value={otp}
                      onChange={(e) => setOtp(e.target.value)}
                      placeholder="Enter 6-digit OTP"
                      maxLength={6}
                      className="w-full px-3 py-2.5 border border-slate-300 rounded-lg text-sm text-center font-mono tracking-[0.3em] focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                    />
                    <p className="text-[10px] text-slate-400 mt-1.5">Demo: Enter any 4+ digit code</p>
                  </div>
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-2.5 rounded-lg bg-brand-600 text-white text-sm font-semibold hover:bg-brand-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
                  >
                    {loading && <Loader2 size={16} className="animate-spin" />}
                    Verify & Sign In
                  </button>
                </form>
              )}
            </div>
          ) : (
            <>
              {/* Email/Password form */}
              <form onSubmit={tab === 'signin' ? handleSignIn : handleSignUp} className="space-y-3">
                {tab === 'signup' && (
                  <div>
                    <label className="text-xs font-medium text-slate-600 mb-1 block">Full Name</label>
                    <div className="relative">
                      <User size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                      <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="Your full name"
                        className="w-full pl-10 pr-3 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                      />
                    </div>
                  </div>
                )}
                <div>
                  <label className="text-xs font-medium text-slate-600 mb-1 block">Email</label>
                  <div className="relative">
                    <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@example.com"
                      className="w-full pl-10 pr-3 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-600 mb-1 block">Password</label>
                  <div className="relative">
                    <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full pl-10 pr-3 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                    />
                  </div>
                </div>
                {tab === 'signup' && (
                  <div>
                    <label className="text-xs font-medium text-slate-600 mb-1 block">Confirm Password</label>
                    <div className="relative">
                      <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                      <input
                        type="password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        placeholder="••••••••"
                        className="w-full pl-10 pr-3 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                      />
                    </div>
                  </div>
                )}
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 rounded-lg bg-brand-600 text-white text-sm font-semibold hover:bg-brand-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
                >
                  {loading && <Loader2 size={16} className="animate-spin" />}
                  {tab === 'signin' ? 'Sign In' : 'Create Account'}
                </button>
              </form>

              {/* Divider */}
              <div className="flex items-center gap-3 my-5">
                <div className="flex-1 h-px bg-slate-200" />
                <span className="text-xs text-slate-400 font-medium">or continue with</span>
                <div className="flex-1 h-px bg-slate-200" />
              </div>

              {/* Social buttons */}
              <div className="grid grid-cols-3 gap-3">
                <button
                  onClick={() => handleSocial('google')}
                  disabled={loading}
                  className="flex flex-col items-center gap-1.5 py-3 rounded-lg border border-slate-200 hover:border-slate-300 hover:bg-slate-50 disabled:opacity-50 transition-all group"
                >
                  <svg viewBox="0 0 24 24" width="20" height="20">
                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                  </svg>
                  <span className="text-[10px] font-medium text-slate-600 group-hover:text-slate-800">Google</span>
                </button>
                <button
                  onClick={() => handleSocial('facebook')}
                  disabled={loading}
                  className="flex flex-col items-center gap-1.5 py-3 rounded-lg border border-slate-200 hover:border-blue-300 hover:bg-blue-50 disabled:opacity-50 transition-all group"
                >
                  <svg viewBox="0 0 24 24" width="20" height="20" fill="#1877F2">
                    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                  </svg>
                  <span className="text-[10px] font-medium text-slate-600 group-hover:text-blue-700">Facebook</span>
                </button>
                <button
                  onClick={() => { setShowPhone(true); setError(''); }}
                  disabled={loading}
                  className="flex flex-col items-center gap-1.5 py-3 rounded-lg border border-slate-200 hover:border-emerald-300 hover:bg-emerald-50 disabled:opacity-50 transition-all group"
                >
                  <Phone size={20} className="text-emerald-600" />
                  <span className="text-[10px] font-medium text-slate-600 group-hover:text-emerald-700">Phone</span>
                </button>
              </div>

              <p className="text-[10px] text-slate-400 text-center mt-4 leading-relaxed">
                Demo mode — no real authentication occurs. Data is stored locally in your browser.
              </p>
            </>
          )}
        </div>
      </div>

      <style>{`
        @keyframes modal-in {
          from { opacity: 0; transform: scale(0.95) translateY(10px); }
          to { opacity: 1; transform: scale(1) translateY(0); }
        }
      `}</style>
    </div>
  );
}
