
export const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000'

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

function buildUrl(path, params) {
  const url = new URL(path, API_URL)
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== '') url.searchParams.set(key, value)
    }
  }
  return url
}

async function request(tokenKey, method, path, { params, body } = {}) {
  const headers = {}
  const token = tokenKey ? localStorage.getItem(tokenKey) : null
  if (token) headers.Authorization = `Bearer ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  let response
  try {
    response = await fetch(buildUrl(path, params), {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined
    })
  } catch {
    throw new ApiError('Cannot reach the server. Is the backend running?', 0)
  }
  return { response, token }
}

async function json(tokenKey, method, path, options) {
  const { response, token } = await request(tokenKey, method, path, options)
  const isJson = (response.headers.get('content-type') || '').includes('application/json')
  const data = isJson ? await response.json() : null

  if (!response.ok) {
    
    if (token && (response.status === 401 || response.status === 422)) {
      localStorage.removeItem(tokenKey)
      window.dispatchEvent(new CustomEvent('auth-expired', { detail: tokenKey }))
    }
    throw new ApiError(data?.message || data?.msg || `Request failed (${response.status})`, response.status)
  }
  return data
}

export function createApi(tokenKey) {
  return {
    get: (path, params) => json(tokenKey, 'GET', path, { params }),
    post: (path, body = {}) => json(tokenKey, 'POST', path, { body }),
    put: (path, body = {}) => json(tokenKey, 'PUT', path, { body }),
    del: (path) => json(tokenKey, 'DELETE', path),
    // Authenticated file download (an <a href> cannot send the Authorization header).
    async download(path, filename) {
      const { response } = await request(tokenKey, 'GET', path)
      if (!response.ok) {
        let message = `Download failed (${response.status})`
        try { message = (await response.json()).message || message } catch { /* not json */ }
        throw new ApiError(message, response.status)
      }
      const blobUrl = URL.createObjectURL(await response.blob())
      const link = document.createElement('a')
      link.href = blobUrl
      link.download = filename
      link.click()
      URL.revokeObjectURL(blobUrl)
    }
  }
}

export const publicApi = createApi(null)
export const adminApi = createApi('admin-token')
export const examinerApi = createApi('examiner-token')
export const studentApi = createApi('student-token')
export const apis = { admin: adminApi, examiner: examinerApi, student: studentApi }
