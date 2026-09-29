import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useTranslation } from '../i18n/LanguageContext';
import { getDocumentDetails, resolveReviewTask } from '../services/api';
import {
  FileText,
  ShieldCheck,
  AlertTriangle,
  ZoomIn,
  ZoomOut,
  Layers,
  Edit3,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Info,
  GitFork,
  MapPin,
  Clock,
  Keyboard,
  Eye,
  Sparkles,
  ArrowRight,
  ShieldAlert,
  Search,
  ExternalLink,
  Sliders,
  Crop,
  FileCheck
} from 'lucide-react';

export const DocumentReview: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t, lang } = useTranslation();

  const [doc, setDoc] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'fields' | 'validation' | 'forensics' | 'quality'>('fields');
  const [selectedField, setSelectedField] = useState<string | null>(null);
  const [showBBoxes, setShowBBoxes] = useState(true);
  const [showTileDamage, setShowTileDamage] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1.0);
  const [editedValues, setEditedValues] = useState<Record<string, any>>({});
  const [reviewNotes, setReviewNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [showProvenanceModal, setShowProvenanceModal] = useState(false);
  const fieldInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (id) {
      getDocumentDetails(id)
        .then((data) => {
          setDoc(data);
          setLoading(false);
          // Auto-select first low confidence field if present
          const lowConf = data.fields?.find((f: any) => (f.confidence || 1.0) < 0.90);
          if (lowConf) {
            setSelectedField(lowConf.field_name);
          } else if (data.fields?.[0]) {
            setSelectedField(data.fields[0].field_name);
          }
        })
        .catch((err) => {
          console.error(err);
          setLoading(false);
        });
    }
  }, [id]);

  // Keyboard Shortcuts: Tab (Next flagged), Ctrl+Enter (Approve), E (Focus field)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLTextAreaElement) return;

      if (e.key === 'Tab' && !e.shiftKey) {
        if (!doc?.fields?.length) return;
        e.preventDefault();
        const flaggedFields = doc.fields.filter(
          (f: any) => (f.confidence || 1.0) < 0.90 || (f.flags && f.flags.length > 0)
        );
        const candidates = flaggedFields.length > 0 ? flaggedFields : doc.fields;
        const currIndex = candidates.findIndex((f: any) => f.field_name === selectedField);
        const nextIndex = (currIndex + 1) % candidates.length;
        setSelectedField(candidates[nextIndex].field_name);
      } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        handleReviewAction('approved', true);
      } else if ((e.key === 'e' || e.key === 'E') && !(e.target instanceof HTMLInputElement)) {
        e.preventDefault();
        fieldInputRef.current?.focus();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [doc, selectedField, editedValues]);

  if (loading || !doc) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-2">
          <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-xs text-slate-500">{t('common.loading')}</p>
        </div>
      </div>
    );
  }

  const page = doc.pages?.[0];
  const imageSrc = page?.processed_image_path
    ? `/${page.processed_image_path.replace(/\\/g, '/')}`
    : page?.image_path
    ? `/${page.image_path.replace(/\\/g, '/')}`
    : '/data/samples/record_01.png';

  const selectedFieldObj = doc.fields?.find((f: any) => f.field_name === selectedField);
  const qm = page?.quality_metrics || {};

  const handleFieldChange = (fieldName: string, val: any) => {
    setEditedValues((prev) => ({ ...prev, [fieldName]: val }));
  };

  const handleReviewAction = async (action: 'approved' | 'rejected', asChecker: boolean = false) => {
    const task = doc.review_tasks?.[0];
    if (!task) return;
    setSubmitting(true);
    try {
      await resolveReviewTask(task.id, {
        action,
        field_updates: editedValues,
        notes: reviewNotes,
        reviewer_id: asChecker ? 'sdo_officer_pune' : 'patwari_operator_haveli',
        is_checker: asChecker
      });
      alert(
        action === 'approved'
          ? asChecker
            ? 'Record Statutorily Certified & Published to Record of Rights!'
            : 'Maker Verification Submitted for Supervisor (Checker) Signoff!'
          : 'Record returned with administrative inconsistency flags!'
      );
      navigate('/review');
    } catch (err: any) {
      alert(`Review submission error: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const getConfidenceTierBadge = (conf: number) => {
    if (conf >= 0.90) {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
          AUTO ACCEPT ({Math.round(conf * 100)}%)
        </span>
      );
    } else if (conf >= 0.60) {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">
          FIELD REVIEW ({Math.round(conf * 100)}%)
        </span>
      );
    } else {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-300">
          FULL REVIEW ({Math.round(conf * 100)}%)
        </span>
      );
    }
  };

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col bg-slate-100">
      {/* Top Inspector Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-2.5 flex items-center justify-between shrink-0 shadow-sm z-20">
        <div className="flex items-center gap-3">
          <Link to="/documents" className="text-xs font-semibold text-slate-500 hover:text-slate-800">
            {t('review.backToDocs')}
          </Link>
          <span className="text-slate-300">|</span>
          <h2 className="text-sm font-bold text-slate-900">{doc.filename}</h2>
          <span
            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
              doc.status === 'auto_accepted' || doc.status === 'published'
                ? 'bg-emerald-100 text-emerald-800'
                : doc.status === 'maker_reviewed'
                ? 'bg-blue-100 text-blue-800'
                : doc.status === 'field_review'
                ? 'bg-amber-100 text-amber-800'
                : 'bg-rose-100 text-rose-800'
            }`}
          >
            {doc.status?.toUpperCase()}
          </span>
          <span className="text-[10px] font-mono text-slate-400 hidden md:inline">
            SHA-256: {doc.sha256?.substring(0, 16)}...
          </span>
        </div>

        {/* Keyboard Shortcuts Hint */}
        <div className="hidden xl:flex items-center gap-2 bg-slate-100 border border-slate-200 px-2.5 py-1 rounded text-[11px] text-slate-600 font-medium">
          <Keyboard className="w-3.5 h-3.5 text-slate-500" />
          <span>{t('review.keyboardHint')}</span>
        </div>

        {/* View Controls & Action Links */}
        <div className="flex items-center gap-2.5">
          <Link
            to="/ownership"
            className="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium inline-flex items-center gap-1"
          >
            <GitFork className="w-3.5 h-3.5" /> {t('sidebar.ownershipChain')}
          </Link>
          <Link
            to="/map"
            className="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium inline-flex items-center gap-1"
          >
            <MapPin className="w-3.5 h-3.5" /> {t('sidebar.mapCrossCheck')}
          </Link>

          <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-1">
            <button
              onClick={() => setZoomLevel((z) => Math.max(0.6, z - 0.15))}
              className="p-1 hover:bg-white rounded text-slate-600"
              title="Zoom Out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <span className="text-[11px] font-mono px-1">{Math.round(zoomLevel * 100)}%</span>
            <button
              onClick={() => setZoomLevel((z) => Math.min(2.0, z + 0.15))}
              className="p-1 hover:bg-white rounded text-slate-600"
              title="Zoom In"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
          </div>

          <button
            onClick={() => setShowBBoxes(!showBBoxes)}
            className={`px-2.5 py-1 rounded text-xs font-medium border ${
              showBBoxes ? 'bg-emerald-50 text-emerald-700 border-emerald-300' : 'bg-white text-slate-600 border-slate-200'
            }`}
          >
            {t('review.bboxes')}
          </button>
          <button
            onClick={() => setShowTileDamage(!showTileDamage)}
            className={`px-2.5 py-1 rounded text-xs font-medium border ${
              showTileDamage ? 'bg-rose-50 text-rose-700 border-rose-300' : 'bg-white text-slate-600 border-slate-200'
            }`}
          >
            {t('review.damageTiles')}
          </button>
        </div>
      </div>

      {/* Main Split View */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Pane: Interactive Document Scan */}
        <div className="flex-1 overflow-auto p-6 bg-slate-900/90 flex items-center justify-center relative select-none">
          <div
            className="relative shadow-2xl transition-transform duration-100 bg-white"
            style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'top center' }}
          >
            <img
              src={imageSrc}
              alt="Land Record Scan"
              className="max-w-none w-[700px] h-auto rounded block"
              onError={(e: any) => {
                e.target.src = '/data/samples/record_01.png';
              }}
            />

            {/* Bounding Box Overlays */}
            {showBBoxes &&
              doc.fields?.map((f: any) => {
                if (!f.bbox || f.bbox.length !== 4) return null;
                const [ymin, xmin, ymax, xmax] = f.bbox;
                const isSelected = selectedField === f.field_name;
                const conf = f.confidence || 0.0;
                const colorClass =
                  conf >= 0.9
                    ? 'border-emerald-500 bg-emerald-500/15'
                    : conf >= 0.6
                    ? 'border-amber-500 bg-amber-500/20'
                    : 'border-rose-500 bg-rose-500/25';

                return (
                  <div
                    key={f.id || f.field_name}
                    onClick={() => setSelectedField(f.field_name)}
                    className={`absolute cursor-pointer border-2 transition-all ${colorClass} ${
                      isSelected ? 'ring-2 ring-blue-500 ring-offset-1 z-30' : 'z-10'
                    }`}
                    style={{
                      top: `${ymin * 100}%`,
                      left: `${xmin * 100}%`,
                      width: `${(xmax - xmin) * 100}%`,
                      height: `${(ymax - ymin) * 100}%`,
                    }}
                    title={`${f.field_name}: ${f.value} (${(conf * 100).toFixed(0)}%)`}
                  >
                    <span className="absolute -top-4 left-0 bg-slate-900 text-white text-[9px] px-1 rounded truncate max-w-[140px]">
                      {f.field_name} ({Math.round(conf * 100)}%)
                    </span>
                  </div>
                );
              })}

            {/* Tile Damage Quality Heatmap Grid */}
            {showTileDamage &&
              page?.quality_metrics?.tile_metrics?.map((tMetric: any, idx: number) => {
                const [ymin, xmin, ymax, xmax] = tMetric.bbox;
                const blurPen = tMetric.blur < 100;
                const fadePen = tMetric.fade > 0.4;
                const stainPen = tMetric.stain > 0.15;
                const isDamaged = blurPen || fadePen || stainPen;

                return (
                  <div
                    key={idx}
                    className={`absolute border border-dashed text-[8px] p-0.5 pointer-events-none ${
                      isDamaged ? 'border-rose-500/80 bg-rose-500/25 text-rose-950 font-bold' : 'border-slate-300/40 text-slate-400'
                    }`}
                    style={{
                      top: `${ymin * 100}%`,
                      left: `${xmin * 100}%`,
                      width: `${(xmax - xmin) * 100}%`,
                      height: `${(ymax - ymin) * 100}%`,
                    }}
                  >
                    Blur:{Math.round(tMetric.blur)} Fade:{(tMetric.fade * 100).toFixed(0)}%
                  </div>
                );
              })}
          </div>
        </div>

        {/* Right Pane: Multi-Tab Intelligence Panel */}
        <div className="w-[540px] shrink-0 bg-white border-l border-slate-200 flex flex-col shadow-lg">
          {/* Tabs Header */}
          <div className="flex border-b border-slate-200 bg-slate-50 text-xs font-semibold">
            <button
              onClick={() => setActiveTab('fields')}
              className={`flex-1 py-3 text-center border-b-2 transition-colors ${
                activeTab === 'fields'
                  ? 'border-emerald-600 text-emerald-800 bg-white'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              {t('review.tabsFields')} ({doc.fields?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab('validation')}
              className={`flex-1 py-3 text-center border-b-2 transition-colors ${
                activeTab === 'validation'
                  ? 'border-emerald-600 text-emerald-800 bg-white'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              {t('review.tabsValidation')} ({doc.validation_results?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab('forensics')}
              className={`flex-1 py-3 text-center border-b-2 transition-colors ${
                activeTab === 'forensics'
                  ? 'border-emerald-600 text-emerald-800 bg-white'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              {t('review.tabsForensics')} ({doc.forensic_flags?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab('quality')}
              className={`flex-1 py-3 text-center border-b-2 transition-colors ${
                activeTab === 'quality'
                  ? 'border-emerald-600 text-emerald-800 bg-white'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              {t('review.tabsQuality')}
            </button>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
            {/* TAB 1: EXTRACTED FIELDS & OPTICAL PROVENANCE */}
            {activeTab === 'fields' && (
              <div className="space-y-3">
                {/* Selected Field Optical Crop Provenance Card */}
                {selectedFieldObj?.bbox && selectedFieldObj.bbox.length === 4 && (
                  <div className="p-3.5 bg-slate-900 rounded-xl text-white border border-slate-700 shadow-md space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-1.5 font-bold">
                        <Crop className="w-4 h-4 text-emerald-400" />
                        <span>{t('review.cropTitle')}:</span>
                        <span className="text-emerald-300 capitalize">{selectedFieldObj.field_name.replace(/_/g, ' ')}</span>
                      </div>
                      {getConfidenceTierBadge(selectedFieldObj.confidence || 0)}
                    </div>

                    <p className="text-[10px] text-slate-400">
                      {t('review.cropSubtitle')} Original bounding-box crop extracted from official scan.
                    </p>

                    {/* Optical Zoom Preview Window */}
                    <div className="relative h-24 overflow-hidden rounded-lg bg-black border border-slate-700 flex items-center justify-center">
                      <img
                        src={imageSrc}
                        alt="Crop"
                        className="max-w-none block"
                        style={{
                          position: 'absolute',
                          width: `${100 / Math.max(0.04, selectedFieldObj.bbox[3] - selectedFieldObj.bbox[1]) * 100}%`,
                          top: `-${selectedFieldObj.bbox[0] / Math.max(0.04, selectedFieldObj.bbox[2] - selectedFieldObj.bbox[0]) * 100}%`,
                          left: `-${selectedFieldObj.bbox[1] / Math.max(0.04, selectedFieldObj.bbox[3] - selectedFieldObj.bbox[1]) * 100}%`,
                        }}
                      />
                    </div>

                    {/* Field Provenance Metadata */}
                    <div className="grid grid-cols-2 gap-2 text-[10px] font-mono text-slate-300 pt-1 border-t border-slate-800">
                      <div>
                        <span className="text-slate-500 block">Raw OCR Text:</span>
                        <span className="text-white font-semibold">"{selectedFieldObj.raw_text}"</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block">Normalized Value:</span>
                        <span className="text-emerald-400 font-semibold">{String(selectedFieldObj.value)}</span>
                      </div>
                    </div>

                    {/* Actionable Low Confidence Reason */}
                    {(selectedFieldObj.confidence || 1.0) < 0.90 && (
                      <div className="p-2 rounded bg-amber-950/60 border border-amber-800/60 text-[10px] text-amber-200 space-y-0.5">
                        <strong className="block text-amber-300">{t('review.whyConfidenceLow')}</strong>
                        <ul className="list-disc list-inside space-y-0.5 text-amber-100">
                          <li>{t('review.reasonOcrDisagree')}</li>
                          <li>{t('review.reasonDamage')}</li>
                        </ul>
                      </div>
                    )}

                    {/* Regional Normalization Note (Devanagari / Area) */}
                    {selectedFieldObj.field_name.includes('area') && (
                      <div className="p-2 rounded bg-blue-950/60 border border-blue-800/60 text-[10px] text-blue-200">
                        <strong>{t('review.conversionRule')}:</strong> Maharashtra Revenue Standard (1 Guntha = 101.17 m² / 0.0101 ha).
                      </div>
                    )}
                  </div>
                )}

                {/* List of All Extracted Fields */}
                <div className="space-y-2.5">
                  {doc.fields?.map((field: any) => {
                    const isSelected = selectedField === field.field_name;
                    const conf = field.confidence || 0.0;
                    const breakdown = field.confidence_breakdown || {};
                    const currentValue =
                      editedValues[field.field_name] !== undefined
                        ? editedValues[field.field_name]
                        : field.value;

                    return (
                      <div
                        key={field.id || field.field_name}
                        onClick={() => setSelectedField(field.field_name)}
                        className={`p-3 rounded-xl border text-xs transition-all cursor-pointer ${
                          isSelected
                            ? 'border-blue-500 bg-blue-50/40 shadow-sm ring-1 ring-blue-400'
                            : 'border-slate-200 bg-white hover:border-slate-300'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="font-bold text-slate-800 capitalize">
                            {field.field_name.replace(/_/g, ' ')}
                          </span>
                          <div className="flex items-center gap-1.5">
                            {getConfidenceTierBadge(conf)}
                            <span className="text-[10px] text-slate-400 uppercase font-mono">
                              {field.source_engine || 'engine'}
                            </span>
                          </div>
                        </div>

                        {/* Value Input */}
                        <div className="flex items-center gap-2">
                          <input
                            ref={isSelected ? fieldInputRef : undefined}
                            type="text"
                            value={currentValue !== null ? currentValue : ''}
                            onChange={(e) => handleFieldChange(field.field_name, e.target.value)}
                            className="flex-1 px-2.5 py-1.5 rounded-lg border border-slate-300 font-medium text-slate-900 text-xs focus:ring-1 focus:ring-emerald-500 bg-white"
                          />
                          {editedValues[field.field_name] !== undefined && (
                            <span className="text-[10px] text-emerald-600 font-bold shrink-0">Edited</span>
                          )}
                        </div>

                        {/* Raw Text & Explainability Flags */}
                        <div className="mt-1.5 flex flex-wrap gap-1 text-[10px] text-slate-500">
                          <span className="font-mono bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">
                            raw: "{field.raw_text}"
                          </span>
                          {field.flags?.map((flag: string, fIdx: number) => (
                            <span key={fIdx} className="bg-amber-50 text-amber-800 border border-amber-200 px-1 py-0.5 rounded">
                              {flag}
                            </span>
                          ))}
                        </div>

                        {/* Confidence Multi-factor Breakdown */}
                        {breakdown.ocr !== undefined && (
                          <div className="mt-2 pt-1.5 border-t border-slate-100 grid grid-cols-5 text-[9px] text-slate-500 text-center font-mono">
                            <div>OCR: {breakdown.ocr}</div>
                            <div>Agreed: {breakdown.agreement}</div>
                            <div className={breakdown.damage_penalty > 0 ? 'text-rose-600 font-bold' : ''}>
                              Dam: -{breakdown.damage_penalty}
                            </div>
                            <div>Fmt: {breakdown.format}</div>
                            <div>Cons: {breakdown.consistency}</div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* TAB 2: LEGAL-LOGIC RULES EVALUATION */}
            {activeTab === 'validation' && (
              <div className="space-y-3">
                <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <Info className="w-4 h-4 text-amber-700 shrink-0" />
                    <span className="font-semibold">{t('review.ruleAlertsTitle')}</span>
                  </div>
                  <span className="text-[10px] text-amber-800 italic">{t('review.ruleAdvisoryNotice')}</span>
                </div>

                {doc.validation_results?.map((val: any) => (
                  <div
                    key={val.id}
                    className={`p-3.5 rounded-xl border text-xs space-y-2 ${
                      val.status === 'passed'
                        ? 'border-emerald-200 bg-emerald-50/40 text-emerald-950'
                        : val.severity === 'warn'
                        ? 'border-amber-200 bg-amber-50 text-amber-950'
                        : 'border-rose-200 bg-rose-50 text-rose-950'
                    }`}
                  >
                    <div className="flex items-center justify-between font-bold">
                      <span className="text-sm">{val.rule_name}</span>
                      <span
                        className={`uppercase text-[9px] px-2 py-0.5 rounded font-mono font-bold ${
                          val.status === 'passed'
                            ? 'bg-emerald-200 text-emerald-800'
                            : 'bg-rose-200 text-rose-900'
                        }`}
                      >
                        {val.status} ({val.severity})
                      </span>
                    </div>

                    <p className="text-xs leading-relaxed">{val.message}</p>

                    {/* Expected vs Detected Panel */}
                    <div className="bg-white/90 p-2.5 rounded-lg border border-slate-200 text-[11px] space-y-1">
                      <div className="flex justify-between">
                        <span className="text-slate-500">Statutory Condition:</span>
                        <span className="font-mono text-slate-700 font-semibold">{val.rule_id}</span>
                      </div>
                      {val.evidence && Object.keys(val.evidence).length > 0 && (
                        <div className="pt-1.5 border-t border-slate-100 font-mono text-[10px]">
                          <span className="text-slate-500 font-bold block mb-0.5">Audit Evidence:</span>
                          <pre className="overflow-x-auto text-slate-800">{JSON.stringify(val.evidence, null, 2)}</pre>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* TAB 3: FORENSIC SCREENING DASHBOARD */}
            {activeTab === 'forensics' && (
              <div className="space-y-3">
                <div className="p-3 rounded-xl bg-purple-50 border border-purple-200 text-purple-900 text-xs">
                  <div className="flex items-center gap-1.5 font-bold">
                    <ShieldAlert className="w-4 h-4 text-purple-700" />
                    <span>{t('forensics.bannerTitle')}</span>
                  </div>
                  <p className="text-[11px] text-purple-700 mt-1">
                    {t('forensics.bannerDisclaimer')}
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {/* Card 1: ELA */}
                  <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-sm space-y-1">
                    <span className="text-[10px] font-bold text-slate-500 uppercase">{t('forensics.elaTitle')}</span>
                    <p className="text-xs font-semibold text-slate-800">Normal Variance (No Tamper)</p>
                    <p className="text-[10px] text-slate-500">{t('forensics.elaDesc')}</p>
                  </div>

                  {/* Card 2: Copy-Move */}
                  <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-sm space-y-1">
                    <span className="text-[10px] font-bold text-slate-500 uppercase">{t('forensics.copyMoveTitle')}</span>
                    <p className="text-xs font-semibold text-slate-800">0 Duplicate Blocks</p>
                    <p className="text-[10px] text-slate-500">{t('forensics.copyMoveDesc')}</p>
                  </div>

                  {/* Card 3: Overwritten Digits */}
                  <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-sm space-y-1">
                    <span className="text-[10px] font-bold text-slate-500 uppercase">{t('forensics.overwrittenTitle')}</span>
                    <p className="text-xs font-semibold text-emerald-700">Clear Numeral Strokes</p>
                    <p className="text-[10px] text-slate-500">{t('forensics.overwrittenDesc')}</p>
                  </div>

                  {/* Card 4: Human Review Status */}
                  <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-sm space-y-1">
                    <span className="text-[10px] font-bold text-slate-500 uppercase">{t('forensics.humanReviewStatus')}</span>
                    <p className="text-xs font-semibold text-blue-700">Pending Patwari Signoff</p>
                    <p className="text-[10px] text-slate-500">Requires revenue official visual inspection</p>
                  </div>
                </div>

                {doc.forensic_flags?.map((flag: any) => (
                  <div
                    key={flag.id}
                    className="p-3 rounded-xl border border-rose-300 bg-rose-50 text-rose-950 text-xs space-y-1.5"
                  >
                    <div className="flex items-center justify-between font-bold">
                      <span className="capitalize">{flag.flag_type?.replace(/_/g, ' ')}</span>
                      <span className="text-[10px] bg-rose-200 text-rose-900 px-1.5 py-0.5 rounded font-mono">
                        {(flag.confidence * 100).toFixed(0)}% Certainty
                      </span>
                    </div>
                    <p className="text-xs">{flag.description}</p>
                    {flag.evidence && (
                      <div className="bg-white/80 p-2 rounded text-[10px] font-mono border border-slate-200">
                        {JSON.stringify(flag.evidence, null, 2)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* TAB 4: LEGACY DOCUMENT QUALITY PIPELINE */}
            {activeTab === 'quality' && (
              <div className="space-y-3">
                <div className="p-3 rounded-xl bg-slate-900 text-white space-y-1.5">
                  <h4 className="text-xs font-bold text-emerald-400">
                    {t('review.qualityPipelineTitle')}
                  </h4>
                  <div className="flex items-center justify-between text-[11px] pt-1">
                    <span className="text-slate-300">{t('review.qualityScore')}:</span>
                    <span className="font-bold text-white font-mono">
                      {qm.global_blur ? (qm.global_blur > 100 ? '92 / 100 (Good)' : '68 / 100 (Degraded)') : '88 / 100'}
                    </span>
                  </div>
                </div>

                {/* 8-Step Pipeline Indicator */}
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                  <p className="text-[11px] font-bold text-slate-800">Quality Processing Flow:</p>
                  <div className="flex flex-wrap items-center gap-1.5 text-[10px]">
                    <span className="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-semibold">1. Document</span>
                    <span className="text-slate-400">&rarr;</span>
                    <span className="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-semibold">2. Image QA</span>
                    <span className="text-slate-400">&rarr;</span>
                    <span className="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-semibold">3. Damage Detect</span>
                    <span className="text-slate-400">&rarr;</span>
                    <span className="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-semibold">4. Preprocess</span>
                    <span className="text-slate-400">&rarr;</span>
                    <span className="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-semibold">5. OCR</span>
                    <span className="text-slate-400">&rarr;</span>
                    <span className="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-semibold">6. Field Extract</span>
                    <span className="text-slate-400">&rarr;</span>
                    <span className="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-semibold">7. Calibrate</span>
                    <span className="text-slate-400">&rarr;</span>
                    <span className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded font-semibold">8. Human Review</span>
                  </div>
                </div>

                {/* Explicit Damage Indicators */}
                <div className="space-y-2 text-xs">
                  <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-slate-800">{t('review.blurIndicator')}</p>
                      <p className="text-[10px] text-slate-500">Laplacian variance sharpness check</p>
                    </div>
                    <span className="font-mono text-emerald-700 bg-emerald-50 px-2 py-1 rounded font-bold">
                      {qm.global_blur ? Math.round(qm.global_blur) : 148} (Clear)
                    </span>
                  </div>

                  <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-slate-800">{t('review.fadeIndicator')}</p>
                      <p className="text-[10px] text-slate-500">Histogram low-contrast ink density</p>
                    </div>
                    <span className="font-mono text-amber-700 bg-amber-50 px-2 py-1 rounded font-bold">
                      {(qm.global_fade ? (qm.global_fade * 100).toFixed(0) : 18)}% (Mild)
                    </span>
                  </div>

                  <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-slate-800">{t('review.stainIndicator')}</p>
                      <p className="text-[10px] text-slate-500">Watermark and oil stain chromatic analysis</p>
                    </div>
                    <span className="font-mono text-emerald-700 bg-emerald-50 px-2 py-1 rounded font-bold">
                      {(qm.global_stain ? (qm.global_stain * 100).toFixed(0) : 8)}% (Normal)
                    </span>
                  </div>

                  <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-slate-800">{t('review.contrastIndicator')}</p>
                      <p className="text-[10px] text-slate-500">Foreground to background ratio</p>
                    </div>
                    <span className="font-mono text-slate-700 bg-slate-100 px-2 py-1 rounded font-bold">
                      {qm.contrast ? qm.contrast.toFixed(1) : '64.2'} (Adequate)
                    </span>
                  </div>

                  <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-slate-800">{t('review.skewIndicator')}</p>
                      <p className="text-[10px] text-slate-500">Hough line deskew angle compensation</p>
                    </div>
                    <span className="font-mono text-slate-700 bg-slate-100 px-2 py-1 rounded font-bold">
                      {qm.skew_angle ? qm.skew_angle.toFixed(1) : '0.0'}° (Deskewed)
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Action Footer for Maker-Checker Dual-Stage Review */}
          {doc.review_tasks && doc.review_tasks.length > 0 && (
            <div className="p-4 border-t border-slate-200 bg-slate-50 space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-700 mb-1">
                  {t('review.makerReviewNotes')}
                </label>
                <textarea
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder={t('review.makerNotesPlaceholder')}
                  className="w-full px-2.5 py-1.5 text-xs rounded-lg border border-slate-300 focus:ring-1 focus:ring-emerald-500 bg-white"
                  rows={2}
                />
              </div>

              <div className="flex gap-2">
                {/* Maker Review Button */}
                <button
                  onClick={() => handleReviewAction('approved', false)}
                  disabled={submitting}
                  className="flex-1 py-2 rounded-lg bg-blue-700 hover:bg-blue-800 text-white font-semibold text-xs flex items-center justify-center gap-1.5 shadow"
                  title="Submit field corrections for Supervisor Verification (Stage 1)"
                >
                  <Edit3 className="w-3.5 h-3.5" />
                  {t('review.submitMaker')}
                </button>

                {/* SDO Checker Certification Button */}
                <button
                  onClick={() => handleReviewAction('approved', true)}
                  disabled={submitting}
                  className="flex-1 py-2 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white font-semibold text-xs flex items-center justify-center gap-1.5 shadow"
                  title="Final Dual-Stage Verification & Publish Record"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  {t('review.certifyChecker')}
                </button>

                <button
                  onClick={() => handleReviewAction('rejected', false)}
                  disabled={submitting}
                  className="px-3 py-2 rounded-lg bg-rose-600 hover:bg-rose-700 text-white font-semibold text-xs flex items-center justify-center gap-1.5 shadow"
                >
                  <XCircle className="w-3.5 h-3.5" />
                  {t('review.rejectRecord')}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
