import { useState, useEffect } from 'react'
import { screeningAPI } from '../services/api'
import './ScreeningForm.css'

export default function ScreeningForm({ job, candidateIds, onBack, onComplete }) {
  const [screenings, setScreenings] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)

  useEffect(() => {
    loadScreenings()
  }, [])

  const loadScreenings = async () => {
    try {
      setLoading(true)
      // Get all screenings for this job
      const listRes = await screeningAPI.listScreeningsForJob(job.id)
      const allScreenings = listRes.data.screenings || []

      // Filter to just the screenings for selected candidates
      const relevantScreenings = allScreenings.filter(s =>
        candidateIds.includes(s.candidate_id)
      )

      if (relevantScreenings.length === 0) {
        throw new Error('No screenings found for selected candidates')
      }

      // For each screening, start workflow if needed and get full details
      const detailedScreenings = []
      for (const screening of relevantScreenings) {
        try {
          // If screening hasn't been run yet (no fit score), start the workflow
          if (!screening.fit_score) {
            await screeningAPI.startWorkflow(screening.id)
          }
          // Always get full details to have candidate and message data
          const detailRes = await screeningAPI.getScreeningDetail(screening.id)
          if (detailRes.data?.screening) {
            detailedScreenings.push(detailRes.data.screening)
          } else {
            detailedScreenings.push(screening)
          }
        } catch (e) {
          console.warn(`Could not get full details for screening ${screening.id}:`, e)
          detailedScreenings.push(screening)
        }
      }

      // Sort by fit score (high to low)
      const sorted = detailedScreenings.sort((a, b) => {
        const scoreA = a.fit_score || 0
        const scoreB = b.fit_score || 0
        return scoreB - scoreA
      })

      setScreenings(sorted)
      setError(null)
    } catch (err) {
      setError('Failed to load screenings: ' + (err.message || 'Unknown error'))
      console.error(err)
      setScreenings([])
    } finally {
      setLoading(false)
    }
  }

  const refreshScreening = async (screeningId) => {
    try {
      const { data } = await screeningAPI.getScreeningDetail(screeningId)
      setScreenings(prev => prev.map(s => s.id === screeningId ? data.screening : s))
    } catch (err) {
      console.error(err)
    }
  }

  const handleApprove = async () => {
    const screening = screenings[currentIndex]
    if (!screening) {
      setError('No screening data available')
      return
    }
    try {
      setActionLoading(true)
      console.log('Approving screening:', screening.id)
      const result = await screeningAPI.approve(screening.id, 'Approved by recruiter')
      console.log('Approve result:', result)
      setScreenings(prev => prev.map(s =>
        s.id === screening.id ? { ...s, approval_status: 'approved' } : s
      ))
      nextScreening()
      setError(null)
    } catch (err) {
      const errMsg = err.response?.data?.detail || err.message || 'Failed to approve'
      setError(errMsg)
      console.error('Approve error:', err)
    } finally {
      setActionLoading(false)
    }
  }

  const handleReject = async () => {
    const screening = screenings[currentIndex]
    if (!screening) {
      setError('No screening data available')
      return
    }
    try {
      setActionLoading(true)
      console.log('Rejecting screening:', screening.id)
      const result = await screeningAPI.reject(screening.id, 'Rejected by recruiter')
      console.log('Reject result:', result)
      setScreenings(prev => prev.map(s =>
        s.id === screening.id ? { ...s, approval_status: 'rejected' } : s
      ))
      nextScreening()
      setError(null)
    } catch (err) {
      const errMsg = err.response?.data?.detail || err.message || 'Failed to reject'
      setError(errMsg)
      console.error('Reject error:', err)
    } finally {
      setActionLoading(false)
    }
  }

  const nextScreening = () => {
    if (currentIndex < screenings.length - 1) {
      setCurrentIndex(currentIndex + 1)
    } else {
      // All screening complete - show results
      if (onComplete) {
        onComplete(screenings)
      } else {
        setError('All candidates have been reviewed! Click Exit to go back.')
      }
    }
  }

  if (loading) return <div className="text-center"><div className="loading"></div></div>

  if (screenings.length === 0) {
    return (
      <div className="card">
        <p className="text-center">No screenings to display</p>
        <div className="text-center mt-20">
          <button className="primary" onClick={onBack}>Back</button>
        </div>
      </div>
    )
  }

  const screening = screenings[currentIndex]
  const candidate = screening?.candidate || {}

  if (!screening) {
    return (
      <div className="card">
        <p className="text-center">No screening data available</p>
        <div className="text-center mt-20">
          <button className="primary" onClick={onBack}>Back</button>
        </div>
      </div>
    )
  }

  return (
    <div className="screening-form">
      {error && (
        <div className="error-banner">
          {error}
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}

      <div className="card screening-card">
        <div className="screening-header">
          <div>
            <h2>{candidate.name || 'Candidate'}</h2>
            <p className="text-muted">{candidate.email || 'No email'}</p>
          </div>
          <div className="progress-bar">
            <span>{currentIndex + 1} / {screenings.length}</span>
            <div className="bar">
              <div className="fill" style={{ width: `${((currentIndex + 1) / screenings.length) * 100}%` }}></div>
            </div>
          </div>
        </div>

        <div className="screening-content mt-20">
          <div className="section">
            <h3>Fit Score</h3>
            <div className="fit-score">
              <div className="score-circle">{screening.fit_score ? Math.round(screening.fit_score) : '?'}%</div>
              <p>{screening.fit_reasoning || 'Calculating fit score...'}</p>
            </div>
          </div>

          {screening.generated_message && (
            <div className="section mt-20">
              <h3>Generated Message</h3>
              <div className="message-box">
                {screening.generated_message}
              </div>
            </div>
          )}

          <div className="section mt-20">
            <h3>Candidate Info</h3>
            <p><strong>Email:</strong> {candidate.email}</p>
            <p><strong>Skills:</strong> {candidate.parsed_skills?.join(', ') || 'Not parsed'}</p>
            <p><strong>Experience:</strong> {candidate.experience_years} years</p>
          </div>
        </div>

        <div className="flex-between mt-20">
          <button className="danger" onClick={handleReject} disabled={actionLoading}>
            Reject
          </button>
          <div className="flex">
            {currentIndex > 0 && (
              <button className="primary" onClick={() => setCurrentIndex(currentIndex - 1)} disabled={actionLoading}>
                Previous
              </button>
            )}
            <button className="success" onClick={handleApprove} disabled={actionLoading}>
              Approve
            </button>
            {currentIndex < screenings.length - 1 && (
              <button className="primary" onClick={nextScreening}>
                Next
              </button>
            )}
          </div>
          <button className="primary" onClick={onBack}>
            Exit
          </button>
        </div>
      </div>
    </div>
  )
}
