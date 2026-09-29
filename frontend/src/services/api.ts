import axios from 'axios';

const API_BASE = '/api';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to add auth token if present in localStorage
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('bhusetu_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const getHealth = async () => {
  const res = await apiClient.get('/health');
  return res.data;
};

export const getDashboardStats = async () => {
  const res = await apiClient.get('/analytics/dashboard');
  return res.data;
};

export const getDocuments = async (params?: { status?: string; doc_type?: string }) => {
  const res = await apiClient.get('/documents/', { params });
  return res.data;
};

export const getDocumentDetails = async (id: string) => {
  const res = await apiClient.get(`/documents/${id}`);
  return res.data;
};

export const uploadDocuments = async (formData: FormData) => {
  const res = await apiClient.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

export const getOwnershipChain = async (id: string) => {
  const res = await apiClient.get(`/ownership/chain/${id}`);
  return res.data;
};

export const getCadastreGeoJSON = async () => {
  const res = await apiClient.get('/geo/cadastre');
  return res.data;
};

export const getParcelByULPIN = async (ulpin: string) => {
  const res = await apiClient.get(`/parcels/${ulpin}`);
  return res.data;
};

export const crossCheckParcel = async (survey_no: string, village?: string, textual_area_sqm?: number) => {
  const res = await apiClient.get('/geo/crosscheck', {
    params: { survey_no, village, textual_area_sqm }
  });
  return res.data;
};

export const getForensicFlags = async (id: string) => {
  const res = await apiClient.get(`/forensics/document/${id}`);
  return res.data;
};

export const getReviewTasks = async (status?: string) => {
  const res = await apiClient.get('/review/tasks', { params: { status } });
  return res.data;
};

export const resolveReviewTask = async (taskId: string, payload: {
  action: 'approved' | 'rejected';
  field_updates: Record<string, any>;
  notes?: string;
  reviewer_id?: string;
  is_checker?: boolean;
}) => {
  const res = await apiClient.post(`/review/tasks/${taskId}/resolve`, payload);
  return res.data;
};

export const getAuditLogs = async (params?: { document_id?: string; action?: string }) => {
  const res = await apiClient.get('/audit/', { params });
  return res.data;
};

export const verifyAuditChain = async () => {
  const res = await apiClient.get('/audit/verify-chain');
  return res.data;
};

export const getAdminRules = async () => {
  const res = await apiClient.get('/admin/rules');
  return res.data;
};

export const updateAdminRule = async (ruleId: string, enabled: boolean, updates?: Record<string, any>) => {
  const res = await apiClient.put(
    `/admin/rules/${ruleId}`,
    { enabled, updates, user_id: 'admin_officer' },
    { headers: { 'X-API-Key': 'bhusetu-admin-key' } }
  );
  return res.data;
};

export const getDILRMPDashboard = async () => {
  const res = await apiClient.get('/integration/dilrmp-dashboard');
  return res.data;
};

export const syncDILRMP = async () => {
  const res = await apiClient.post('/integration/dilrmp-sync');
  return res.data;
};

export const exportRecordsUrl = (format: 'json' | 'csv' | 'geojson') => {
  return `${API_BASE}/records/export?format=${format}`;
};
