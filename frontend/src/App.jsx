import { useEffect, useMemo, useRef, useState } from 'react'
import { startOrResumeGame, submitGuess } from './api.js'
import { getPinUrl } from './pins.js'
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

function BrawlerPin({ name, className }) {
  const src = getPinUrl(name)
  if (!src) return null
  return (
    <img
      className={className}
      src={src}
      alt=""
      onError={(event) => {
        event.currentTarget.style.visibility = 'hidden'
      }}
    />
  )
}

export default function App() {
  const [history, setHistory] = useState([])
  const [status, setStatus] = useState('in_progress')
  const [guessCount, setGuessCount] = useState(0)
  const [answerName, setAnswerName] = useState(null)
  const [brawlerNames, setBrawlerNames] = useState([])
  const [guess, setGuess] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const [highlightIndex, setHighlightIndex] = useState(0)
  const [flippingRow, setFlippingRow] = useState(null)
  const inputRef = useRef(null)
  const listRef = useRef(null)
  const blurTimeoutRef = useRef(null)
  const FLIP_STAGGER_MS = 320
  const FLIP_DURATION_MS = 500

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
        setBrawlerNames(data.brawler_names ?? [])
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
      if (blurTimeoutRef.current) clearTimeout(blurTimeoutRef.current)
    }
  }, [])

  const suggestions = useMemo(() => {
    const query = guess.trim().toLowerCase()
    if (!query) return brawlerNames
    return brawlerNames.filter((name) => name.toLowerCase().startsWith(query))
  }, [brawlerNames, guess])

  const won = status === 'won'
  const isFlipping = flippingRow !== null
  const showSuggestions =
    menuOpen && !won && !loading && !submitting && !isFlipping && suggestions.length > 0

  useEffect(() => {
    setHighlightIndex(0)
  }, [guess, menuOpen])

  useEffect(() => {
    if (!showSuggestions || !listRef.current) return
    const active = listRef.current.querySelector('.suggestion.active')
    active?.scrollIntoView({ block: 'nearest' })
  }, [highlightIndex, showSuggestions])

  useEffect(() => {
    if (flippingRow === null) return
    const attrCount = history[flippingRow]?.attributes?.length ?? COLUMN_HEADERS.length
    const totalMs = (attrCount - 1) * FLIP_STAGGER_MS + FLIP_DURATION_MS + 50
    const timer = setTimeout(() => setFlippingRow(null), totalMs)
    return () => clearTimeout(timer)
  }, [flippingRow, history])

  function selectSuggestion(name) {
    setGuess(name)
    setMenuOpen(false)
    setHighlightIndex(0)
    inputRef.current?.focus()
  }

  function onInputChange(event) {
    setGuess(event.target.value)
    setMenuOpen(true)
  }

  function onInputFocus() {
    if (blurTimeoutRef.current) clearTimeout(blurTimeoutRef.current)
    if (!won && !loading && !isFlipping) setMenuOpen(true)
  }

  function onInputBlur() {
    blurTimeoutRef.current = setTimeout(() => setMenuOpen(false), 150)
  }

  function onInputKeyDown(event) {
    if (!showSuggestions) {
      if (event.key === 'Escape') setMenuOpen(false)
      return
    }

    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setHighlightIndex((i) => Math.min(i + 1, suggestions.length - 1))
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setHighlightIndex((i) => Math.max(i - 1, 0))
    } else if (event.key === 'Enter' && menuOpen) {
      const selected = suggestions[highlightIndex]
      if (selected && guess.trim().toLowerCase() !== selected.toLowerCase()) {
        event.preventDefault()
        selectSuggestion(selected)
      }
    } else if (event.key === 'Escape') {
      event.preventDefault()
      setMenuOpen(false)
    }
  }

  async function onSubmit(event) {
    event.preventDefault()
    const trimmed = guess.trim()
    if (!trimmed || status === 'won' || submitting || isFlipping) return

    setSubmitting(true)
    setMenuOpen(false)
    setError('')
    try {
      const data = await submitGuess(trimmed)
      setHistory((prev) => {
        const next = [...prev, data.result]
        setFlippingRow(next.length - 1)
        return next
      })
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

  const guessesWord = guessCount === 1 ? 'guess' : 'guesses'

  return (
    <div className="app">
      <div className="main-container">
        <div className="game-content">
          <h1 className="title">Brawldle</h1>
          <p className="subtitle">Guess the brawler by their stats</p>

          <form className="guess-form" onSubmit={onSubmit}>
            <div className="guess-input-wrap">
              <input
                ref={inputRef}
                type="text"
                value={guess}
                onChange={onInputChange}
                onFocus={onInputFocus}
                onBlur={onInputBlur}
                onKeyDown={onInputKeyDown}
                placeholder="Guess a brawler"
                disabled={loading || won || submitting || isFlipping}
                autoComplete="off"
                role="combobox"
                aria-expanded={showSuggestions}
                aria-controls="brawler-suggestions"
                aria-autocomplete="list"
              />
              {showSuggestions ? (
                <ul
                  id="brawler-suggestions"
                  ref={listRef}
                  className="suggestions"
                  role="listbox"
                >
                  {suggestions.map((name, index) => (
                    <li key={name} role="option" aria-selected={index === highlightIndex}>
                      <button
                        type="button"
                        className={
                          index === highlightIndex
                            ? 'suggestion active'
                            : 'suggestion'
                        }
                        onMouseDown={(event) => event.preventDefault()}
                        onClick={() => selectSuggestion(name)}
                        onMouseEnter={() => setHighlightIndex(index)}
                      >
                        <BrawlerPin name={name} className="brawler-pin pin-sm" />
                        <span>{name}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
            <button
              type="submit"
              className="button"
              disabled={loading || won || submitting || isFlipping || !guess.trim()}
            >
              <span className="button-label">Guess</span>
            </button>
          </form>

          {error ? <p className="message error">{error}</p> : null}
          {won && !isFlipping ? (
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
                  {history.map((row, index) => {
                    const rowFlipping = flippingRow === index
                    return (
                      <tr key={`${row.guess_name}-${index}`}>
                        <td className="guess-name">
                          <div className="guess-cell">
                            <BrawlerPin
                              name={row.guess_name}
                              className="brawler-pin pin-lg"
                            />
                            <span>{row.guess_name}</span>
                          </div>
                        </td>
                        {row.attributes.map((attr, attrIndex) => (
                          <td key={attr.column} className="cell-slot">
                            <div
                              className={
                                rowFlipping
                                  ? `cell-face status-${attr.status} flip`
                                  : `cell-face status-${attr.status}`
                              }
                              style={
                                rowFlipping
                                  ? {
                                      '--flip-delay': `${attrIndex * (FLIP_STAGGER_MS / 1000)}s`,
                                    }
                                  : undefined
                              }
                            >
                              {displayValue(attr.value, attr.status)}
                            </div>
                          </td>
                        ))}
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}
