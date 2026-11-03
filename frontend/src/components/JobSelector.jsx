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
            {jobs.map(job => (
              <div key={job.id} className="job-card" onClick={() => onSelectJob(job)}>
                <h3>{job.title}</h3>
                <p className="text-sm text-muted mb-10">{job.description.substring(0, 100)}...</p>
                <div className="flex">
                  {job.requirements.slice(0, 3).map(req => (
                    <span key={req} className="badge success">{req}</span>
                  ))}
                  {job.requirements.length > 3 && (
                    <span className="badge warning">+{job.requirements.length - 3}</span>
                  )}
                </div>
                <div className="flex-between mt-20">
                  <span className={`badge ${job.level === 'senior' ? 'danger' : 'warning'}`}>
                    {job.level}
                  </span>
                  <button className="primary">Select</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
