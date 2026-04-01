import { useState } from 'react'
import PatientForm from './components/PatientForm.jsx'
import ResultsDashboard from './components/ResultsDashboard.jsx'
import Header from './components/Header.jsx'

export default function App() {
  const [results, setResults]           = useState(null)
  const [loading, setLoading]           = useState(false)
  const [error, setError]               = useState(null)
  const [inputErrors, setInputErrors]   = useState([])   // guardrail blocks
  const [outputWarnings, setOutputWarnings] = useState([]) // guardrail soft flags

  const handleSubmit = async (formData, files) => {
    setLoading(true)
    setError(null)
    setResults(null)
    setInputErrors([])
    setOutputWarnings([])

    try {
      let response
      if (files && files.length > 0) {
        const fd = new FormData()
        fd.append('patient_json', JSON.stringify(formData))
        files.forEach(f => fd.append('files', f))
        response = await fetch('/api/diagnose/upload', { method: 'POST', body: fd })
      } else {
        response = await fetch('/api/diagnose', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData),
        })
      }

      const json = await response.json()

      if (!response.ok) {
        throw new Error(json.detail || 'Server error')
      }

      // ── Input guardrail blocked ──────────────────────────────────────────
      if (json.blocked) {
        setInputErrors(json.input_errors || ['Input validation failed'])
        return
      }

      // ── Success — check for output warnings ──────────────────────────────
      if (json.data?.output_warnings?.length > 0) {
        setOutputWarnings(json.data.output_warnings)
      }

      setResults(json.data)

    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setResults(null)
    setError(null)
    setInputErrors([])
    setOutputWarnings([])
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>
      <Header showBack={!!results || !!error || inputErrors.length > 0} onBack={handleReset} />
      <main style={{ maxWidth: 1100, margin: '0 auto', padding: '0 24px 80px' }}>

        {!results && !loading && (
          <>
            {/* ── Input Guardrail Error Banner ────────────────────────── */}
            {inputErrors.length > 0 && (
              <div style={{
                marginTop: 32,
                background: '#f43f5e10',
                border: '1px solid #f43f5e50',
                borderRadius: 12,
                padding: '20px 24px',
              }}>
                <div style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  marginBottom: 14,
                }}>
                  <div style={{
                    width: 36, height: 36, borderRadius: 8,
                    background: '#f43f5e20', border: '1px solid #f43f5e40',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 18,
                  }}>🛡️</div>
                  <div>
                    <div style={{ fontWeight: 700, color: '#f43f5e', fontSize: '0.95rem' }}>
                      Input Guardrail — Submission Blocked
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#4a6080' }}>
                      Please fix the following issues before resubmitting
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {inputErrors.map((err, i) => (
                    <div key={i} style={{
                      display: 'flex', alignItems: 'flex-start', gap: 10,
                      background: '#f43f5e08', borderRadius: 8,
                      padding: '10px 14px', border: '1px solid #f43f5e25',
                      fontSize: '0.85rem', color: '#f43f5e',
                    }}>
                      <span>✗</span> {err}
                    </div>
                  ))}
                </div>
                <button
                  onClick={handleReset}
                  style={{
                    marginTop: 16, padding: '9px 20px',
                    background: '#f43f5e20', border: '1px solid #f43f5e50',
                    borderRadius: 8, color: '#f43f5e', cursor: 'pointer',
                    fontFamily: 'var(--font-body)', fontWeight: 600, fontSize: '0.85rem',
                  }}
                >
                  ← Fix &amp; Retry
                </button>
              </div>
            )}

            <PatientForm onSubmit={handleSubmit} error={error} />
          </>
        )}

        {loading && <LoadingScreen />}

        {results && !loading && (
          <ResultsDashboard
            results={results}
            outputWarnings={outputWarnings}
            onReset={handleReset}
          />
        )}

      </main>
    </div>
  )
}

function LoadingScreen() {
  const stages = [
    { icon: '🛡️', label: 'Input Guardrail',        color: 'var(--teal)',   delay: '0s',   note: 'Validating patient data…' },
    { icon: '🔬', label: 'Diagnosis Agent',          color: 'var(--teal)',   delay: '0.5s', note: 'Analysing symptoms…' },
    { icon: '🧪', label: 'Lab Analysis Agent',       color: 'var(--blue)',   delay: '1.0s', note: 'Recommending tests…' },
    { icon: '⚠️', label: 'Risk Evaluation Agent',    color: 'var(--amber)',  delay: '1.5s', note: 'Checking risk factors…' },
    { icon: '💊', label: 'Treatment Agent',          color: 'var(--violet)', delay: '2.0s', note: 'Building treatment plan…' },
    { icon: '🛡️', label: 'Output Guardrail',        color: 'var(--teal)',   delay: '2.5s', note: 'Validating outputs…' },
  ]
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '70vh', gap: 40 }}>
      <div style={{ position: 'relative', width: 72, height: 72 }}>
        <div style={{ width: 72, height: 72, borderRadius: '50%', border: '3px solid var(--border)', borderTop: '3px solid var(--teal)', animation: 'spin 1s linear infinite' }} />
        <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 26 }}>🏥</div>
      </div>
      <div style={{ textAlign: 'center' }}>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.8rem', marginBottom: 6 }}>Analysing Patient Data</h2>
        <p style={{ color: 'var(--text-muted)' }}>Guardrails active · 4 AI agents running via Groq…</p>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, width: '100%', maxWidth: 440 }}>
        {stages.map((s, i) => (
          <div key={i} className="animate-in" style={{
            animationDelay: s.delay,
            display: 'flex', alignItems: 'center', gap: 12,
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            borderRadius: 'var(--radius)', padding: '11px 16px',
          }}>
            <span style={{ fontSize: 17 }}>{s.icon}</span>
            <div style={{ flex: 1 }}>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', fontWeight: 500 }}>{s.label}</div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.73rem' }}>{s.note}</div>
            </div>
            <div style={{
              width: 64, height: 4, borderRadius: 2,
              background: `linear-gradient(90deg, var(--border) 25%, ${s.color}60 50%, var(--border) 75%)`,
              backgroundSize: '200% 100%',
              animation: 'shimmer 1.5s infinite',
              animationDelay: s.delay,
            }} />
          </div>
        ))}
      </div>
    </div>
  )
}