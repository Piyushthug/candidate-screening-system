import { useState, useEffect } from 'react'
import { screeningAPI } from '../services/api'
import CandidateModal from './CandidateModal'
import './ResultsSummary.css'

export default function ResultsSummary({ job, screenings: initialScreenings, onBack }) {
  const [screenings, setScreenings] = useState(initialScreenings)
  const [selectedScreening, setSelectedScreening] = useState(null)
  const [sendingEmails, setSendingEmails] = useState({})
  const [emailsSent, setEmailsSent] = useState({})
  const [error, setError] = useState(null)

  // Load full screening details for all screenings
  useEffect(() => {
    loadAllScreenings()
  }, [])

  const loadAllScreenings = async () => {
    try {
      const detailedScreenings = []
      for (const screening of initialScreenings) {
        try {
          if (!screening.fit_score) {
            // Start workflow if not already run
            await screeningAPI.startWorkflow(screening.id)
          }
          const { data } = await screeningAPI.getScreeningDetail(screening.id)
          if (data?.screening) {
            detailedScreenings.push(data.screening)
          } else {
            detailedScreenings.push(screening)
          }
        } catch (e) {
          console.warn(`Could not load full details for screening ${screening.id}:`, e)
          detailedScreenings.push(screening)
        }
      }
      setScreenings(detailedScreenings)
    } catch (err) {
      console.error('Error loading screening details:', err)
    }
  }

  const approved = screenings.filter(s => s.approval_status === 'approved')
  const rejected = screenings.filter(s => s.approval_status === 'rejected')
  const pending = screenings.filter(s => s.approval_status === 'pending')

  const averageFitScore = approved.length > 0
    ? (approved.reduce((sum, s) => sum + (s.fit_score || 0), 0) / approved.length).toFixed(1)
    : 0

  const handleModalClose = () => {
    setSelectedScreening(null)
  }

  const handleDecision = (screeningId, decision) => {
    // Update the screening in state
    setScreenings(prev => prev.map(s =>
      s.id === screeningId ? { ...s, approval_status: decision } : s
    ))
    setSelectedScreening(null)
  }

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
      {selectedScreening && (
        <CandidateModal
          screening={selectedScreening}
          onClose={handleModalClose}
          onDecision={handleDecision}
        />
      )}

      <div className="card">
        <div className="flex-between mb-20">
          <div>
            <h2>Review Candidates</h2>
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
            <div className="stat-label">Total to Review</div>
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
            <div className="stat-number">{pending.length}</div>
            <div className="stat-label">Pending</div>
          </div>
        </div>

        {/* All Candidates List - Clickable */}
        <div className="results-section mt-30">
          <h3>Click a candidate to review and decide</h3>

          <div className="results-list">
            {screenings.map(screening => {
              const candidate = screening.candidate || {}
              const status = screening.approval_status

              return (
                <div
                  key={screening.id}
                  className={`result-card clickable ${status}`}
                  onClick={() => setSelectedScreening(screening)}
                >
                  <div className="result-header">
                    <div>
                      <h4>{candidate.name || 'Candidate'}</h4>
                      <p className="text-muted">{candidate.email || 'No email'}</p>
                    </div>
                    <div className="result-score">
                      <span className={`badge ${status === 'pending' ? 'neutral' : status}`}>
                        {status === 'approved' && '✓ Approved'}
                        {status === 'rejected' && '✗ Rejected'}
                        {status === 'pending' && `${Math.round(screening.fit_score || 0)}%`}
                      </span>
                    </div>
                  </div>

                  <div className="result-body">
                    <p><strong>Skills:</strong> {candidate.parsed_skills?.slice(0, 3).join(', ') || 'Not specified'}</p>
                    <p><strong>Experience:</strong> {candidate.experience_years || 'N/A'} years</p>
                  </div>

                  {status === 'pending' && (
                    <div className="result-actions">
                      <p className="text-muted small">Click to review and decide</p>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* Send Approved Emails Section */}
        {approved.length > 0 && (
          <div className="results-section mt-30">
            <h3>Send Approval Emails</h3>
            <p className="text-muted">Send personalized messages to approved candidates</p>

            <div className="results-list">
              {approved.map(screening => {
                const candidate = screening.candidate || {}
                return (
                  <div key={screening.id} className="result-card approved">
                    <div className="result-header">
                      <div>
                        <h4>{candidate.name || 'Candidate'}</h4>
                        <p className="text-muted">{candidate.email || 'No email'}</p>
                      </div>
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
                )
              })}
            </div>

            <div className="mt-15">
              <button
                className="success large"
                onClick={handleSendAllEmails}
                disabled={Object.values(sendingEmails).some(v => v) || approved.length === 0}
              >
                Send All Emails ({approved.length})
              </button>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="results-footer mt-30">
          <button className="primary" onClick={onBack}>← Back to Jobs</button>
        </div>
      </div>
    </div>
  )
}
