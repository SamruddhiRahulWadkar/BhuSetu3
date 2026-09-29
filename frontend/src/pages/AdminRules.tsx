import React, { useEffect, useState } from 'react';
import { useTranslation } from '../i18n/LanguageContext';
import { getAdminRules, updateAdminRule } from '../services/api';
import {
  Sliders,
  CheckCircle2,
  AlertCircle,
  Save,
  Info,
  RefreshCw,
  ShieldAlert,
  GitBranch,
  Settings2,
  FileCheck
} from 'lucide-react';

export const AdminRules: React.FC = () => {
  const { t } = useTranslation();
  const [rules, setRules] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [savingId, setSavingId] = useState<string | null>(null);
  const [selectedRule, setSelectedRule] = useState<any>(null);
  const [gisTolerance, setGisTolerance] = useState<number>(10.0);

  const fetchRules = () => {
    setLoading(true);
    getAdminRules().then((data) => {
      setRules(data);
      if (data && data.length > 0) {
        setSelectedRule(data[0]);
      }
      setLoading(false);
    });
  };

  useEffect(() => {
    fetchRules();
  }, []);

  const handleToggle = async (ruleId: string, currentEnabled: boolean) => {
    setSavingId(ruleId);
    try {
      await updateAdminRule(ruleId, !currentEnabled);
      setRules((prev) =>
        prev.map((r) => (r.id === ruleId ? { ...r, enabled: !currentEnabled } : r))
      );
      if (selectedRule?.id === ruleId) {
        setSelectedRule((prev: any) => ({ ...prev, enabled: !currentEnabled }));
      }
    } catch (err: any) {
      alert(`Failed to update rule: ${err.message}`);
    } finally {
      setSavingId(null);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-slate-900">{t('rulesAdmin.title')}</h2>
          <p className="text-xs text-slate-500 mt-1">
            {t('rulesAdmin.subtitle')}
          </p>
        </div>
        <button
          onClick={fetchRules}
          className="px-3.5 py-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 inline-flex items-center gap-1.5 shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5" /> {t('rulesAdmin.reloadRules')}
        </button>
      </div>

      {/* Advisory Notice */}
      <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-center gap-2">
        <Info className="w-4 h-4 shrink-0 text-amber-700" />
        <span>{t('rulesAdmin.advisoryNotice')}</span>
      </div>

      {/* Main Layout: Rules Grid + Selected Rule Details Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Rules List */}
        <div className="lg:col-span-2 space-y-3.5">
          {loading ? (
            <div className="p-8 text-center text-xs text-slate-500">{t('common.loading')}</div>
          ) : (
            rules.map((rule) => {
              const isSelected = selectedRule?.id === rule.id;
              return (
                <div
                  key={rule.id}
                  onClick={() => setSelectedRule(rule)}
                  className={`bg-white rounded-xl border p-4 shadow-sm transition-all cursor-pointer ${
                    isSelected
                      ? 'border-emerald-600 bg-emerald-50/20 ring-1 ring-emerald-500'
                      : rule.enabled
                      ? 'border-slate-200 hover:border-slate-300'
                      : 'border-slate-200 opacity-60 bg-slate-50/50'
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-1.5">
                    <div className="flex items-center gap-2">
                      <span
                        className={`font-mono text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                          rule.severity === 'critical'
                            ? 'bg-rose-100 text-rose-800'
                            : rule.severity === 'error'
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}
                      >
                        {rule.severity}
                      </span>
                      <h3 className="text-sm font-bold text-slate-900">{rule.name}</h3>
                      <span className="text-[10px] font-mono text-slate-400">ID: {rule.id}</span>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className="text-xs font-semibold text-slate-600">
                        {rule.enabled ? t('common.active') : t('common.disabled')}
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleToggle(rule.id, rule.enabled);
                        }}
                        disabled={savingId === rule.id}
                        className={`w-11 h-6 rounded-full transition-colors relative p-0.5 focus:outline-none ${
                          rule.enabled ? 'bg-emerald-600' : 'bg-slate-300'
                        }`}
                      >
                        <div
                          className={`w-5 h-5 rounded-full bg-white shadow-md transform transition-transform ${
                            rule.enabled ? 'translate-x-5' : 'translate-x-0'
                          }`}
                        ></div>
                      </button>
                    </div>
                  </div>

                  <p className="text-xs text-slate-600 leading-relaxed">{rule.description}</p>

                  <div className="mt-2.5 pt-2.5 border-t border-slate-100 flex flex-wrap items-center gap-3 text-[11px] text-slate-500">
                    <span>
                      <strong>Applies To:</strong>{' '}
                      {Array.isArray(rule.applies_to) ? rule.applies_to.join(', ') : rule.applies_to}
                    </span>
                    <span>•</span>
                    <span>
                      <strong>Scope:</strong> {rule.state_scope || 'National (All States)'}
                    </span>
                    {rule.tolerance !== undefined && (
                      <>
                        <span>•</span>
                        <span>
                          <strong>Tolerance:</strong> &plusmn;{rule.tolerance}
                        </span>
                      </>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Right Col: Deep Rule Details & Expected vs Detected Panel */}
        <div className="space-y-4">
          {selectedRule && (
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
              <div className="border-b border-slate-100 pb-2.5">
                <span className="text-[10px] uppercase font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                  {t('rulesAdmin.ruleDetailsTitle')}
                </span>
                <h3 className="text-sm font-bold text-slate-900 mt-2">{selectedRule.name}</h3>
                <p className="text-[11px] font-mono text-slate-500">{selectedRule.id}</p>
              </div>

              <div className="space-y-2 text-xs">
                <div>
                  <span className="text-slate-500 block">{t('rulesAdmin.jurisdiction')}</span>
                  <span className="font-semibold text-slate-800">{selectedRule.state_scope || 'All States (National DILRMP Model)'}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">{t('rulesAdmin.condition')}</span>
                  <span className="font-mono text-slate-700 font-semibold">{selectedRule.description}</span>
                </div>
                <div className="grid grid-cols-2 gap-2 pt-1 border-t border-slate-100">
                  <div>
                    <span className="text-slate-500 block">{t('rulesAdmin.version')}</span>
                    <span className="font-mono font-bold text-slate-800">2026.1 (Active)</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">{t('rulesAdmin.lastUpdated')}</span>
                    <span className="font-mono text-slate-800">2026-09-29</span>
                  </div>
                </div>
              </div>

              {/* Expected vs Detected Example Card */}
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-2 text-xs">
                <span className="font-bold text-slate-800 text-[11px] block">
                  {t('rulesAdmin.expectedVsDetected')}
                </span>
                <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
                  <div className="p-2 rounded bg-emerald-50 text-emerald-900 border border-emerald-200">
                    <strong className="block text-emerald-700">Expected:</strong>
                    <span>Total share sum = 1.000</span>
                  </div>
                  <div className="p-2 rounded bg-rose-50 text-rose-900 border border-rose-200">
                    <strong className="block text-rose-700">Detected:</strong>
                    <span>Detected sum = 1.250</span>
                  </div>
                </div>
                <p className="text-[10px] text-slate-500 italic">
                  Result: Administrative inconsistency detected (Potential violation requiring review).
                </p>
              </div>
            </div>
          )}

          {/* Configurable Spatial GIS Tolerance Box */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
            <h4 className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
              <Settings2 className="w-4 h-4 text-emerald-600" />
              {t('rulesAdmin.thresholdConfig')}
            </h4>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-slate-600">GIS Area Error Threshold:</span>
                <span className="font-mono font-bold text-rose-600">{gisTolerance}%</span>
              </div>
              <input
                type="range"
                min="5"
                max="25"
                value={gisTolerance}
                onChange={(e) => setGisTolerance(Number(e.target.value))}
                className="w-full accent-emerald-600"
              />
              <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                <span>5% (Strict)</span>
                <span>10% (Default)</span>
                <span>25% (Relaxed)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
