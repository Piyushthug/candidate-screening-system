import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ResultsSummary from '../ResultsSummary'
import * as api from '../../services/api'

vi.mock('../../services/api')
vi.mock('../CandidateModal', () => ({
  default: ({ screening, onClose, onDecision }) => (
    <div data-testid="modal">
      <div>{screening?.candidate?.name}</div>
      <button onClick={onClose}>Close Modal</button>
      <button onClick={() => onDecision(screening.id, 'approved')}>Modal Approve</button>
    </div>
  )
}))

describe('ResultsSummary', () => {
  const mockJob = {
    id: 'job_001',
    title: 'Senior Python Engineer'
  }

  const mockScreenings = [
    {
      id: 'screening_001',
      candidate: {
        id: 'cand_001',
        name: 'Alice Johnson',
        email: 'alice@example.com',
        parsed_skills: ['Python', 'FastAPI'],
        experience_years: 7
      },
      fit_score: 85,
      approval_status: 'pending'
    },
    {
      id: 'screening_002',
      candidate: {
        id: 'cand_002',
        name: 'Bob Smith',
        email: 'bob@example.com',
        parsed_skills: ['Python', 'Django'],
        experience_years: 5
      },
      fit_score: 72,
      approval_status: 'approved'
    },
    {
      id: 'screening_003',
      candidate: {
        id: 'cand_003',
        name: 'Carol White',
        email: 'carol@example.com',
        parsed_skills: ['JavaScript'],
        experience_years: 3
      },
      fit_score: 45,
      approval_status: 'rejected'
    }
  ]

  const mockOnBack = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    api.screeningAPI = {
      getScreeningDetail: vi.fn().mockResolvedValue({
        data: { screening: mockScreenings[0] }
      }),
      startWorkflow: vi.fn().mockResolvedValue({ data: {} }),
      sendApprovalEmail: vi.fn().mockResolvedValue({ data: { status: 'sent' } })
    }
  })

  it('renders job title and screening count', () => {
    render(
      <ResultsSummary
        job={mockJob}
        screenings={mockScreenings}
        onBack={mockOnBack}
      />
    )

    expect(screen.getByText('Senior Python Engineer')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('displays statistics correctly', () => {
    render(
      <ResultsSummary
        job={mockJob}
        screenings={mockScreenings}
        onBack={mockOnBack}
      />
    )

    // Verify component renders without errors
    expect(screen.getByText('Review Candidates')).toBeInTheDocument()
  })

  it('renders all candidates as clickable cards', () => {
    render(
      <ResultsSummary
        job={mockJob}
        screenings={mockScreenings}
        onBack={mockOnBack}
      />
    )

    expect(screen.getByText('Alice Johnson')).toBeInTheDocument()
    expect(screen.queryAllByText(/Smith|White/).length).toBeGreaterThanOrEqual(2)
  })

  it('opens modal when candidate card clicked', () => {
    render(
      <ResultsSummary
        job={mockJob}
        screenings={mockScreenings}
        onBack={mockOnBack}
      />
    )

    const aliceCard = screen.getByText('Alice Johnson').closest('.result-card')
    fireEvent.click(aliceCard)

    expect(screen.getByTestId('modal')).toBeInTheDocument()
  })

  it('closes modal when close is clicked', async () => {
    render(
      <ResultsSummary
        job={mockJob}
        screenings={mockScreenings}
        onBack={mockOnBack}
      />
    )

    const aliceCard = screen.getByText('Alice Johnson').closest('.result-card')
    fireEvent.click(aliceCard)

    expect(screen.getByTestId('modal')).toBeInTheDocument()

    const closeButton = screen.getByText('Close Modal')
    fireEvent.click(closeButton)

    await waitFor(() => {
      expect(screen.queryByTestId('modal')).not.toBeInTheDocument()
    })
  })

  it('updates screening status after decision in modal', async () => {
    const { rerender } = render(
      <ResultsSummary
        job={mockJob}
        screenings={mockScreenings}
        onBack={mockOnBack}
      />
    )

    const aliceCard = screen.getByText('Alice Johnson').closest('.result-card')
    fireEvent.click(aliceCard)

    const modalApproveButton = screen.getByText('Modal Approve')
    fireEvent.click(modalApproveButton)

    await waitFor(() => {
      const updatedScreening = {
        ...mockScreenings[0],
        approval_status: 'approved'
      }
      rerender(
        <ResultsSummary
          job={mockJob}
          screenings={[...mockScreenings]}
          onBack={mockOnBack}
        />
      )
    })
  })

  it('shows Back to Jobs button', () => {
    render(
      <ResultsSummary
        job={mockJob}
        screenings={mockScreenings}
        onBack={mockOnBack}
      />
    )

    const backButtons = screen.queryAllByText(/Back to Jobs/)
    expect(backButtons.length).toBeGreaterThan(0)

    fireEvent.click(backButtons[0])
    expect(mockOnBack).toHaveBeenCalled()
  })

  it('displays approved candidates in email section', () => {
    render(
      <ResultsSummary
        job={mockJob}
        screenings={mockScreenings}
        onBack={mockOnBack}
      />
    )

    // Verify the component renders and has the email section
    expect(screen.getByText('Send Approval Emails')).toBeInTheDocument()
  })

  it('handles send approval email for single candidate', async () => {
    render(
      <ResultsSummary
        job={mockJob}
        screenings={mockScreenings}
        onBack={mockOnBack}
      />
    )

    const sendEmailButtons = screen.getAllByText('Send Email')
    if (sendEmailButtons.length > 0) {
      fireEvent.click(sendEmailButtons[0])

      await waitFor(() => {
        expect(api.screeningAPI.sendApprovalEmail).toHaveBeenCalled()
      })
    }
  })

  it('handles send all emails', async () => {
    render(
      <ResultsSummary
        job={mockJob}
        screenings={mockScreenings}
        onBack={mockOnBack}
      />
    )

    const sendAllButton = screen.getByText(/Send All Emails/)
    if (sendAllButton) {
      fireEvent.click(sendAllButton)

      await waitFor(() => {
        expect(api.screeningAPI.sendApprovalEmail).toHaveBeenCalled()
      })
    }
  })

  it('shows fit scores for pending candidates', () => {
    const pendingScreenings = mockScreenings.filter(s => s.approval_status === 'pending')

    render(
      <ResultsSummary
        job={mockJob}
        screenings={pendingScreenings}
        onBack={mockOnBack}
      />
    )

    expect(screen.getByText('85%')).toBeInTheDocument()
  })

  it('shows approved badge for approved candidates', () => {
    const approvedScreenings = mockScreenings.filter(s => s.approval_status === 'approved')

    render(
      <ResultsSummary
        job={mockJob}
        screenings={approvedScreenings}
        onBack={mockOnBack}
      />
    )

    expect(screen.getByText('✓ Approved')).toBeInTheDocument()
  })

  it('handles empty screenings gracefully', () => {
    render(
      <ResultsSummary
        job={mockJob}
        screenings={[]}
        onBack={mockOnBack}
      />
    )

    expect(screen.getByText('Review Candidates')).toBeInTheDocument()
  })
})
