import { useEffect, useEffectEvent, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { newGame, startOrResumeGame, submitGuess } from './api.js'
import { getPinUrl } from './pins.js'
import './App.css'

const SUPER_CATEGORIES = [
  'Buff',
  'CC',
  'Damage',
  'Debuff',
  'DOT',
  'Heal',
  'Mobility',
  'Summon',
  'Transform',
]

const STATIC_HEADER_TOOLTIPS = {
  'Attacks per Ammo':
    'The number of bullets the brawler shoots per ammo (e.g. Colt: 6, Piper: 1)',
  'Super Type': `Super categories include ${SUPER_CATEGORIES.slice(0, -1).join(', ')}, and ${SUPER_CATEGORIES.at(-1)}`,
}

const COLUMN_HEADERS = [
  { key: 'brawler number', label: 'Brawler Number' },
  { key: 'Role', label: 'Role' },
  { key: 'Rarity', label: 'Rarity' },
  { key: 'Attack Range', label: 'Attack Range' },
  { key: 'Gender', label: 'Gender' },
  { key: 'Attacks per Ammo', label: 'Attacks per Ammo' },
  { key: 'Super Type', label: 'Super Type' },
]

function ordinal(n) {
  const mod100 = n % 100
  if (mod100 >= 11 && mod100 <= 13) return `${n}th`
  switch (n % 10) {
    case 1:
      return `${n}st`
    case 2:
      return `${n}nd`
    case 3:
      return `${n}rd`
    default:
      return `${n}th`
  }
}

function brawlerNumberTooltip(guessName, value, status) {
  const text = String(value).trim()
  const rankPart =
    text === 'Original 15'
      ? `${guessName} is one of the original 15 brawlers to be released`
      : `${guessName} is the ${ordinal(Number(text))} brawler to be released`

  if (status === 'higher') return `${rankPart} Guess a newer brawler`
  if (status === 'lower') return `${rankPart} Guess an older brawler`
  return `${rankPart}.`
}

function displayValue(value, status) {
  const text = String(value)
  if (status === 'higher') return `${text} ↑`
  if (status === 'lower') return `${text} ↓`
  return text
}

function AttributeContent({ attr }) {
  if (attr.column === 'Super Type' && Array.isArray(attr.tags) && attr.tags.length > 0) {
    return (
      <div className="super-tags">
        {attr.tags.map((tag) => (
          <span
            key={tag.value}
            className={`super-tag status-${tag.status}`}
            title={tag.value}
          >
            {tag.value}
          </span>
        ))}
      </div>
    )
  }
  return displayValue(attr.value, attr.status)
}

function HeaderTooltip({ label, tip }) {
  const triggerRef = useRef(null)
  const tipRef = useRef(null)
  const [open, setOpen] = useState(false)
  const [coords, setCoords] = useState(null)

  const placeTooltip = useEffectEvent(() => {
    const trigger = triggerRef.current
    const tipEl = tipRef.current
    if (!trigger || !tipEl) return

    const rect = trigger.getBoundingClientRect()
    const tipRect = tipEl.getBoundingClientRect()
    const gap = 8
    const pad = 8

    let top = rect.bottom + gap
    if (top + tipRect.height > window.innerHeight - pad) {
      top = rect.top - tipRect.height - gap
    }
    top = Math.max(pad, Math.min(top, window.innerHeight - tipRect.height - pad))

    let left = rect.left + rect.width / 2 - tipRect.width / 2
    left = Math.max(pad, Math.min(left, window.innerWidth - tipRect.width - pad))

    setCoords({ top, left })
  })

  useLayoutEffect(() => {
    if (!open) {
      setCoords(null)
      return
    }
    placeTooltip()
    const onReposition = () => placeTooltip()
    window.addEventListener('scroll', onReposition, true)
    window.addEventListener('resize', onReposition)
    return () => {
      window.removeEventListener('scroll', onReposition, true)
      window.removeEventListener('resize', onReposition)
    }
  }, [open, tip])

  if (!tip) return label

  return (
    <>
      <span
        ref={triggerRef}
        className="header-tip"
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        tabIndex={0}
      >
        {label}
      </span>
      {open
        ? createPortal(
            <div
              ref={tipRef}
              className={coords ? 'tooltip-overlay' : 'tooltip-overlay tooltip-overlay-measure'}
              style={coords ? { top: coords.top, left: coords.left } : undefined}
              role="tooltip"
            >
              {tip}
            </div>,
            document.body,
          )
        : null}
    </>
  )
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

const PORTRAIT_MOBILE_QUERY = '(max-width: 900px) and (orientation: portrait)'

function useIsPortraitMobile() {
  const [matches, setMatches] = useState(() =>
    typeof window !== 'undefined'
      ? window.matchMedia(PORTRAIT_MOBILE_QUERY).matches
      : false,
  )

  useEffect(() => {
    const mql = window.matchMedia(PORTRAIT_MOBILE_QUERY)
    const onChange = () => setMatches(mql.matches)
    onChange()
    mql.addEventListener('change', onChange)
    return () => mql.removeEventListener('change', onChange)
  }, [])

  return matches
}

export default function App() {
  const showRotatePrompt = useIsPortraitMobile()
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

  async function onPlayAgain() {
    if (submitting || isFlipping) return
    setSubmitting(true)
    setError('')
    try {
      const data = await newGame()
      setHistory(data.state.history ?? [])
      setStatus(data.state.status)
      setGuessCount(data.state.guess_count)
      setAnswerName(data.state.answer_name)
      setGuess('')
      setFlippingRow(null)
      setMenuOpen(false)
    } catch (err) {
      setError(err.message || 'Failed to start a new game')
    } finally {
      setSubmitting(false)
    }
  }

  const guessesWord = guessCount === 1 ? 'guess' : 'guesses'

  const headerTooltips = useMemo(() => {
    const tips = { ...STATIC_HEADER_TOOLTIPS }
    const first = history[0]
    if (!first) return tips
    const attr = first.attributes?.find((a) => a.column === 'brawler number')
    if (!attr) return tips
    tips['brawler number'] = brawlerNumberTooltip(
      first.guess_name,
      attr.value,
      attr.status,
    )
    return tips
  }, [history])

  return (
    <div className="app">
      {showRotatePrompt ? (
        <div className="rotate-prompt" role="dialog" aria-modal="true" aria-live="polite">
          <div className="rotate-prompt-card">
            <div className="rotate-phone" aria-hidden="true">
              <div className="rotate-phone-body" />
              <div className="rotate-arrow" />
            </div>
            <p>Please turn your phone sideways to play</p>
          </div>
        </div>
      ) : null}
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
            <div className="win-row">
              <p className="message win">
                You got it! {answerName} in {guessCount} {guessesWord}.
              </p>
              <button
                type="button"
                className="button play-again"
                onClick={onPlayAgain}
                disabled={submitting}
              >
                <span className="button-label">Play again</span>
              </button>
            </div>
          ) : null}

          {history.length > 0 ? (
            <div className="table-wrap">
              <table className="guess-table">
                <thead>
                  <tr>
                    <th>Guess</th>
                    {COLUMN_HEADERS.map((col) => (
                      <th key={col.key}>
                        <HeaderTooltip
                          label={col.label}
                          tip={headerTooltips[col.key]}
                        />
                      </th>
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
                              <div className="cell-content">
                                <AttributeContent attr={attr} />
                              </div>
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

          <div className="color-legend" aria-label="Color meanings">
            <div className="legend-item">
              <span className="legend-swatch legend-correct" aria-hidden="true" />
              <span>Correct</span>
            </div>
            <div className="legend-item">
              <span className="legend-swatch legend-partial" aria-hidden="true" />
              <span>Partial</span>
            </div>
            <div className="legend-item">
              <span className="legend-swatch legend-miss" aria-hidden="true" />
              <span>Incorrect</span>
            </div>
          </div>
        </div>

        <p className="made-by">
          <span>Made by</span>
          <a
            className="made-by-link"
            href="https://github.com/ChristopherHsu07"
            target="_blank"
            rel="noopener noreferrer"
          >
            @ChristopherHsu07
          </a>
        </p>
      </div>
    </div>
  )
}
