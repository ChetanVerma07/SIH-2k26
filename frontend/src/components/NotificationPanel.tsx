import React, { useState } from 'react';
import {
  Bell,
  CheckCircle2,
  Sparkles,
  Activity,
  FileText,
  AlertTriangle,
  X,
  Check,
} from 'lucide-react';

interface Notification {
  id: string;
  title: string;
  message: string;
  time: string;
  read: boolean;
  icon: 'success' | 'info' | 'warning' | 'activity';
  type: string;
}

const INITIAL_NOTIFICATIONS: Notification[] = [
  {
    id: 'n1',
    title: 'Simulation Completed',
    message: 'Leh Winter Shelter v3 simulation finished with 87% comfort score.',
    time: '2 min ago',
    read: false,
    icon: 'success',
    type: 'simulation',
  },
  {
    id: 'n2',
    title: 'AI Design Recommended',
    message: 'A new optimized design has been generated with 91% overall suitability.',
    time: '15 min ago',
    read: false,
    icon: 'info',
    type: 'design',
  },
  {
    id: 'n3',
    title: 'Optimization Complete',
    message: '480 candidates evaluated across 10 generations. Best score: 91.',
    time: '1 hour ago',
    read: false,
    icon: 'activity',
    type: 'optimization',
  },
  {
    id: 'n4',
    title: 'Report Ready',
    message: 'Comprehensive thermal analysis report is ready for download.',
    time: '3 hours ago',
    read: true,
    icon: 'info',
    type: 'report',
  },
  {
    id: 'n5',
    title: 'Climate Data Updated',
    message: 'Ladakh winter climate dataset has been refreshed with latest readings.',
    time: '1 day ago',
    read: true,
    icon: 'warning',
    type: 'data',
  },
];

const ICON_MAP = {
  success: { Icon: CheckCircle2, color: 'text-emerald-500', bg: 'bg-emerald-50' },
  info: { Icon: Sparkles, color: 'text-blue-500', bg: 'bg-blue-50' },
  warning: { Icon: AlertTriangle, color: 'text-amber-500', bg: 'bg-amber-50' },
  activity: { Icon: Activity, color: 'text-purple-500', bg: 'bg-purple-50' },
};

export function NotificationPanel({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [notifications, setNotifications] = useState(INITIAL_NOTIFICATIONS);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const markAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const markRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  };

  const clearAll = () => {
    setNotifications([]);
  };

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <div className="absolute right-0 top-full mt-2 w-96 max-h-[520px] bg-white rounded-xl shadow-2xl border border-slate-200 z-50 flex flex-col overflow-hidden animate-in">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 bg-slate-50/80">
          <div className="flex items-center gap-2">
            <Bell size={16} className="text-slate-600" />
            <h3 className="text-sm font-semibold text-slate-800">Notifications</h3>
            {unreadCount > 0 && (
              <span className="h-5 min-w-[20px] flex items-center justify-center rounded-full bg-red-500 text-white text-[10px] font-bold px-1.5">
                {unreadCount}
              </span>
            )}
          </div>
          <div className="flex items-center gap-1">
            {unreadCount > 0 && (
              <button
                onClick={markAllRead}
                className="text-xs text-brand-600 hover:text-brand-700 font-medium px-2 py-1 rounded hover:bg-brand-50 transition-colors"
              >
                Mark all read
              </button>
            )}
            <button
              onClick={onClose}
              className="p-1 rounded hover:bg-slate-200 text-slate-400 hover:text-slate-600 transition-colors"
              aria-label="Close notifications"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Notification List */}
        <div className="flex-1 overflow-y-auto">
          {notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center px-6">
              <div className="p-3 rounded-full bg-slate-100 text-slate-300 mb-3">
                <Bell size={24} />
              </div>
              <p className="text-sm text-slate-500 font-medium">No notifications</p>
              <p className="text-xs text-slate-400 mt-1">You're all caught up!</p>
            </div>
          ) : (
            notifications.map((n) => {
              const { Icon, color, bg } = ICON_MAP[n.icon];
              return (
                <button
                  key={n.id}
                  onClick={() => markRead(n.id)}
                  className={`w-full text-left px-4 py-3.5 border-b border-slate-50 hover:bg-slate-50 transition-colors flex gap-3 ${
                    !n.read ? 'bg-blue-50/40' : ''
                  }`}
                >
                  <div className={`shrink-0 p-2 rounded-lg ${bg}`}>
                    <Icon size={16} className={color} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <p className={`text-sm truncate ${!n.read ? 'font-semibold text-slate-800' : 'font-medium text-slate-600'}`}>
                        {n.title}
                      </p>
                      {!n.read && (
                        <span className="h-2 w-2 rounded-full bg-blue-500 shrink-0" />
                      )}
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{n.message}</p>
                    <p className="text-[10px] text-slate-400 mt-1 font-medium">{n.time}</p>
                  </div>
                </button>
              );
            })
          )}
        </div>

        {/* Footer */}
        {notifications.length > 0 && (
          <div className="border-t border-slate-100 px-4 py-2.5 bg-slate-50/80 flex justify-between items-center">
            <button
              onClick={clearAll}
              className="text-xs text-slate-500 hover:text-red-600 font-medium transition-colors"
            >
              Clear all
            </button>
            <span className="text-[10px] text-slate-400">
              {notifications.length} notification{notifications.length !== 1 ? 's' : ''}
            </span>
          </div>
        )}
      </div>
    </>
  );
}

export function useNotificationCount() {
  return INITIAL_NOTIFICATIONS.filter((n) => !n.read).length;
}
