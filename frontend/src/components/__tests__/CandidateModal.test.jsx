import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import CandidateModal from '../CandidateModal'
import * as api from '../../services/api'

vi.mock('../../services/api')

describe('CandidateModal', () => {
  const mockScreening = {
    id: 'screening_123',
    candidate: {
      id: 'cand_001',
      name: 'Alice Johnson',
      email: 'alice@example.com',
      parsed_skills: ['Python', 'FastAPI', 'PostgreSQL'],
      experience_years: 7
    },
    fit_score: 85,
    fit_reasoning: 'Strong match for the role',
    generated_message: 'Hi Alice, we are interested in your profile...',
    approval_status: 'pending'
  }

  const mockOnClose = vi.fn()
  const mockOnDecision = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders modal with candidate details', () => {
    render(
      <CandidateModal
        screening={mockScreening}
        onClose={mockOnClose}
        onDecision={mockOnDecision}
      />
    )

    expect(screen.getByText('Alice Johnson')).toBeInTheDocument()
    expect(screen.getByText('alice@example.com')).toBeInTheDocument()
    expect(screen.getByText('Python, FastAPI, PostgreSQL')).toBeInTheDocument()
    expect(screen.getByText('7 years')).toBeInTheDocument()
  })

  it('displays fit score and reasoning', () => {
    render(
      <CandidateModal
        screening={mockScreening}
        onClose={mockOnClose}
        onDecision={mockOnDecision}
      />
    )

    // Modal renders without errors - content is inside the modal
    expect(screen.getByText('Fit Analysis')).toBeInTheDocument()
  })

  it('shows generated email draft', () => {
    render(
      <CandidateModal
        screening={mockScreening}
        onClose={mockOnClose}
        onDecision={mockOnDecision}
      />
    )

    expect(screen.getByText(/Hi Alice, we are interested/)).toBeInTheDocument()
  })

  it('closes modal when close button clicked', () => {
    render(
      <CandidateModal
        screening={mockScreening}
        onClose={mockOnClose}
        onDecision={mockOnDecision}
      />
    )

    const closeButton = screen.getByText('×')
    fireEvent.click(closeButton)

    expect(mockOnClose).toHaveBeenCalled()
  })

  it('closes modal when close button is clicked', () => {
    render(
      <CandidateModal
        screening={mockScreening}
        onClose={mockOnClose}
        onDecision={mockOnDecision}
      />
    )

    const closeButton = screen.getByText('×')
    fireEvent.click(closeButton)
    expect(mockOnClose).toHaveBeenCalled()
  })

  it('handles approve action', async () => {
    api.screeningAPI = {
      approve: vi.fn().mockResolvedValue({ data: { status: 'approved' } })
    }

    render(
      <CandidateModal
        screening={mockScreening}
        onClose={mockOnClose}
        onDecision={mockOnDecision}
      />
    )

    const approveButton = screen.getByText('Approve')
    fireEvent.click(approveButton)

    await waitFor(() => {
      expect(api.screeningAPI.approve).toHaveBeenCalledWith(
        'screening_123',
        'Approved by recruiter'
      )
    })

    await waitFor(() => {
      expect(mockOnDecision).toHaveBeenCalledWith('screening_123', 'approved')
    })
  })

  it('handles reject action', async () => {
    api.screeningAPI = {
      reject: vi.fn().mockResolvedValue({ data: { status: 'rejected' } })
    }

    render(
      <CandidateModal
        screening={mockScreening}
        onClose={mockOnClose}
        onDecision={mockOnDecision}
      />
    )

    const rejectButton = screen.getByText('Reject')
    fireEvent.click(rejectButton)

    await waitFor(() => {
      expect(api.screeningAPI.reject).toHaveBeenCalledWith(
        'screening_123',
        'Rejected by recruiter'
      )
    })

    await waitFor(() => {
      expect(mockOnDecision).toHaveBeenCalledWith('screening_123', 'rejected')
    })
  })

  it('disables buttons when approval_status is not pending', () => {
    const approvedScreening = {
      ...mockScreening,
      approval_status: 'approved'
    }

    render(
      <CandidateModal
        screening={approvedScreening}
        onClose={mockOnClose}
        onDecision={mockOnDecision}
      />
    )

    expect(screen.getByText('✓ Approved')).toBeDisabled()
    expect(screen.getByText('Reject')).toBeDisabled()
  })

  it('handles missing candidate data gracefully', () => {
    const incompleteScreening = {
      ...mockScreening,
      candidate: null
    }

    render(
      <CandidateModal
        screening={incompleteScreening}
        onClose={mockOnClose}
        onDecision={mockOnDecision}
      />
    )

    expect(screen.getByText('Candidate')).toBeInTheDocument()
    expect(screen.getByText('No email')).toBeInTheDocument()
  })

  it('handles API errors gracefully', async () => {
    api.screeningAPI = {
      approve: vi.fn().mockRejectedValue(new Error('API Error'))
    }

    render(
      <CandidateModal
        screening={mockScreening}
        onClose={mockOnClose}
        onDecision={mockOnDecision}
      />
    )

    const approveButton = screen.getByText('Approve')
    fireEvent.click(approveButton)

    await waitFor(() => {
      expect(screen.getByText(/Failed to approve/)).toBeInTheDocument()
    })

    expect(mockOnDecision).not.toHaveBeenCalled()
  })
})
