import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import App from '../../App'
import * as api from '../../services/api'

vi.mock('../../services/api')

describe('App Navigation Flow', () => {
  const mockJobs = [
    {
      id: 'job_001',
      title: 'Senior Python Engineer',
      description: 'Looking for a Python expert'
    }
  ]

  const mockCandidates = [
    {
      id: 'cand_001',
      name: 'Alice Johnson',
      email: 'alice@example.com',
      parsed_skills: ['Python', 'FastAPI'],
      experience_years: 7
    },
    {
      id: 'cand_002',
      name: 'Bob Smith',
      email: 'bob@example.com',
      parsed_skills: ['Python', 'Django'],
      experience_years: 5
    }
  ]

  const mockScreenings = [
    {
      id: 'screening_001',
      candidate: mockCandidates[0],
      fit_score: 85,
      approval_status: 'pending',
      generated_message: 'Test message'
    },
    {
      id: 'screening_002',
      candidate: mockCandidates[1],
      fit_score: 72,
      approval_status: 'pending',
      generated_message: 'Test message'
    }
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    api.screeningAPI = {
      getJobs: vi.fn().mockResolvedValue({ data: mockJobs }),
      getCandidatesForJob: vi.fn().mockResolvedValue({ data: mockCandidates }),
      createBatch: vi.fn().mockResolvedValue({
        data: {
          screening_ids: ['screening_001', 'screening_002']
        }
      }),
      getScreeningDetail: vi.fn().mockResolvedValue({
        data: { screening: mockScreenings[0] }
      })
    }
  })

  it('renders job selector on initial load', async () => {
    render(<App />)

    await waitFor(() => {
      expect(screen.getByText('AI Candidate Screening System')).toBeInTheDocument()
    })
  })

  it('displays jobs after loading', async () => {
    render(<App />)

    await waitFor(() => {
      expect(screen.getByText('Senior Python Engineer')).toBeInTheDocument()
    })
  })

  it('navigates to candidate list when job selected', async () => {
    render(<App />)

    await waitFor(() => {
      expect(screen.getByText('Senior Python Engineer')).toBeInTheDocument()
    })

    const jobCard = screen.getByText('Senior Python Engineer').closest('button')
    if (jobCard) {
      fireEvent.click(jobCard)

      await waitFor(() => {
        expect(api.screeningAPI.getCandidatesForJob).toHaveBeenCalled()
      })
    }
  })

  it('shows candidates after job selection', async () => {
    render(<App />)

    await waitFor(() => {
      expect(screen.getByText('Senior Python Engineer')).toBeInTheDocument()
    })

    const jobCard = screen.getByText('Senior Python Engineer').closest('button')
    if (jobCard) {
      fireEvent.click(jobCard)

      await waitFor(() => {
        expect(screen.getByText('Alice Johnson')).toBeInTheDocument()
        expect(screen.getByText('Bob Smith')).toBeInTheDocument()
      })
    }
  })

  it('navigates to results page after starting screening', async () => {
    render(<App />)

    // Select job
    await waitFor(() => {
      expect(screen.getByText('Senior Python Engineer')).toBeInTheDocument()
    })

    const jobCard = screen.getByText('Senior Python Engineer').closest('button')
    if (jobCard) {
      fireEvent.click(jobCard)

      // Wait for candidates to load
      await waitFor(() => {
        expect(screen.getByText('Alice Johnson')).toBeInTheDocument()
      })

      // Select candidates
      const checkboxes = screen.getAllByRole('checkbox')
      if (checkboxes.length > 0) {
        fireEvent.click(checkboxes[0])
        fireEvent.click(checkboxes[1])

        // Start screening
        const startButton = screen.getByText('Start Screening')
        fireEvent.click(startButton)

        // Should navigate to results
        await waitFor(() => {
          expect(api.screeningAPI.createBatch).toHaveBeenCalled()
        })
      }
    }
  })

  it('handles error when loading jobs fails', async () => {
    api.screeningAPI.getJobs = vi
      .fn()
      .mockRejectedValue(new Error('Failed to load jobs'))

    render(<App />)

    await waitFor(() => {
      expect(screen.getByText(/Error/)).toBeInTheDocument()
    })
  })

  it('handles back navigation from candidate list', async () => {
    render(<App />)

    await waitFor(() => {
      expect(screen.getByText('Senior Python Engineer')).toBeInTheDocument()
    })

    const jobCard = screen.getByText('Senior Python Engineer').closest('button')
    if (jobCard) {
      fireEvent.click(jobCard)

      await waitFor(() => {
        expect(screen.getByText('Alice Johnson')).toBeInTheDocument()
      })

      const backButton = screen.getByText(/Back/)
      fireEvent.click(backButton)

      await waitFor(() => {
        expect(screen.getByText('Senior Python Engineer')).toBeInTheDocument()
      })
    }
  })

  it('shows loading state while fetching', async () => {
    api.screeningAPI.getJobs = vi.fn().mockImplementation(
      () =>
        new Promise(resolve =>
          setTimeout(() => resolve({ data: mockJobs }), 100)
        )
    )

    render(<App />)

    expect(screen.getByText('Loading...')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('Senior Python Engineer')).toBeInTheDocument()
    })
  })
})
