import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: BASE_URL,
  // Analysis can take a while on large files
  timeout: 180_000,
});

// Normalize error messages from FastAPI detail fields
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error.response?.data?.detail;
    const message =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((d) => d.msg).join('; ')
          : error.message || 'An unexpected error occurred';
    return Promise.reject(new Error(message));
  },
);

/**
 * Upload a CSV file to the backend.
 * @param {File} file
 * @param {function} onUploadProgress - axios progress callback
 */
export function uploadFile(file, onUploadProgress) {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress,
  });
}

/**
 * Trigger the cleaning + validation pipeline for an uploaded file.
 * @param {string} uploadId
 * @param {object} options - AnalyzeRequest body
 */
export function analyzeDataset(uploadId, options = {}) {
  return api.post(`/analyze/${uploadId}`, options);
}

/** Check backend health */
export function getHealth() {
  return api.get('/health');
}

/** Build the URL to open the HTML report in a new browser tab */
export function getReportUrl(uploadId) {
  return `${BASE_URL}/report/${uploadId}`;
}

/** Build the URL to download the cleaned CSV */
export function getDownloadUrl(uploadId) {
  return `${BASE_URL}/download-cleaned/${uploadId}`;
}

export default api;
