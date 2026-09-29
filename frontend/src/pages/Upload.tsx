import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from '../i18n/LanguageContext';
import { uploadDocuments } from '../services/api';
import { UploadCloud, FileText, CheckCircle2, AlertCircle, ArrowRight, Loader2, Sparkles } from 'lucide-react';

export const Upload: React.FC = () => {
  const { t } = useTranslation();
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files));
      setError(null);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files) {
      setSelectedFiles(Array.from(e.dataTransfer.files));
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setError('Please select at least one document image or PDF file.');
      return;
    }

    setUploading(true);
    setError(null);

    const formData = new FormData();
    selectedFiles.forEach((file) => {
      formData.append('files', file);
    });
    formData.append('uploader_id', 'revenue_officer_pune');

    try {
      const data = await uploadDocuments(formData);
      setResults(data.documents || []);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to upload and digitize documents.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold border border-emerald-300 mb-2">
          <Sparkles className="w-3 h-3 text-emerald-700" />
          {t('positioning.badge')}
        </div>
        <h2 className="text-xl font-bold text-slate-900">{t('sidebar.uploadDigitize')}</h2>
        <p className="text-xs text-slate-500 mt-1 leading-relaxed">
          Upload Khatauni, 7-12 extracts, Mutation registers, or Sale deeds (PDF, PNG, JPG).
          The pipeline computes cryptographic SHA-256 hashes, runs CLAHE deskew, dual-engine Indic OCR, regional normalization, cadastral GIS cross-check, and legal validation.
        </p>
      </div>

      {/* Drag & Drop Box */}
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        className="border-2 border-dashed border-slate-300 hover:border-emerald-500 bg-white rounded-2xl p-8 text-center transition-all cursor-pointer shadow-sm"
      >
        <div className="w-16 h-16 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto mb-4">
          <UploadCloud className="w-8 h-8" />
        </div>
        <h3 className="text-base font-semibold text-slate-800">
          Drop land record scans here, or browse files
        </h3>
        <p className="text-xs text-slate-500 mt-1">
          Supports multi-page PDF, PNG, JPEG up to 25MB per file
        </p>
        <input
          type="file"
          multiple
          accept=".pdf,.png,.jpg,.jpeg"
          onChange={handleFileChange}
          className="hidden"
          id="file-input"
        />
        <label
          htmlFor="file-input"
          className="mt-4 inline-block px-5 py-2.5 rounded-lg bg-emerald-700 text-white text-xs font-semibold hover:bg-emerald-800 cursor-pointer shadow transition-colors"
        >
          Select Files from Computer
        </label>
      </div>

      {/* Selected Files Preview */}
      {selectedFiles.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-slate-800">
              Selected Files ({selectedFiles.length})
            </h4>
            <button
              onClick={() => setSelectedFiles([])}
              className="text-xs text-slate-400 hover:text-rose-500 font-medium"
            >
              {t('common.clearAll')}
            </button>
          </div>

          <div className="max-h-48 overflow-y-auto divide-y divide-slate-100 text-xs">
            {selectedFiles.map((f, idx) => (
              <div key={idx} className="py-2 flex items-center justify-between">
                <div className="flex items-center gap-2 text-slate-700">
                  <FileText className="w-4 h-4 text-emerald-600" />
                  <span className="font-medium">{f.name}</span>
                </div>
                <span className="text-slate-400">{(f.size / 1024).toFixed(1)} KB</span>
              </div>
            ))}
          </div>

          <button
            onClick={handleUpload}
            disabled={uploading}
            className="w-full py-3 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white font-semibold text-sm shadow flex items-center justify-center gap-2 disabled:opacity-50 transition-colors"
          >
            {uploading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Running Intelligent Preprocessing & Validation Pipeline...</span>
              </>
            ) : (
              <>
                <span>Launch Digitization & Validation Pipeline</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Upload Results */}
      {results.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-slate-800 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              Processed Documents ({results.length})
            </h4>
            <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
              Pipeline Completed
            </span>
          </div>

          <div className="divide-y divide-slate-100 text-xs">
            {results.map((document) => (
              <div key={document.id} className="py-3 flex items-center justify-between">
                <div>
                  <p className="font-semibold text-slate-800">{document.filename}</p>
                  <p className="font-mono text-[10px] text-slate-400">SHA-256: {document.sha256.substring(0, 24)}...</p>
                </div>
                <div className="flex items-center gap-4">
                  <span
                    className={`px-2.5 py-1 rounded font-semibold text-[11px] ${
                      document.status === 'auto_accepted'
                        ? 'bg-emerald-100 text-emerald-800'
                        : document.status === 'field_review'
                        ? 'bg-amber-100 text-amber-800'
                        : 'bg-rose-100 text-rose-800'
                    }`}
                  >
                    {document.status.toUpperCase()}
                  </span>
                  <button
                    onClick={() => navigate(`/documents/${document.id}`)}
                    className="px-3 py-1 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-medium transition-colors"
                  >
                    {t('common.inspect')}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
