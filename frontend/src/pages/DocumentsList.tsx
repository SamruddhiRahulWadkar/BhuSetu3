import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from '../i18n/LanguageContext';
import { getDocuments } from '../services/api';
import { FileText, Search, Filter, ShieldCheck, AlertCircle, ArrowUpRight } from 'lucide-react';

export const DocumentsList: React.FC = () => {
  const { t } = useTranslation();
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  const fetchDocs = () => {
    setLoading(true);
    getDocuments({
      status: statusFilter || undefined,
      doc_type: typeFilter || undefined,
    })
      .then((data) => {
        setDocuments(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchDocs();
  }, [statusFilter, typeFilter]);

  const filteredDocs = documents.filter((doc) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      doc.filename.toLowerCase().includes(term) ||
      doc.sha256.toLowerCase().includes(term) ||
      doc.id.toLowerCase().includes(term)
    );
  });

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">{t('documents.title')}</h2>
          <p className="text-xs text-slate-500 mt-1">
            {t('documents.subtitle')}
          </p>
        </div>

        <Link
          to="/upload"
          className="px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg text-xs font-semibold shadow transition-colors inline-flex items-center gap-1.5 self-start"
        >
          {t('documents.uploadNew')}
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-center justify-between gap-3 text-xs">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder={t('documents.searchPlaceholder')}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-xs bg-white"
          />
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-1.5 text-slate-600 font-medium">
            <Filter className="w-3.5 h-3.5" />
            <span>{t('documents.filterStatus')}</span>
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 rounded-lg border border-slate-200 bg-white text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500 font-medium"
          >
            <option value="">{t('documents.allStatuses')}</option>
            <option value="auto_accepted">{t('documents.autoAccepted')}</option>
            <option value="field_review">{t('documents.fieldReview')}</option>
            <option value="document_review">{t('documents.fullReview')}</option>
            <option value="certified">{t('documents.certified')}</option>
          </select>

          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-2 rounded-lg border border-slate-200 bg-white text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500 font-medium"
          >
            <option value="">{t('documents.allDocTypes')}</option>
            <option value="khatauni_7_12">Khatauni / 7-12 Extract</option>
            <option value="mutation_register">Mutation Register</option>
            <option value="sale_deed">Sale Deed Summary</option>
          </select>
        </div>
      </div>

      {/* Documents Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-xs text-slate-500">{t('common.loading')}</div>
        ) : filteredDocs.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500">{t('common.noDataFound')}</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-3 px-4">{t('documents.tableFilename')}</th>
                  <th className="py-3 px-4">{t('documents.tableType')}</th>
                  <th className="py-3 px-4">{t('documents.tableConfidence')}</th>
                  <th className="py-3 px-4">{t('documents.tableStatus')}</th>
                  <th className="py-3 px-4 text-right">{t('documents.tableActions')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {filteredDocs.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded bg-slate-100 text-slate-600 flex items-center justify-center shrink-0">
                          <FileText className="w-4 h-4" />
                        </div>
                        <div>
                          <p className="font-semibold text-slate-900">{doc.filename}</p>
                          <p className="text-[10px] font-mono text-slate-400">
                            SHA: {doc.sha256.substring(0, 16)}...
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4 capitalize font-medium">
                      {doc.doc_type ? doc.doc_type.replace(/_/g, ' ') : 'Land Record'}
                    </td>
                    <td className="py-3 px-4 font-mono">
                      <span
                        className={`font-semibold px-2 py-0.5 rounded text-[11px] ${
                          (doc.overall_confidence || 0) >= 0.90
                            ? 'bg-emerald-100 text-emerald-800'
                            : (doc.overall_confidence || 0) >= 0.60
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-rose-100 text-rose-800'
                        }`}
                      >
                        {((doc.overall_confidence || 0) * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                          doc.status === 'auto_accepted' || doc.status === 'published'
                            ? 'bg-emerald-100 text-emerald-800'
                            : doc.status === 'field_review'
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-rose-100 text-rose-800'
                        }`}
                      >
                        {doc.status?.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        to={`/documents/${doc.id}`}
                        className="px-3 py-1.5 rounded bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs inline-flex items-center gap-1 transition-colors"
                      >
                        <span>{t('documents.inspectBtn')}</span>
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      </Link>
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
