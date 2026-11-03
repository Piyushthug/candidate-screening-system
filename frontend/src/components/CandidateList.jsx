import './CandidateList.css'

export default function CandidateList({
  job,
  candidates,
  selectedCandidates,
  onToggle,
  onStart,
  onBack
}) {
  return (
    <div className="candidate-list">
      <div className="card">
        <div className="flex-between">
          <div>
            <h2>Select Candidates</h2>
            <p className="text-muted">For: <strong>{job.title}</strong></p>
          </div>
          <button className="danger" onClick={onBack}>Back</button>
        </div>

        {candidates.length === 0 ? (
          <p className="text-center text-muted mt-20">No candidates available</p>
        ) : (
          <>
            <div className="candidate-table mt-20">
              <div className="table-header">
                <input type="checkbox"
                  checked={selectedCandidates.length === candidates.length}
                  onChange={() => {
                    if (selectedCandidates.length === candidates.length) {
                      onToggle(null)
                    } else {
                      candidates.forEach(c => {
                        if (!selectedCandidates.includes(c.id)) {
                          onToggle(c.id)
                        }
                      })
                    }
                  }}
                />
                <span>Name</span>
                <span>Email</span>
                <span>Experience</span>
              </div>

              {candidates.map(candidate => (
                <div key={candidate.id} className="table-row">
                  <input
                    type="checkbox"
                    checked={selectedCandidates.includes(candidate.id)}
                    onChange={() => onToggle(candidate.id)}
                  />
                  <span className="name">{candidate.name}</span>
                  <span className="email">{candidate.email}</span>
                  <span className="experience">
                    {candidate.experience_years || '-'} years
                  </span>
                </div>
              ))}
            </div>

            <div className="flex-between mt-20">
              <span className="text-muted">
                {selectedCandidates.length} of {candidates.length} selected
              </span>
              <button
                className="success"
                onClick={onStart}
                disabled={selectedCandidates.length === 0}
              >
                Start Screening ({selectedCandidates.length})
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
