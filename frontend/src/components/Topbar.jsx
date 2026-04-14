export default function Topbar({
  apiStatus,
  user,
  role,
  goal,
  knowledgeLevel,
  department,
  businessContext,
  pastLearning,
  summary,
  onRoleChange,
  onGoalChange,
  onKnowledgeLevelChange,
  onDepartmentChange,
  onBusinessContextChange,
  onPastLearningChange,
  onSubmit,
  loading,
  onLogout,
}) {
  return (
    <section className="hero-panel">
      <div className="hero-copy">
        <p className="eyebrow">Learning workspace</p>
        <h1>Build sharper skills with a plan that actually moves.</h1>
        <p className="hero-text">
          Connect your role, define the goal, and generate a practical roadmap with
          a guided assistant beside it.
        </p>
        <div className="hero-guide">
          <article className="hero-guide-card">
            <strong>How the coach helps</strong>
            <p>It turns your role and goal into a realistic roadmap, one project, and one best next action.</p>
          </article>
          <article className="hero-guide-card">
            <strong>Best way to use it</strong>
            <p>Generate a plan, ask for a 7-day sprint, then track progress after each study block.</p>
          </article>
        </div>
        <div className="status-row">
          <span className={`status-pill status-pill--${apiStatus}`}>
            {apiStatus === "online" ? "Backend online" : apiStatus === "offline" ? "Backend offline" : "Checking backend"}
          </span>
          <span className="hero-meta">FastAPI + React dashboard</span>
          {user ? (
            <span className="hero-meta">
              Signed in as <strong>{user.full_name}</strong>
            </span>
          ) : null}
          {summary ? <span className="hero-meta">{summary}</span> : null}
        </div>
      </div>

      <form className="planner-form" onSubmit={onSubmit}>
        <label>
          <span>Target role</span>
          <input
            value={role}
            onChange={(event) => onRoleChange(event.target.value)}
            placeholder="Frontend Developer"
          />
        </label>

        <label>
          <span>Learning goal</span>
          <textarea
            value={goal}
            onChange={(event) => onGoalChange(event.target.value)}
            placeholder="Become job-ready for production React work"
            rows={4}
          />
        </label>

        <label>
          <span>Current knowledge level</span>
          <select
            value={knowledgeLevel}
            onChange={(event) => onKnowledgeLevelChange(event.target.value)}
          >
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
        </label>

        <label>
          <span>Department</span>
          <input
            value={department}
            onChange={(event) => onDepartmentChange(event.target.value)}
            placeholder="Engineering"
          />
        </label>

        <label>
          <span>Business context</span>
          <textarea
            value={businessContext}
            onChange={(event) => onBusinessContextChange(event.target.value)}
            placeholder="Example: Improve onboarding speed and reduce recurring production incidents."
            rows={3}
          />
        </label>

        <label>
          <span>Past learning or certifications</span>
          <textarea
            value={pastLearning}
            onChange={(event) => onPastLearningChange(event.target.value)}
            placeholder="Example: Completed React basics, internal API bootcamp, and incident response workshop."
            rows={3}
          />
        </label>

        <button type="submit" className="primary-button" disabled={loading}>
          {loading ? "Generating plan..." : "Generate learning plan"}
        </button>
        {user ? (
          <button type="button" className="ghost-button" onClick={onLogout}>
            Log out
          </button>
        ) : (
          <p className="feedback">Sign in to save plans, track progress, and sync metrics.</p>
        )}
      </form>
    </section>
  );
}
