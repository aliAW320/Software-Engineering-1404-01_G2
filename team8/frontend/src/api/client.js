import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || '/api'

export const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
})

// Core auth lives on the parent app404 at /api/auth/*
export const coreApi = axios.create({
  baseURL: '/api/auth',
  withCredentials: true,
})

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Let hooks handle logout; nothing to clear because we rely on cookies.
    }
    return Promise.reject(error)
  }
)
