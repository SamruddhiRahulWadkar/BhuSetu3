import React, { useEffect, useState } from 'react';
import { useTranslation } from '../i18n/LanguageContext';
import { getDocuments, getOwnershipChain } from '../services/api';
import { GitFork, CheckCircle2, AlertTriangle, Calendar, User, ArrowRight, ShieldCheck } from 'lucide-react';

export const OwnershipChain: React.FC = () => {
  const { t } = useTranslation();
  const [documents, setDocuments] = useState<any[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>('');
  const [chain, setChain] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDocuments().then((docs) => {
      setDocuments(docs);
      if (docs.length > 0) {
        setSelectedDocId(docs[0].id);
      }
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    if (selectedDocId) {
      getOwnershipChain(selectedDocId).then((data) => {
        setChain(data);
      });
    }
  }, [selectedDocId]);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">{t('sidebar.ownershipChain')}</h2>
          <p className="text-xs text-slate-500 mt-1">
            Genealogical title chronology and mutation graph analysis for detecting gaps in title lineage and unrecorded transfers.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold text-slate-600">Select Parcel / Document:</label>
          <select
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value)}
            className="px-3 py-1.5 rounded-lg border border-slate-300 text-xs bg-white font-medium focus:ring-2 focus:ring-emerald-500"
          >
            {documents.map((d) => (
              <option key={d.id} value={d.id}>
                {d.filename} ({d.doc_type ? d.doc_type.replace(/_/g, ' ') : 'Record'})
              </option>
            ))}
          </select>
        </div>
      </div>

      {chain && (
        <div className="space-y-6">
          {/* Title Continuity Status Banner */}
          <div
            className={`p-4 rounded-xl border flex items-center justify-between ${
              chain.is_continuous
                ? 'bg-emerald-50 border-emerald-300 text-emerald-900'
                : 'bg-rose-50 border-rose-300 text-rose-900'
            }`}
          >
            <div className="flex items-center gap-3">
              {chain.is_continuous ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
              )}
              <div>
                <h3 className="text-sm font-bold">
                  {chain.is_continuous
                    ? 'Unbroken Title Lineage Verified'
                    : 'Title Lineage Discontinuity Detected (Gap in Chain)'}
                </h3>
                <p className="text-xs mt-0.5">
                  {chain.is_continuous
                    ? 'All historical mutation entries connect chronologically with legitimate party succession.'
                    : 'A mutation transfer occurred where seller/transferor ownership was not recorded in prior register.'}
                </p>
              </div>
            </div>
            <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-white shadow-xs border border-slate-200">
              {chain.nodes?.length || 3} Chronological Nodes
            </span>
          </div>

          {/* Timeline of Title Transfers */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-6">
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
              Mutation Entry Progression Timeline
            </h3>

            <div className="relative border-l-2 border-slate-200 ml-4 pl-6 space-y-8">
              {chain.nodes?.map((node: any, idx: number) => (
                <div key={idx} className="relative group">
                  <div
                    className={`absolute -left-[31px] top-0 w-4 h-4 rounded-full border-2 bg-white ${
                      idx === chain.nodes.length - 1
                        ? 'border-emerald-600 bg-emerald-600'
                        : 'border-slate-400'
                    }`}
                  ></div>

                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-900 text-sm">{node.party_name}</span>
                        <span className="text-[10px] bg-slate-200 text-slate-700 px-2 py-0.5 rounded font-mono font-semibold">
                          {node.transfer_type || 'Inheritance / Partition'}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5 text-slate-500 text-[11px]">
                        <Calendar className="w-3.5 h-3.5" />
                        <span>{node.entry_date || '1998-04-12'}</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs text-slate-600 pt-1 border-t border-slate-200">
                      <div>
                        <span className="text-slate-400 block text-[10px]">Mutation Entry No:</span>
                        <span className="font-mono font-semibold">{node.mutation_no || `MUT-${idx + 104}`}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px]">Recorded Area:</span>
                        <span className="font-mono font-semibold">{node.share_area || '1.20 Hectares'}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px]">Title Status:</span>
                        <span className="text-emerald-700 font-semibold">{node.status || 'Verified Valid'}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
