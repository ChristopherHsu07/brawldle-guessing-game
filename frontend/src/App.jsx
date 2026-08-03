import { useEffect, useState } from 'react'
import { startOrResumeGame, submitGuess } from './api.js'
import './App.css'

const COLUMN_HEADERS = [
  { key: 'brawler number', label: 'Brawler Number' },
  { key: 'Role', label: 'Role' },
  { key: 'Rarity', label: 'Rarity' },
  { key: 'Attack Range', label: 'Attack Range' },
  { key: 'Gender', label: 'Gender' },
  { key: 'Attacks per Ammo', label: 'Attacks per Ammo' },
  { key: 'Super Type', label: 'Super Type' },
]

function displayValue(value, status) {
  const text = String(value)
  if (status === 'higher') return `${text} ↑`
  if (status === 'lower') return `${text} ↓`
  return text
}

export default function App() {
  const [history, setHistory] = useState([])
  const [status, setStatus] = useState('in_progress')
  const [guessCount, setGuessCount] = useState(0)
  const [answerName, setAnswerName] = useState(null)
  const [guess, setGuess] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const data = await startOrResumeGame()
        if (cancelled) return
        setHistory(data.state.history ?? [])
        setStatus(data.state.status)
        setGuessCount(data.state.guess_count)
        setAnswerName(data.state.answer_name)
        setError('')
      } catch (err) {
        if (!cancelled) {
          setError(err.message || 'Failed to start game')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  async function onSubmit(event) {
    event.preventDefault()
    const trimmed = guess.trim()
    if (!trimmed || status === 'won' || submitting) return

    setSubmitting(true)
    setError('')
    try {
      const data = await submitGuess(trimmed)
      setHistory((prev) => [...prev, data.result])
      setStatus(data.status)
      setGuessCount(data.guess_count)
      setAnswerName(data.answer_name)
      setGuess('')
    } catch (err) {
      setError(err.message || 'Guess failed')
    } finally {
      setSubmitting(false)
    }
  }

  const won = status === 'won'
  const guessesWord = guessCount === 1 ? 'guess' : 'guesses'

  return (
    <div className="app">
      <div className="main-container">
        <div className="wrapper-pattern">
          <div className="top-bar" />
          <div className="game-content">
            <h1 className="title">Brawldle</h1>
            <p className="subtitle">Guess the brawler by their stats</p>

            <form className="guess-form" onSubmit={onSubmit}>
              <input
                type="text"
                value={guess}
                onChange={(e) => setGuess(e.target.value)}
                placeholder="Guess a brawler"
                disabled={loading || won || submitting}
                autoComplete="off"
              />
              <button
                type="submit"
                className="button"
                disabled={loading || won || submitting || !guess.trim()}
              >
                <span className="button-label">Guess</span>
              </button>
            </form>

            {error ? <p className="message error">{error}</p> : null}
            {won ? (
              <p className="message win">
                You got it! {answerName} in {guessCount} {guessesWord}.
              </p>
            ) : null}

            {history.length > 0 ? (
              <div className="table-wrap">
                <table className="guess-table">
                  <thead>
                    <tr>
                      <th>Guess</th>
                      {COLUMN_HEADERS.map((col) => (
                        <th key={col.key}>{col.label}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((row, index) => (
                      <tr key={`${row.guess_name}-${index}`}>
                        <td className="guess-name">{row.guess_name}</td>
                        {row.attributes.map((attr) => (
                          <td
                            key={attr.column}
                            className={`cell status-${attr.status}`}
                          >
                            {displayValue(attr.value, attr.status)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  )
}
