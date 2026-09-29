import React, { useEffect, useState } from 'react';
import { useTranslation } from '../i18n/LanguageContext';
import { getCadastreGeoJSON, crossCheckParcel } from '../services/api';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import {
  MapPin,
  AlertTriangle,
  CheckCircle2,
  Search,
  Compass,
  Layers,
  Info,
  ShieldCheck,
  Building,
  ArrowRight,
  GitBranch
} from 'lucide-react';

export const MapCrossCheck: React.FC = () => {
  const { t } = useTranslation();
  const [geoData, setGeoData] = useState<any>(null);
  const [selectedFeature, setSelectedFeature] = useState<any>(null);
  const [searchSurvey, setSearchSurvey] = useState('');
  const [checkResult, setCheckResult] = useState<any>(null);
  const [thresholdNormal, setThresholdNormal] = useState<number>(5.0);
  const [thresholdWarn, setThresholdWarn] = useState<number>(10.0);

  useEffect(() => {
    getCadastreGeoJSON().then((data) => {
      setGeoData(data);
      // Select first parcel by default
      if (data?.features?.[0]?.properties) {
        setSelectedFeature(data.features[0].properties);
      }
    });
  }, []);

  const handleSearchCheck = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchSurvey) return;
    const res = await crossCheckParcel(searchSurvey);
    setCheckResult(res);
  };

  const geoJsonStyle = (feature: any) => {
    const mismatch = feature.properties?.area_mismatch_pct || 0;
    const isError = mismatch > thresholdWarn;
    const isWarn = mismatch > thresholdNormal && mismatch <= thresholdWarn;
    return {
      fillColor: isError ? '#ef4444' : isWarn ? '#f59e0b' : '#10b981',
      weight: 2,
      opacity: 1,
      color: isError ? '#b91c1c' : isWarn ? '#d97706' : '#047857',
      fillOpacity: isError ? 0.5 : isWarn ? 0.4 : 0.3,
    };
  };

  const onEachFeature = (feature: any, layer: any) => {
    layer.on({
      click: () => {
        setSelectedFeature(feature.properties);
        setCheckResult(null);
      },
    });
  };

  const activeProp = selectedFeature || (geoData?.features?.[0]?.properties || {});
  const areaMismatch = activeProp?.area_mismatch_pct || 0;
  const isMismatchError = areaMismatch > thresholdWarn;
  const isMismatchWarn = areaMismatch > thresholdNormal && areaMismatch <= thresholdWarn;

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col bg-slate-100">
      {/* Top Map Control Bar */}
      <div className="bg-white border-b border-slate-200 px-6 py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm z-20">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-slate-900">
              {t('gis.title')}
            </h2>
            <span className="text-[10px] bg-emerald-100 text-emerald-800 font-bold px-2 py-0.5 rounded border border-emerald-200">
              {t('gis.parcelsSynced')}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            {t('gis.subtitle')}
          </p>
        </div>

        <form onSubmit={handleSearchCheck} className="flex items-center gap-2">
          <input
            type="text"
            placeholder={t('gis.searchPlaceholder')}
            value={searchSurvey}
            onChange={(e) => setSearchSurvey(e.target.value)}
            className="px-3 py-1.5 rounded-lg border border-slate-300 text-xs w-64 focus:ring-2 focus:ring-emerald-500 bg-white"
          />
          <button
            type="submit"
            className="px-3.5 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg text-xs font-semibold shadow transition-colors"
          >
            {t('gis.verifyBtn')}
          </button>
        </form>
      </div>

      {/* Main Map + Inspection Sidebar */}
      <div className="flex-1 flex overflow-hidden">
        {/* Leaflet Map Canvas */}
        <div className="flex-1 relative z-10">
          <MapContainer
            center={[18.5795, 73.9810]}
            zoom={15}
            style={{ width: '100%', height: '100%' }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {geoData && (
              <GeoJSON
                key={JSON.stringify(geoData)}
                data={geoData}
                style={geoJsonStyle}
                onEachFeature={onEachFeature}
              />
            )}
          </MapContainer>

          {/* Floating Map Legend */}
          <div className="absolute bottom-6 left-6 z-[1000] bg-white/95 backdrop-blur p-3.5 rounded-xl border border-slate-200 shadow-lg text-xs space-y-2 max-w-xs">
            <span className="font-bold text-slate-800 block text-[11px] uppercase tracking-wider">
              Configurable Spatial Discrepancy Tiers
            </span>
            <div className="flex items-center gap-2 text-[11px]">
              <div className="w-3.5 h-3.5 rounded bg-emerald-500 border border-emerald-600 shrink-0"></div>
              <span className="text-slate-700">{t('gis.thresholdNormal')}</span>
            </div>
            <div className="flex items-center gap-2 text-[11px]">
              <div className="w-3.5 h-3.5 rounded bg-amber-500 border border-amber-600 shrink-0"></div>
              <span className="text-slate-700">{t('gis.thresholdWarning')}</span>
            </div>
            <div className="flex items-center gap-2 text-[11px]">
              <div className="w-3.5 h-3.5 rounded bg-rose-500 border border-rose-600 shrink-0"></div>
              <span className="text-slate-700">{t('gis.thresholdError')}</span>
            </div>
          </div>
        </div>

        {/* Right Inspection & ULPIN Provenance Panel */}
        <div className="w-96 bg-white border-l border-slate-200 p-5 overflow-y-auto space-y-4 shadow-lg flex flex-col justify-between">
          <div className="space-y-4">
            {/* Authoritative ULPIN Relationship Chain Flow */}
            <div className="p-3 bg-slate-900 rounded-xl text-white space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-400">
                <GitBranch className="w-4 h-4" />
                <span>{t('gis.ulpinFlowTitle')}</span>
              </div>
              <div className="grid grid-cols-3 gap-1 text-[9px] text-center font-mono">
                <div className="bg-slate-800 p-1 rounded border border-slate-700 text-amber-300">
                  {t('gis.ulpinStep')}
                </div>
                <div className="bg-slate-800 p-1 rounded border border-slate-700 text-emerald-300">
                  {t('gis.parcelStep')}
                </div>
                <div className="bg-slate-800 p-1 rounded border border-slate-700 text-blue-300">
                  {t('gis.surveyStep')}
                </div>
                <div className="bg-slate-800 p-1 rounded border border-slate-700 text-slate-300">
                  {t('gis.rorStep')}
                </div>
                <div className="bg-slate-800 p-1 rounded border border-slate-700 text-slate-300">
                  {t('gis.validationStep')}
                </div>
                <div className="bg-slate-800 p-1 rounded border border-slate-700 text-slate-300">
                  {t('gis.auditStep')}
                </div>
              </div>
            </div>

            {/* Selected Parcel Details Card */}
            <div className="border border-slate-200 rounded-xl p-4 bg-slate-50/70 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                <span className="text-[10px] font-mono text-slate-500 uppercase font-bold">Selected Cadastral Parcel</span>
                <span className="text-xs font-bold text-slate-900">
                  Survey: {activeProp.survey_no || '103/1'}
                </span>
              </div>

              {/* ULPIN Highlight */}
              <div className="p-2.5 bg-amber-50 border border-amber-200 rounded-lg">
                <span className="text-[10px] uppercase font-bold text-amber-800 block">ULPIN / Bhu-Aadhaar Key:</span>
                <span className="font-mono text-xs font-bold text-slate-900">
                  {activeProp.ulpin || '27-512-004-00103-0001'}
                </span>
              </div>

              {/* Area Comparison */}
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-500">{t('gis.docArea')}:</span>
                  <span className="font-semibold text-slate-900 font-mono">
                    {activeProp.area_sqm ? (activeProp.area_sqm * (1 + (activeProp.area_mismatch_pct || 0)/100)).toFixed(1) : '12,500'} m²
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">{t('gis.gisArea')}:</span>
                  <span className="font-semibold text-slate-900 font-mono">
                    {activeProp.area_sqm ? activeProp.area_sqm.toFixed(1) : '12,480'} m²
                  </span>
                </div>
                <div className="flex justify-between pt-1 border-t border-slate-200">
                  <span className="font-bold text-slate-700">{t('gis.areaDifference')}:</span>
                  <span
                    className={`font-bold font-mono px-1.5 py-0.5 rounded text-[11px] ${
                      isMismatchError
                        ? 'bg-rose-100 text-rose-800'
                        : isMismatchWarn
                        ? 'bg-amber-100 text-amber-800'
                        : 'bg-emerald-100 text-emerald-800'
                    }`}
                  >
                    {areaMismatch > 0 ? `+${areaMismatch}%` : `${areaMismatch}%`}
                  </span>
                </div>
              </div>

              {/* Status Outcome Banner */}
              <div
                className={`p-3 rounded-lg border text-xs font-medium ${
                  isMismatchError
                    ? 'border-rose-300 bg-rose-50 text-rose-900'
                    : isMismatchWarn
                    ? 'border-amber-300 bg-amber-50 text-amber-900'
                    : 'border-emerald-300 bg-emerald-50 text-emerald-900'
                }`}
              >
                <div className="flex items-center gap-1.5 font-bold mb-1">
                  {isMismatchError ? (
                    <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                  ) : (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  )}
                  <span>
                    {isMismatchError
                      ? t('gis.statusDiscrepancy')
                      : t('gis.statusMatch')}
                  </span>
                </div>
                <p className="text-[11px] leading-relaxed opacity-90">
                  {isMismatchError
                    ? 'Difference exceeds 10% threshold. Recommended action: physical measurement by authorized taluka surveyor.'
                    : 'Spatial area is aligned within permissible statutory measurement tolerances.'}
                </p>
              </div>
            </div>
          </div>

          {/* Honest Disclaimer */}
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-[10px] text-slate-500 leading-relaxed">
            <strong>Advisory Notice:</strong> {t('gis.disclaimer')}
          </div>
        </div>
      </div>
    </div>
  );
};
