import axios from 'axios'

const API_BASE_URL = 'http://127.0.0.1:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  }
})

export const screeningAPI = {
  // Jobs
  getJobs: () => api.get('/jobs'),
  getJob: (jobId) => api.get(`/jobs/${jobId}`),

  // Candidates
  getCandidates: () => api.get('/candidates'),
  getCandidate: (candidateId) => api.get(`/candidates/${candidateId}`),
  getCandidatesForJob: (jobId) => api.get(`/jobs/${jobId}/candidates`),

  // Screening
  createBatch: (jobId, candidateIds) => {
    const params = new URLSearchParams()
    params.append('job_id', jobId)
    candidateIds.forEach(id => params.append('candidate_ids', id))
    return api.post(`/screen/batch?${params.toString()}`)
  },

  startWorkflow: (screeningId) =>
    api.post(`/screen/${screeningId}/start-workflow`),

  getScreening: (screeningId) =>
    api.get(`/screen/${screeningId}`),

  getScreeningDetail: (screeningId) =>
    api.get(`/screen/${screeningId}/detail`),

  approve: (screeningId, feedback = '') =>
    api.post(`/screen/${screeningId}/approve`, {
      approval_status: 'approved',
      feedback
    }),

  reject: (screeningId, feedback = '') =>
    api.post(`/screen/${screeningId}/reject`, {
      approval_status: 'rejected',
      feedback
    }),

  listScreeningsForJob: (jobId) =>
    api.get(`/screen/job/${jobId}/screenings`)
}

export default api
