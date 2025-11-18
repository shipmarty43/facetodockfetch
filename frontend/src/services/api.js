import axios from 'axios'
import store from '../store'
import { logout } from '../store/authSlice'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - logout
      store.dispatch(logout())
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  login: (username, password) =>
    api.post('/auth/login', { username, password }),

  logout: () => api.post('/auth/logout'),

  getMe: () => api.get('/auth/me'),
}

// Documents API
export const documentsAPI = {
  upload: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  list: (params) => api.get('/documents', { params }),

  get: (id) => api.get(`/documents/${id}`),

  delete: (id) => api.delete(`/documents/${id}`),

  indexDirectory: (data) => api.post('/documents/index-directory', data),

  // Get file URL for viewing
  getFileUrl: (id) => `/api/v1/documents/${id}/file`,

  // Get thumbnail URL
  getThumbnailUrl: (id) => `/api/v1/documents/${id}/thumbnail`,

  // Download file
  downloadFile: async (id, filename) => {
    const response = await api.get(`/documents/${id}/file`, {
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },
}

// Settings API
export const settingsAPI = {
  getSystemInfo: () => api.get('/admin/stats'),

  getHealth: () => axios.get('/health'),
}

// Search API
export const searchAPI = {
  searchByFace: (data) => api.post('/search/face', data),

  searchByText: (data) => api.post('/search/text', data),
}

// Admin API
export const adminAPI = {
  getStats: () => api.get('/admin/stats'),

  getTasks: () => api.get('/admin/tasks'),

  reindex: (data) => api.post('/admin/reindex', data),

  listUsers: () => api.get('/admin/users'),

  createUser: (data) => api.post('/admin/users', data),

  updateUser: (id, data) => api.put(`/admin/users/${id}`, data),

  deleteUser: (id) => api.delete(`/admin/users/${id}`),

  getLogs: (params) => api.get('/admin/logs', { params }),
}

export default api
