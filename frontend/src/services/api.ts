import axios, { AxiosError } from 'axios';
import { ClusterListResponse, InvestigationResponse } from '../types';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: BACKEND_URL,
  timeout: 300000, // 5 minute timeout for long-running investigations
});

export const investigationApi = {
  /**
   * Fetch available Kubernetes contexts from kubeconfig
   */
  async getClusters(): Promise<ClusterListResponse> {
    try {
      const { data } = await apiClient.get('/clusters');
      return data;
    } catch (error) {
      if (error instanceof AxiosError) {
        const detail = error.response?.data?.detail;
        throw new Error(detail || error.message || 'Failed to fetch clusters');
      }
      throw error;
    }
  },

  /**
   * Trigger a Kubernetes cluster investigation
   * Returns diagnosis with root cause analysis and fix recommendations
   */
  async investigate(payload: {
    user_id: string;
    progress_channel: string;
    namespace?: string;
    context?: string;
  }): Promise<InvestigationResponse> {
    try {
      const { data } = await apiClient.post('/investigate', payload);

      if (!data?.diagnosis) {
        throw new Error('Backend returned an empty diagnosis');
      }

      return data;
    } catch (error) {
      if (error instanceof AxiosError) {
        if (error.code === 'ECONNABORTED') {
          throw new Error('Investigation timed out. Check backend logs and try again.');
        }

        if (error.code === 'ERR_NETWORK' || !error.response) {
          throw new Error(
            'Cannot reach the backend server.\nMake sure the backend is running on ' + BACKEND_URL
          );
        }

        const detail = error.response?.data?.detail;
        throw new Error(detail || error.message || 'Investigation request failed');
      }

      throw error;
    }
  },

  /**
   * Get health status of the backend
   */
  async health() {
    const { data } = await apiClient.get('/health');
    return data;
  },
};

export default apiClient;
