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

export async function startOrResumeGame() {
  const response = await fetch('/api/', { credentials: 'include' })
  if (!response.ok) {
    throw new Error(await parseError(response))
  }
  return response.json()
}

export async function newGame() {
  const response = await fetch('/api/new', {
    method: 'POST',
    credentials: 'include',
  })
  if (!response.ok) {
    throw new Error(await parseError(response))
  }
  return response.json()
}

export async function submitGuess(guess) {
  const response = await fetch('/api/guess', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ guess }),
  })
  if (!response.ok) {
    throw new Error(await parseError(response))
  }
  return response.json()
}
