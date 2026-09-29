import React, { useEffect, useState } from 'react';
import { useTranslation } from '../i18n/LanguageContext';
import { getAuditLogs, verifyAuditChain } from '../services/api';
import {
  History,
  Shield,
  Filter,
  Search,
  CheckCircle2,
  AlertTriangle,
  Lock,
  RefreshCw,
  GitCommit,
  ArrowRight,
  ShieldCheck
} from 'lucide-react';

export const AuditLog: React.FC = () => {
  const { t } = useTranslation();
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<any>(null);

  const fetchLogs = () => {
    setLoading(true);
    getAuditLogs({ action: actionFilter || undefined })
      .then((data) => {
        setLogs(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchLogs();
  }, [actionFilter]);

  const handleVerifyChain = async () => {
    setVerifying(true);
    setVerificationResult(null);
    try {
      const res = await verifyAuditChain();
      setVerificationResult(res);
    } catch (e: any) {
      setVerificationResult({
        chain_valid: false,
        message: `Verification check error: ${e.message}`,
        total_blocks: logs.length
      });
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-900">{t('audit.title')}</h2>
            <span className="text-[10px] bg-slate-100 text-slate-700 font-mono px-2 py-0.5 rounded border border-slate-200">
              SHA-256 Hash Chain
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            {t('audit.subtitle')}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleVerifyChain}
            disabled={verifying}
            className="px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg text-xs font-semibold shadow transition-colors flex items-center gap-1.5"
          >
            <ShieldCheck className={`w-4 h-4 ${verifying ? 'animate-spin' : ''}`} />
            <span>{verifying ? 'Verifying Hashes...' : t('audit.verifyChainBtn')}</span>
          </button>

          <div className="flex items-center gap-1.5 text-xs text-slate-600 bg-white border border-slate-300 rounded-lg px-2.5 py-1.5">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            <select
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              className="bg-transparent text-xs font-medium focus:outline-none"
            >
              <option value="">{t('common.all')} Actions</option>
              <option value="DOCUMENT_UPLOADED">DOCUMENT_UPLOADED</option>
              <option value="DOCUMENT_PREPROCESSED">DOCUMENT_PREPROCESSED</option>
              <option value="PIPELINE_COMPLETED">PIPELINE_COMPLETED</option>
              <option value="REVIEW_TASK_CREATED">REVIEW_TASK_CREATED</option>
              <option value="REVIEW_APPROVED">REVIEW_APPROVED</option>
              <option value="RULE_UPDATED">RULE_UPDATED</option>
            </select>
          </div>
        </div>
      </div>

      {/* Verification Results Panel & Visual Hash Chain */}
      {verificationResult && (
        <div
          className={`p-5 rounded-2xl border shadow-sm space-y-4 ${
            verificationResult.chain_valid
              ? 'bg-emerald-50/70 border-emerald-300 text-emerald-950'
              : 'bg-rose-50/70 border-rose-300 text-rose-950'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {verificationResult.chain_valid ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-rose-600" />
              )}
              <h3 className="text-sm font-bold">
                {verificationResult.chain_valid
                  ? t('audit.chainValid')
                  : 'Audit Hash Continuity Broken!'}
              </h3>
            </div>
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-white/80 border border-slate-300">
              {verificationResult.total_blocks} Blocks Verified
            </span>
          </div>

          <p className="text-xs leading-relaxed">
            {verificationResult.message || t('audit.chainValidDesc')}
          </p>

          {/* Interactive Visual Chain (Genesis -> Block 1 -> Block 2 -> ... -> Latest) */}
          <div className="bg-white/90 p-4 rounded-xl border border-slate-200 space-y-2">
            <p className="text-[11px] font-bold text-slate-700 uppercase tracking-wider">
              Cryptographic Chaining Progression:
            </p>
            <div className="flex flex-wrap items-center gap-2 text-[10px] font-mono">
              <div className="p-2 rounded bg-slate-900 text-amber-300 border border-slate-800 font-bold">
                GENESIS BLOCK (000000...)
              </div>
              <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
              <div className="p-2 rounded bg-slate-100 text-slate-700 border border-slate-300">
                Block #1: PIPELINE_START
              </div>
              <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
              <div className="p-2 rounded bg-slate-100 text-slate-700 border border-slate-300">
                Block #2: OCR_EXTRACT
              </div>
              <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
              <div className="p-2 rounded bg-slate-100 text-slate-700 border border-slate-300">
                ... (Chained)
              </div>
              <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
              <div className="p-2 rounded bg-emerald-700 text-white border border-emerald-800 font-bold">
                Block #{verificationResult.total_blocks || logs.length}: CERTIFIED & SIGNED
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Audit Trail Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-xs text-slate-500">{t('common.loading')}</div>
        ) : logs.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500">{t('common.noDataFound')}</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-3 px-4">{t('audit.tableTimestamp')}</th>
                  <th className="py-3 px-4">{t('audit.tableAction')}</th>
                  <th className="py-3 px-4">{t('audit.tableDocId')}</th>
                  <th className="py-3 px-4">{t('audit.tableUserRole')}</th>
                  <th className="py-3 px-4">{t('audit.tablePrevHash')}</th>
                  <th className="py-3 px-4">{t('audit.tableCurrHash')}</th>
                  <th className="py-3 px-4">{t('audit.tableDetails')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/70 font-mono text-[11px]">
                    <td className="py-3 px-4 whitespace-nowrap text-slate-500 font-sans">
                      {log.timestamp ? new Date(log.timestamp).toLocaleString() : 'N/A'}
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                        {log.action}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-600">
                      {log.document_id ? log.document_id.substring(0, 8) + '...' : 'System'}
                    </td>
                    <td className="py-3 px-4 text-slate-800 font-medium font-sans">
                      {log.user_id || 'system'}
                    </td>
                    <td className="py-3 px-4 text-slate-400 max-w-[120px] truncate" title={log.previous_hash}>
                      {log.previous_hash ? log.previous_hash.substring(0, 12) + '...' : 'GENESIS'}
                    </td>
                    <td className="py-3 px-4 text-emerald-700 font-bold max-w-[120px] truncate" title={log.current_hash}>
                      {log.current_hash ? log.current_hash.substring(0, 12) + '...' : 'N/A'}
                    </td>
                    <td className="py-3 px-4 text-slate-600 max-w-xs truncate font-sans">
                      {JSON.stringify(log.details || {})}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
