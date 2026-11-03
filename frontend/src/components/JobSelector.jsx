import './JobSelector.css'

export default function JobSelector({ jobs, onSelectJob, onRefresh }) {
  return (
    <div className="job-selector">
      <div className="card">
        <div className="flex-between">
          <h2>Select a Job to Screen</h2>
          <button className="primary" onClick={onRefresh}>Refresh</button>
        </div>

        {jobs.length === 0 ? (
          <p className="text-center text-muted mt-20">No jobs available</p>
        ) : (
          <div className="grid-2 mt-20">
            {jobs.map(job => {
              const desc = job.description || ''
              const requirements = job.required_skills || job.requirements || []
              const level = job.level || 'mid'

              return (
                <div key={job.id} className="job-card" onClick={() => onSelectJob(job)}>
                  <h3>{job.title}</h3>
                  <p className="text-sm text-muted mb-10">
                    {desc.substring(0, 100)}
                    {desc.length > 100 ? '...' : ''}
                  </p>
                  <div className="flex">
                    {requirements.slice(0, 3).map((req, idx) => (
                      <span key={`${req}-${idx}`} className="badge success">{req}</span>
                    ))}
                    {requirements.length > 3 && (
                      <span className="badge warning">+{requirements.length - 3}</span>
                    )}
                  </div>
                  <div className="flex-between mt-20">
                    <span className={`badge ${level === 'senior' ? 'danger' : 'warning'}`}>
                      {level}
                    </span>
                    <button className="primary">Select</button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
