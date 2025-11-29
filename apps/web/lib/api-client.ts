// API client with error handling and loading states
'use client';

import { useState, useCallback } from 'react';

export interface ApiError {
  message: string;
  detail?: string;
  status?: number;
}

export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const defaultHeaders: HeadersInit = {
      'Content-Type': 'application/json',
    };

    // Get token from storage
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
      }
    }

    const config: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        let errorData: any;
        try {
          errorData = await response.json();
        } catch {
          errorData = { detail: response.statusText };
        }

        throw {
          message: errorData.detail || 'Request failed',
          detail: errorData.detail,
          status: response.status,
        } as ApiError;
      }

      // Handle 204 No Content
      if (response.status === 204) {
        return {} as T;
      }

      return await response.json();
    } catch (error: any) {
      if (error.message && error.status) {
        throw error;
      }
      
      // Network error
      throw {
        message: 'Network error. Please check your connection.',
        detail: error.message,
        status: 0,
      } as ApiError;
    }
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  async patch<T>(endpoint: string, data: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }
}

export const apiClient = new ApiClient(API_BASE_URL);

// React hook for API calls with loading and error states
export function useAsync<T>() {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(
    async (promise: Promise<T>) => {
      setState({ data: null, loading: true, error: null });
      
      try {
        const data = await promise;
        setState({ data, loading: false, error: null });
        return data;
      } catch (error: any) {
        const apiError: ApiError = {
          message: error.message || 'An error occurred',
          detail: error.detail,
          status: error.status,
        };
        setState({ data: null, loading: false, error: apiError });
        throw apiError;
      }
    },
    []
  );

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return { ...state, execute, reset };
}

// Specific API endpoints
export const api = {
  // Auth
  auth: {
    githubCallback: (code: string, state?: string) =>
      apiClient.post('/auth/github/callback', { code, state }),
    getMe: () => apiClient.get('/auth/me'),
  },

  // Collector
  collector: {
    sync: (source: 'github' | 'solvedac' | 'velog', force_full_sync = false) =>
      apiClient.post('/collector/sync', { source, force_full_sync }),
    getStatus: () => apiClient.get('/collector/status'),
    getConfig: () => apiClient.get('/collector/config'),
  },

  // Dashboard
  dashboard: {
    getStats: () => apiClient.get('/dashboard/stats'),
    getSummary: (range: 'week' | 'month' | 'year' = 'week') =>
      apiClient.get(`/dashboard/summary?range=${range}`),
  },

  // Repos
  repos: {
    list: (page = 1, pageSize = 20) =>
      apiClient.get(`/repos?page=${page}&page_size=${pageSize}`),
    get: (repoId: number) => apiClient.get(`/repos/${repoId}`),
    getCommits: (repoId: number, page = 1, pageSize = 20) =>
      apiClient.get(`/repos/${repoId}/commits?page=${page}&page_size=${pageSize}`),
    getStats: () => apiClient.get('/repos/stats'),
  },

  // Weekly summaries
  weekly: {
    list: (page = 1, pageSize = 10, year?: number, month?: number) => {
      let url = `/weekly?page=${page}&page_size=${pageSize}`;
      if (year) url += `&year=${year}`;
      if (month) url += `&month=${month}`;
      return apiClient.get(url);
    },
    get: (weeklyId: number) => apiClient.get(`/weekly/${weeklyId}`),
    create: (startDate: string, endDate: string, regenerate = false) =>
      apiClient.post('/weekly', { start_date: startDate, end_date: endDate, regenerate }),
    delete: (weeklyId: number) => apiClient.delete(`/weekly/${weeklyId}`),
    getStats: () => apiClient.get('/weekly/stats/overview'),
  },

  // Content generation
  content: {
    generate: (data: {
      content_type: 'blog_post' | 'portfolio' | 'summary' | 'report';
      title?: string;
      context?: string;
      date_range_start?: string;
      date_range_end?: string;
      use_style_profile?: boolean;
    }) => apiClient.post('/generate/content', data),
    list: (page = 1, pageSize = 20, filters?: any) => {
      let url = `/generate/content?page=${page}&page_size=${pageSize}`;
      if (filters) {
        Object.keys(filters).forEach(key => {
          if (filters[key] !== undefined) {
            url += `&${key}=${filters[key]}`;
          }
        });
      }
      return apiClient.get(url);
    },
    get: (contentId: number) => apiClient.get(`/generate/content/${contentId}`),
    update: (contentId: number, data: { title?: string; content?: string; metadata?: any }) =>
      apiClient.put(`/generate/content/${contentId}`, data),
    regenerate: (contentId: number, newContext?: string, useStyleProfile = true) =>
      apiClient.post(`/generate/content/${contentId}/regenerate`, {
        content_id: contentId,
        new_context: newContext,
        use_style_profile: useStyleProfile,
      }),
    delete: (contentId: number) => apiClient.delete(`/generate/content/${contentId}`),
    getStats: () => apiClient.get('/generate/stats'),
  },

  // Profile
  profile: {
    get: () => apiClient.get('/profile'),
    update: (data: any) => apiClient.put('/profile', data),
    getStyleProfile: () => apiClient.get('/profile/style'),
    updateStyleProfile: (data: any) => apiClient.put('/profile/style', data),
  },
};
