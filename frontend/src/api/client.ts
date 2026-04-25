/**
 * Axios API client with JWT authentication and token refresh.
 * Provides interceptors for automatic token attachment and 401 handling.
 */

import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import type {
  ApiError,
  TokenPair,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

/**
 * Pre-configured axios instance for API communication.
 * Base URL is configured via VITE_API_URL environment variable.
 */
export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor that attaches JWT access token to outgoing requests.
 * Retrieves token from localStorage and sets Authorization header.
 */
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor for handling 401 errors and automatic token refresh.
 * Attempts to refresh the access token using the refresh token.
 * On refresh failure, clears auth state and redirects to login.
 */
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle 401 errors (unauthorized)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post<TokenPair>(
            `${API_BASE_URL}/session/refresh`,
            null,
            {
              headers: {
                'Content-Type': 'application/json',
              'Authorization': `Bearer ${refreshToken}`,
              'X-Refresh-Token': refreshToken,
              'Content-Length': '0',
              'Accept': 'application/json',
              'Access-Control-Allow-Headers': 'Content-Type, Authorization',
              'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
              'Access-Control-Allow-Origin': '*',
            },
          );

          const { access_token, refresh_token: newRefreshToken, expires_in } = response.data;

          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', newRefreshToken);

          if (originalRequest.headers) {
            originalRequest.headers['Authorization'] = `Bearer ${access_token}`;
          }

          return api(originalRequest);
        } catch (refreshError) {
          // Refresh failed, clear tokens and redirect to login
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('session_id');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }
    }

    return Promise.reject(error);
  }
);

/**
 * Type guard to check if a response is an API error.
 * @param response - The response to check
 * @returns True if the response is an ApiError
 */
export function isApiError(response: unknown): response is ApiError {
  return (
    typeof response === 'object' &&
    response !== null &&
    'success' in response &&
    (response as ApiError).success === false
  );
}

/**
 * Extracts a human-readable error message from various error types.
 * @param error - The error to extract message from
 * @returns A string error message
 */
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiError>;
    if (axiosError.response?.data?.error?.message) {
      return axiosError.response.data.error.message;
    }
    if (axiosError.message) {
      return axiosError.message;
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unexpected error occurred';
}

/**
 * Checks if an error is a network connectivity error (no response received).
 * @param error - The error to check
 * @returns True if this is a network error
 */
export function isNetworkError(error: unknown): boolean {
  return axios.isAxiosError(error) && !error.response;
}

export default api;
