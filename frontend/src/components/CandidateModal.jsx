import { useState } from 'react'
import { screeningAPI } from '../services/api'
import './CandidateModal.css'

export default function CandidateModal({ screening, onClose, onDecision }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const candidate = screening?.candidate || {}

  const handleApprove = async () => {
    try {
      setLoading(true)
      await screeningAPI.approve(screening.id, 'Approved by recruiter')
      onDecision(screening.id, 'approved')
      onClose()
      setError(null)
    } catch (err) {
      setError('Failed to approve: ' + (err.message || 'Unknown error'))
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleReject = async () => {
    try {
      setLoading(true)
      await screeningAPI.reject(screening.id, 'Rejected by recruiter')
      onDecision(screening.id, 'rejected')
      onClose()
      setError(null)
    } catch (err) {
      setError('Failed to reject: ' + (err.message || 'Unknown error'))
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (!screening) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{candidate.name || 'Candidate'}</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        {error && (
          <div className="error-banner">
            {error}
            <button onClick={() => setError(null)}>×</button>
          </div>
        )}

        <div className="modal-body">
          {/* Candidate Info */}
          <div className="section">
            <h3>Candidate Information</h3>
            <div className="info-grid">
              <div className="info-item">
                <strong>Email:</strong>
                <p>{candidate.email || 'No email'}</p>
              </div>
              <div className="info-item">
                <strong>Experience:</strong>
                <p>{candidate.experience_years || 'N/A'} years</p>
              </div>
              <div className="info-item">
                <strong>Skills:</strong>
                <p>{candidate.parsed_skills?.join(', ') || 'Not specified'}</p>
              </div>
            </div>
          </div>

          {/* Fit Score */}
          <div className="section">
            <h3>Fit Analysis</h3>
            <div className="fit-info">
              <div className="score-circle">{Math.round(screening.fit_score || 0)}%</div>
              <p>{screening.fit_reasoning || 'Analyzing fit...'}</p>
            </div>
          </div>

          {/* Email Draft */}
          <div className="section">
            <h3>Email Draft</h3>
            <div className="email-draft">
              {screening.generated_message || 'Generating message...'}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="modal-footer">
          <button
            className="danger"
            onClick={handleReject}
            disabled={loading || screening.approval_status !== 'pending'}
          >
            {screening.approval_status === 'rejected' ? '✓ Rejected' : 'Reject'}
          </button>
          <button
            className="success"
            onClick={handleApprove}
            disabled={loading || screening.approval_status !== 'pending'}
          >
            {screening.approval_status === 'approved' ? '✓ Approved' : 'Approve'}
          </button>
        </div>
      </div>
    </div>
  )
}
