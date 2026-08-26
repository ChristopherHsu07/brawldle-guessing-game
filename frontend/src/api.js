const API_BASE = '/api'
const FETCH_TIMEOUT_MS = import.meta.env.PROD ? 60_000 : 30_000
const LOCAL_API_HINT = "Can't reach the local API (is uvicorn running?)"
const TIMEOUT_HINT = 'Server did not respond in time'

async function parseError(response) {
  try {
    const data = await response.json()
    const detail = data.detail
    if (typeof detail === 'string') return detail
    if (detail && typeof detail === 'object') {
      let message = detail.message || 'Request failed'
      if (detail.suggestion) {
        message += ` Did you mean ${detail.suggestion}?`
      }
      return message
    }
    return 'Request failed'
  } catch {
    return `Request failed (${response.status})`
  }
}

async function apiFetch(path, options = {}) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS)
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      credentials: 'include',
      ...options,
      signal: controller.signal,
    })
    if (!response.ok) {
      throw new Error(await parseError(response))
    }
    return response.json()
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new Error(TIMEOUT_HINT)
    }
    if (err instanceof TypeError && !import.meta.env.PROD) {
      throw new Error(LOCAL_API_HINT)
    }
    throw err
  } finally {
    clearTimeout(timer)
  }
}

export async function startOrResumeGame() {
  return apiFetch('/')
}

export async function newGame() {
  return apiFetch('/new', { method: 'POST' })
}

export async function submitGuess(guess) {
  return apiFetch('/guess', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ guess }),
  })
}
