import React, { useState, useEffect } from 'react';
import { useTranslation, SupportedLanguage } from '../i18n/LanguageContext';
import { ShieldCheck, UserCheck, Bell, Database, Globe, RefreshCw, ChevronDown } from 'lucide-react';
import { syncDILRMP } from '../services/api';

interface NavbarProps {
  userRole?: string;
  userName?: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  userRole = 'Senior Revenue Officer (SDO)',
  userName = 'Arvind Sharma'
}) => {
  const { t, lang, setLanguage, languages } = useTranslation();
  const [syncing, setSyncing] = useState(false);
  const [storedUser, setStoredUser] = useState<any>(null);
  const [langMenuOpen, setLangMenuOpen] = useState(false);

  useEffect(() => {
    const userStr = localStorage.getItem('bhusetu_user');
    if (userStr) {
      try {
        setStoredUser(JSON.parse(userStr));
      } catch (e) {}
    }
  }, []);

  const handleDILRMPSync = async () => {
    setSyncing(true);
    try {
      const res = await syncDILRMP();
      alert(`DILRMP MIS Sync Successful!\nAcknowledgment ID: ${res.ack_id || 'DILRMP-MIS-ACK'}`);
    } catch (e: any) {
      alert(`DILRMP Sync Error: ${e?.response?.data?.detail || e.message}`);
    } finally {
      setSyncing(false);
    }
  };

  const displayName = storedUser?.full_name || userName;
  const rawRole = (storedUser?.role || userRole).toLowerCase();
  const displayRole = rawRole.includes('admin')
    ? t('navbar.roleAdmin')
    : rawRole.includes('maker') || rawRole.includes('verifier')
    ? t('navbar.roleMaker')
    : rawRole.includes('checker')
    ? t('navbar.roleChecker')
    : rawRole.includes('auditor')
    ? t('navbar.roleAuditor')
    : t('navbar.roleSDO');

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between sticky top-0 z-30 shadow-sm">
      {/* Brand Identity & System Tagline */}
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-emerald-700 text-white font-bold shadow-md shrink-0">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-slate-900">
              {t('navbar.title')}
            </h1>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-300">
              {t('navbar.sihBadge')}
            </span>
            <span className="hidden md:inline-block text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
              {t('positioning.badge')}
            </span>
          </div>
          <p className="text-[11px] text-slate-500 font-medium truncate max-w-sm sm:max-w-md">
            {t('navbar.dept')}
          </p>
        </div>
      </div>

      {/* Right Controls: DILRMP Sync, DB Health, Language Selector, User Profile */}
      <div className="flex items-center gap-3">
        {/* DILRMP Central Sync Button */}
        <button
          onClick={handleDILRMPSync}
          disabled={syncing}
          className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-100 hover:bg-slate-200 text-xs text-slate-700 font-medium border border-slate-200 transition-colors"
          title="Push progress indicators to Central DILRMP MIS"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-emerald-600 ${syncing ? 'animate-spin' : ''}`} />
          <span>{syncing ? t('navbar.syncing') : t('navbar.dilrmpSync')}</span>
        </button>

        {/* Database Health Badge */}
        <div className="hidden xl:flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 text-xs text-emerald-700 font-medium border border-emerald-200">
          <Database className="w-3.5 h-3.5 text-emerald-600" />
          <span>{t('navbar.postgisLive')}</span>
        </div>

        {/* Global Multi-Language Selector: English | हिन्दी | मराठी */}
        <div className="relative">
          <div className="flex items-center rounded-lg border border-slate-300 bg-white p-0.5 shadow-sm text-xs font-semibold">
            {languages.map((item) => {
              const isActive = lang === item.code;
              return (
                <button
                  key={item.code}
                  onClick={() => setLanguage(item.code)}
                  className={`px-2.5 py-1 rounded-md transition-all ${
                    isActive
                      ? 'bg-emerald-700 text-white shadow-xs font-bold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                  title={`Switch to ${item.label}`}
                >
                  {item.nativeName}
                </button>
              );
            })}
          </div>
        </div>

        {/* Notifications Icon */}
        <button
          className="relative p-2 rounded-lg text-slate-500 hover:bg-slate-100 transition-colors"
          title={t('navbar.notifications')}
        >
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-rose-500"></span>
        </button>

        {/* Current Officer Profile Badge */}
        <div className="flex items-center gap-3 pl-3 border-l border-slate-200">
          <div className="w-8 h-8 rounded-full bg-slate-800 text-white flex items-center justify-center text-xs font-bold shrink-0">
            {displayName.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase()}
          </div>
          <div className="hidden sm:block text-left">
            <p className="text-xs font-semibold text-slate-800 leading-tight">{displayName}</p>
            <p className="text-[10px] font-bold text-emerald-700 tracking-wider truncate max-w-[140px]">
              {displayRole}
            </p>
          </div>
        </div>
      </div>
    </header>
  );
};
