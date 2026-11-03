import { useState } from 'react'
import { screeningAPI } from '../services/api'
import './ResultsSummary.css'

export default function ResultsSummary({ job, screenings, onBack }) {
  const [sendingEmails, setSendingEmails] = useState({})
  const [emailsSent, setEmailsSent] = useState({})
  const [error, setError] = useState(null)

  const approved = screenings.filter(s => s.approval_status === 'approved')
  const rejected = screenings.filter(s => s.approval_status === 'rejected')
  const pending = screenings.filter(s => s.approval_status === 'pending')

  const averageFitScore = approved.length > 0
    ? (approved.reduce((sum, s) => sum + (s.fit_score || 0), 0) / approved.length).toFixed(1)
    : 0

  const handleSendEmail = async (screeningId) => {
    try {
      setSendingEmails(prev => ({ ...prev, [screeningId]: true }))
      const result = await screeningAPI.sendApprovalEmail(screeningId)
      setEmailsSent(prev => ({ ...prev, [screeningId]: true }))
      setError(null)
    } catch (err) {
      setError('Failed to send email: ' + (err.message || 'Unknown error'))
      console.error(err)
    } finally {
      setSendingEmails(prev => ({ ...prev, [screeningId]: false }))
    }
  }

  const handleSendAllEmails = async () => {
    try {
      setSendingEmails(Object.fromEntries(approved.map(s => [s.id, true])))
      for (const screening of approved) {
        if (!emailsSent[screening.id]) {
          await screeningAPI.sendApprovalEmail(screening.id)
          setEmailsSent(prev => ({ ...prev, [screening.id]: true }))
        }
      }
      setError(null)
    } catch (err) {
      setError('Failed to send some emails: ' + (err.message || 'Unknown error'))
      console.error(err)
    } finally {
      setSendingEmails({})
    }
  }

  return (
    <div className="results-summary">
      <div className="card">
        <div className="flex-between mb-20">
          <div>
            <h2>Screening Results</h2>
            <p className="text-muted">Job: <strong>{job.title}</strong></p>
          </div>
          <button className="primary" onClick={onBack}>Back to Jobs</button>
        </div>

        {error && (
          <div className="error-banner mb-20">
            {error}
            <button onClick={() => setError(null)}>×</button>
          </div>
        )}

        {/* Statistics */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-number">{screenings.length}</div>
            <div className="stat-label">Total Screened</div>
          </div>
          <div className="stat-card success">
            <div className="stat-number">{approved.length}</div>
            <div className="stat-label">Approved</div>
          </div>
          <div className="stat-card danger">
            <div className="stat-number">{rejected.length}</div>
            <div className="stat-label">Rejected</div>
          </div>
          <div className="stat-card warning">
            <div className="stat-number">{averageFitScore}%</div>
            <div className="stat-label">Avg Fit Score</div>
          </div>
        </div>

        {/* Approved Candidates */}
        {approved.length > 0 && (
          <div className="results-section mt-30">
            <div className="flex-between mb-15">
              <h3>✓ Approved ({approved.length})</h3>
              <button
                className="success"
                onClick={handleSendAllEmails}
                disabled={Object.values(sendingEmails).some(v => v)}
              >
                Send All Emails
              </button>
            </div>

            <div className="results-list">
              {approved.map(screening => (
                <div key={screening.id} className="result-card approved">
                  <div className="result-header">
                    <div>
                      <h4>{screening.candidate.name}</h4>
                      <p className="text-muted">{screening.candidate.email}</p>
                    </div>
                    <div className="result-score">
                      <span className="badge success">{Math.round(screening.fit_score)}%</span>
                    </div>
                  </div>

                  <div className="result-body">
                    <p><strong>Skills:</strong> {screening.candidate.parsed_skills?.join(', ') || 'Not specified'}</p>
                    <p><strong>Experience:</strong> {screening.candidate.experience_years || 'N/A'} years</p>
                  </div>

                  <div className="result-actions">
                    <button
                      className="success"
                      onClick={() => handleSendEmail(screening.id)}
                      disabled={sendingEmails[screening.id]}
                    >
                      {emailsSent[screening.id] ? '✓ Email Sent' : 'Send Email'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Rejected Candidates */}
        {rejected.length > 0 && (
          <div className="results-section mt-30">
            <h3>✗ Rejected ({rejected.length})</h3>

            <div className="results-list">
              {rejected.map(screening => (
                <div key={screening.id} className="result-card rejected">
                  <div className="result-header">
                    <div>
                      <h4>{screening.candidate.name}</h4>
                      <p className="text-muted">{screening.candidate.email}</p>
                    </div>
                    <div className="result-score">
                      <span className="badge danger">{Math.round(screening.fit_score || 0)}%</span>
                    </div>
                  </div>

                  <div className="result-body">
                    <p><strong>Skills:</strong> {screening.candidate.parsed_skills?.join(', ') || 'Not specified'}</p>
                    <p><strong>Experience:</strong> {screening.candidate.experience_years || 'N/A'} years</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Pending */}
        {pending.length > 0 && (
          <div className="results-section mt-30">
            <h3>⏳ Pending ({pending.length})</h3>
            <p className="text-muted">These candidates still need to be reviewed.</p>
          </div>
        )}

        {/* Export */}
        <div className="results-footer mt-30">
          <button className="primary" onClick={onBack}>← Back to Jobs</button>
        </div>
      </div>
    </div>
  )
}
