import axios from 'axios';

const serverApiBase =
  process.env.BACKEND_BASE_URL || process.env.NEXT_PUBLIC_BACKEND_BASE_URL || 'http://127.0.0.1:8001';

const api = axios.create({
  baseURL: typeof window !== 'undefined' ? '/api' : `${serverApiBase}/api`,
});

const refreshClient = axios.create({
  baseURL: typeof window !== 'undefined' ? '/api' : `${serverApiBase}/api`,
});

export const getCoverImageUrl = (datasetId: string, coverImageKey?: string | null) => {
  const versionPart = coverImageKey ? `?v=${encodeURIComponent(coverImageKey)}` : '';
  return `/api/datasets/by-id/${datasetId}/cover-image${versionPart}`;
};

// Add a request interceptor
api.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (typeof window === 'undefined') {
      return Promise.reject(error);
    }

    const originalRequest = error?.config;
    const status = error?.response?.status;

    if (status !== 401 || !originalRequest || originalRequest._retry) {
      return Promise.reject(error);
    }

    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;
    try {
      const refreshRes = await refreshClient.post('/auth/refresh', {
        refresh_token: refreshToken,
      });
      const nextAccessToken = refreshRes.data?.access_token;
      const nextRefreshToken = refreshRes.data?.refresh_token;
      const nextUser = refreshRes.data?.user;

      if (!nextAccessToken) {
        throw new Error('Missing access token after refresh');
      }

      localStorage.setItem('token', nextAccessToken);
      if (nextRefreshToken) {
        localStorage.setItem('refresh_token', nextRefreshToken);
      }
      if (nextUser) {
        localStorage.setItem('user', JSON.stringify(nextUser));
      }

      originalRequest.headers = originalRequest.headers || {};
      originalRequest.headers.Authorization = `Bearer ${nextAccessToken}`;
      return api(originalRequest);
    } catch (refreshError) {
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      return Promise.reject(refreshError);
    }
  }
);

export default api;
