import React from 'react';
import { NavLink } from 'react-router-dom';
import { useTranslation } from '../i18n/LanguageContext';
import {
  LayoutDashboard,
  UploadCloud,
  FileText,
  CheckSquare,
  GitFork,
  MapPin,
  History,
  Sliders,
  Network,
  LogOut,
  ShieldCheck
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const { t } = useTranslation();

  const navItems = [
    { name: t('sidebar.dashboard'), path: '/', icon: LayoutDashboard },
    { name: t('sidebar.uploadDigitize'), path: '/upload', icon: UploadCloud },
    { name: t('sidebar.landRecords'), path: '/documents', icon: FileText },
    { name: t('sidebar.humanReview'), path: '/review', icon: CheckSquare },
    { name: t('sidebar.ownershipChain'), path: '/ownership', icon: GitFork },
    { name: t('sidebar.mapCrossCheck'), path: '/map', icon: MapPin },
    { name: t('sidebar.auditTrail'), path: '/audit', icon: History },
    { name: t('sidebar.legalRulesAdmin'), path: '/admin', icon: Sliders },
    { name: t('sidebar.ecosystemIntegration'), path: '/ecosystem', icon: Network },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col shrink-0 min-h-[calc(100vh-4rem)]">
      {/* Sidebar Header */}
      <div className="p-4 border-b border-slate-800">
        <p className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
          {t('sidebar.systemTitle')}
        </p>
        <p className="text-sm font-semibold text-white mt-0.5">
          {t('sidebar.portalName')}
        </p>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-emerald-600 text-white shadow-sm font-semibold'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.name}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Positioning Callout & Status Footer */}
      <div className="p-4 border-t border-slate-800 space-y-3">
        <div className="bg-slate-800/90 rounded-lg p-3 text-xs border border-slate-700/60 space-y-1">
          <div className="flex items-center gap-1.5 text-emerald-400 font-semibold">
            <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
            <span className="truncate">{t('sidebar.offlineEngine')}</span>
          </div>
          <p className="text-slate-400 text-[11px]">{t('sidebar.recordsParcelsActive')}</p>
        </div>

        <NavLink
          to="/login"
          className="flex items-center gap-2 text-xs text-slate-400 hover:text-rose-400 transition-colors py-1"
        >
          <LogOut className="w-4 h-4" />
          <span>{t('sidebar.logout')}</span>
        </NavLink>
      </div>
    </aside>
  );
};
