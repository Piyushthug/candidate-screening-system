import { useState, useEffect } from 'react'
import { screeningAPI } from './services/api'
import JobSelector from './components/JobSelector'
import CandidateList from './components/CandidateList'
import ResultsSummary from './components/ResultsSummary'
import './App.css'

function App() {
  const [page, setPage] = useState('jobs') // jobs, candidates, results
  const [jobs, setJobs] = useState([])
  const [candidates, setCandidates] = useState([])
  const [screenings, setScreenings] = useState([])
  const [selectedJob, setSelectedJob] = useState(null)
  const [selectedCandidates, setSelectedCandidates] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Load jobs on mount
  useEffect(() => {
    loadJobs()
  }, [])

  const loadJobs = async () => {
    try {
      setLoading(true)
      const { data } = await screeningAPI.getJobs()
      setJobs(data)
      setError(null)
    } catch (err) {
      setError('Failed to load jobs')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleJobSelect = async (job) => {
    try {
      setLoading(true)
      setSelectedJob(job)
      const { data } = await screeningAPI.getCandidatesForJob(job.id)
      setCandidates(data)
      setSelectedCandidates([])
      setPage('candidates')
      setError(null)
    } catch (err) {
      setError('Failed to load candidates')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleCandidateToggle = (candidateId) => {
    setSelectedCandidates(prev => {
      if (prev.includes(candidateId)) {
        return prev.filter(id => id !== candidateId)
      } else {
        return [...prev, candidateId]
      }
    })
  }

  const handleStartScreening = async () => {
    if (selectedCandidates.length === 0) {
      setError('Please select at least one candidate')
      return
    }

    try {
      setLoading(true)
      const { data } = await screeningAPI.createBatch(selectedJob.id, selectedCandidates)

      // Load full screening details for results page
      const screeningsList = []
      for (const screeningId of data.screening_ids) {
        try {
          const { data: screeningData } = await screeningAPI.getScreeningDetail(screeningId)
          if (screeningData?.screening) {
            screeningsList.push(screeningData.screening)
          }
        } catch (e) {
          console.warn(`Could not load screening ${screeningId}:`, e)
        }
      }

      setScreenings(screeningsList)
      setPage('results')
      setError(null)
    } catch (err) {
      setError('Failed to start screening: ' + (err.message || 'Unknown error'))
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="container">
          <h1>AI Candidate Screening System</h1>
          <p>Powered by Gemini</p>
        </div>
      </header>

      <div className="container">
        {error && (
          <div className="error-banner">
            <strong>Error:</strong> {error}
            <button onClick={() => setError(null)}>×</button>
          </div>
        )}

        {loading && (
          <div className="loading-container">
            <div className="loading"></div>
            <p>Loading...</p>
          </div>
        )}

        {!loading && page === 'jobs' && (
          <JobSelector
            jobs={jobs}
            onSelectJob={handleJobSelect}
            onRefresh={loadJobs}
          />
        )}

        {!loading && page === 'candidates' && selectedJob && (
          <CandidateList
            job={selectedJob}
            candidates={candidates}
            selectedCandidates={selectedCandidates}
            onToggle={handleCandidateToggle}
            onStart={handleStartScreening}
            onBack={() => setPage('jobs')}
          />
        )}

        {!loading && page === 'results' && selectedJob && (
          <ResultsSummary
            job={selectedJob}
            screenings={screenings}
            onBack={() => setPage('jobs')}
          />
        )}
      </div>
    </div>
  )
}

export default App
