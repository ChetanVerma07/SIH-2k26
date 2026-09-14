import React, { ReactNode, useState } from 'react';
import { LucideIcon, AlertTriangle, Inbox, Loader2 } from 'lucide-react';

export function Card({
  title,
  subtitle,
  action,
  children,
  className = '',
}: {
  title?: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`bg-white border border-slate-200 rounded-lg shadow-sm ${className}`}>
      {(title || action) && (
        <header className="flex items-start justify-between px-5 py-4 border-b border-slate-100">
          <div>
            {title && <h3 className="text-sm font-semibold text-slate-800">{title}</h3>}
            {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
          </div>
          {action}
        </header>
      )}
      <div className="p-5">{children}</div>
    </section>
  );
}

export function Badge({
  children,
  tone = 'slate',
}: {
  children: ReactNode;
  tone?: 'slate' | 'green' | 'amber' | 'red' | 'blue';
}) {
  const tones: Record<string, string> = {
    slate: 'bg-slate-100 text-slate-700',
    green: 'bg-emerald-100 text-emerald-700',
    amber: 'bg-amber-100 text-amber-700',
    red: 'bg-red-100 text-red-700',
    blue: 'bg-blue-100 text-blue-700',
  };
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${tones[tone]}`}
    >
      {children}
    </span>
  );
}

export function ProgressBar({ value, tone = 'blue' }: { value: number; tone?: 'blue' | 'green' | 'amber' }) {
  const tones: Record<string, string> = {
    blue: 'bg-brand-600',
    green: 'bg-emerald-500',
    amber: 'bg-amber-500',
  };
  return (
    <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden" role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={100}>
      <div
        className={`h-full ${tones[tone]} transition-all duration-500 ease-out`}
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  );
}

export function StatCard({
  label,
  value,
  unit,
  icon: Icon,
  tone = 'slate',
  hint,
}: {
  label: string;
  value: string | number;
  unit?: string;
  icon?: LucideIcon;
  tone?: 'slate' | 'blue' | 'green' | 'amber' | 'red';
  hint?: string;
}) {
  const tones: Record<string, string> = {
    slate: 'text-slate-700 bg-slate-100',
    blue: 'text-brand-700 bg-brand-50',
    green: 'text-emerald-700 bg-emerald-50',
    amber: 'text-amber-700 bg-amber-50',
    red: 'text-red-700 bg-red-50',
  };
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4 flex items-start justify-between">
      <div>
        <p className="text-xs font-medium text-slate-500">{label}</p>
        <p className="mt-1 text-2xl font-semibold text-slate-900">
          {value}
          {unit && <span className="text-sm font-normal text-slate-500 ml-1">{unit}</span>}
        </p>
        {hint && <p className="text-xs text-slate-400 mt-1">{hint}</p>}
      </div>
      {Icon && (
        <div className={`p-2 rounded-md ${tones[tone]}`}>
          <Icon size={18} />
        </div>
      )}
    </div>
  );
}

export function Tabs({
  tabs,
  active,
  onChange,
}: {
  tabs: { id: string; label: string }[];
  active: string;
  onChange: (id: string) => void;
}) {
  return (
    <div className="border-b border-slate-200 flex gap-1 overflow-x-auto scrollbar-thin" role="tablist">
      {tabs.map((t) => (
        <button
          key={t.id}
          role="tab"
          aria-selected={active === t.id}
          onClick={() => onChange(t.id)}
          className={`px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 -mb-px transition-colors ${
            active === t.id
              ? 'border-brand-600 text-brand-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

export function EmptyState({
  title,
  message,
  action,
}: {
  title: string;
  message: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-16 px-6">
      <div className="p-3 rounded-full bg-slate-100 text-slate-400 mb-3">
        <Inbox size={22} />
      </div>
      <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
      <p className="text-sm text-slate-500 mt-1 max-w-sm">{message}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function ErrorState({ title, message }: { title: string; message: string }) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-16 px-6" role="alert">
      <div className="p-3 rounded-full bg-red-50 text-red-500 mb-3">
        <AlertTriangle size={22} />
      </div>
      <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
      <p className="text-sm text-slate-500 mt-1 max-w-sm">{message}</p>
    </div>
  );
}

export function LoadingState({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-16 px-6" role="status">
      <Loader2 className="animate-spin text-brand-600 mb-3" size={22} />
      <p className="text-sm text-slate-500">{message}</p>
    </div>
  );
}

export function Field({
  label,
  htmlFor,
  children,
  hint,
}: {
  label: string;
  htmlFor: string;
  children: ReactNode;
  hint?: string;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={htmlFor} className="text-xs font-medium text-slate-600">
        {label}
      </label>
      {children}
      {hint && <p className="text-xs text-slate-400">{hint}</p>}
    </div>
  );
}

export function TextInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={`border border-slate-300 rounded-md px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 ${props.className ?? ''}`}
    />
  );
}

export function Select({
  children,
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement> & { children: ReactNode }) {
  return (
    <select
      {...props}
      className={`border border-slate-300 rounded-md px-3 py-2 text-sm text-slate-800 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 ${props.className ?? ''}`}
    >
      {children}
    </select>
  );
}

export function Button({
  children,
  variant = 'primary',
  className = '',
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'ghost' | 'danger' }) {
  const variants: Record<string, string> = {
    primary: 'bg-brand-600 text-white hover:bg-brand-700',
    secondary: 'bg-white text-slate-700 border border-slate-300 hover:bg-slate-50',
    ghost: 'text-slate-600 hover:bg-slate-100',
    danger: 'bg-red-600 text-white hover:bg-red-700',
  };
  return (
    <button
      {...props}
      className={`inline-flex items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${variants[variant]} ${className}`}
    >
      {children}
    </button>
  );
}

export function Tooltip({ text, children }: { text: string; children: ReactNode }) {
  const [show, setShow] = useState(false);
  return (
    <span
      className="relative inline-flex"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
      onFocus={() => setShow(true)}
      onBlur={() => setShow(false)}
      tabIndex={0}
    >
      {children}
      {show && (
        <span
          role="tooltip"
          className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 whitespace-nowrap rounded bg-slate-800 text-white text-xs px-2 py-1 z-10"
        >
          {text}
        </span>
      )}
    </span>
  );
}

export function SectionHeading({ title, description }: { title: string; description?: string }) {
  return (
    <div className="mb-4">
      <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
      {description && <p className="text-sm text-slate-500 mt-0.5">{description}</p>}
    </div>
  );
}

export function NumberField({
  label,
  unit,
  hint,
  value,
  onChange,
  min,
  max,
  step,
  className = '',
}: {
  label: string;
  unit?: string;
  hint?: string;
  value: number;
  onChange: (val: number) => void;
  min?: number;
  max?: number;
  step?: number;
  className?: string;
}) {
  return (
    <Field label={label + (unit ? ` (${unit})` : '')} htmlFor="" hint={hint}>
      <input
        type="number"
        value={Number.isFinite(value) ? value : ''}
        min={min}
        max={max}
        step={step ?? 0.1}
        onChange={(e) => onChange(e.target.value === '' ? NaN : Number(e.target.value))}
        className={`border border-slate-300 rounded-md px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 font-mono ${className}`}
      />
    </Field>
  );
}

export function SliderField({
  label,
  unit,
  hint,
  value,
  onChange,
  min,
  max,
  step,
}: {
  label: string;
  unit?: string;
  hint?: string;
  value: number;
  onChange: (val: number) => void;
  min: number;
  max: number;
  step?: number;
}) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-baseline justify-between text-xs font-medium text-slate-600">
        <label>
          {label}
          {unit && <span className="text-slate-400 font-mono ml-1">({unit})</span>}
        </label>
        <span className="font-mono text-brand-600">{value}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step ?? 1}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-brand-600"
      />
      {hint && <p className="text-xs text-slate-400">{hint}</p>}
    </div>
  );
}
