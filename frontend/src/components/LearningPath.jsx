function parsePlanGuide(planText) {
  const lines = String(planText || "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  const guide = {
    role: "",
    goal: "",
    currentLevel: "",
    timeAvailable: "",
    summary: "",
    weeks: [],
    books: [],
    videos: [],
    projectTitle: "Project",
    project: [],
    nextAction: [],
    followUpQuestions: [],
  };

  let currentSection = "";
  let currentWeek = null;

  for (const line of lines) {
    if (line.startsWith("SUMMARY:")) {
      guide.summary = line.replace("SUMMARY:", "").trim();
      currentSection = "summary";
      currentWeek = null;
      continue;
    }

    if (line.startsWith("ROLE:")) {
      guide.role = line.replace("ROLE:", "").trim();
      currentSection = "meta";
      currentWeek = null;
      continue;
    }

    if (line.startsWith("GOAL:")) {
      guide.goal = line.replace("GOAL:", "").trim();
      currentSection = "meta";
      currentWeek = null;
      continue;
    }

    if (line.startsWith("CURRENT LEVEL:")) {
      guide.currentLevel = line.replace("CURRENT LEVEL:", "").trim();
      currentSection = "meta";
      currentWeek = null;
      continue;
    }

    if (line.startsWith("TIME AVAILABLE:")) {
      guide.timeAvailable = line.replace("TIME AVAILABLE:", "").trim();
      currentSection = "meta";
      currentWeek = null;
      continue;
    }

    if (/^WEEK\s+\d+\s*:/i.test(line)) {
      currentWeek = {
        id: `week-${guide.weeks.length + 1}`,
        title: line.replace(/^WEEK\s+\d+\s*:/i, "").trim(),
        details: [],
      };
      guide.weeks.push(currentWeek);
      currentSection = "week";
      continue;
    }

    if (line === "BOOKS:") {
      currentSection = "books";
      currentWeek = null;
      continue;
    }

    if (line === "VIDEOS:") {
      currentSection = "videos";
      currentWeek = null;
      continue;
    }

    if (line === "NEXT ACTION:") {
      currentSection = "next";
      currentWeek = null;
      continue;
    }

    if (line === "PROJECT:" || line === "STUDY OUTPUT:" || line === "TEACHING OUTPUT:") {
      guide.projectTitle = line.replace(":", "").trim();
      currentSection = "project";
      currentWeek = null;
      continue;
    }

    if (line === "FOLLOW-UP QUESTIONS:") {
      currentSection = "follow-up";
      currentWeek = null;
      continue;
    }

    if (currentSection === "week" && currentWeek) {
      currentWeek.details.push(line.replace(/^-+\s*/, ""));
      continue;
    }

    if (currentSection === "books" && line.startsWith("-")) {
      guide.books.push(line.replace(/^-+\s*/, ""));
      continue;
    }

    if (currentSection === "videos" && line.startsWith("-")) {
      guide.videos.push(line.replace(/^-+\s*/, ""));
      continue;
    }

    if (currentSection === "next" && line.startsWith("-")) {
      guide.nextAction.push(line.replace(/^-+\s*/, ""));
      continue;
    }

    if (currentSection === "project" && line.startsWith("-")) {
      guide.project.push(line.replace(/^-+\s*/, ""));
      continue;
    }

    if (currentSection === "follow-up" && line.startsWith("-")) {
      guide.followUpQuestions.push(line.replace(/^-+\s*/, ""));
    }
  }

  return guide;
}

function parseStructuredPlan(structuredPlan) {
  if (!structuredPlan || typeof structuredPlan !== "object") {
    return null;
  }

  const weeklyPlan = Array.isArray(structuredPlan.weekly_plan) ? structuredPlan.weekly_plan : [];
  const resources = structuredPlan.recommended_resources || {};
  const externalResources = Array.isArray(resources.external) ? resources.external : [];

  return {
    role: structuredPlan.role || "",
    goal: structuredPlan.goal || "",
    currentLevel: structuredPlan.knowledge_level || "",
    timeAvailable: "Weekly focused blocks aligned to your work schedule",
    summary: structuredPlan.summary || "",
    weeks: weeklyPlan.map((week, index) => ({
      id: `week-${index + 1}`,
      title: week.focus || `Week ${index + 1}`,
      details: [
        `Focus: ${week.focus || ""}`,
        `Study: ${week.study || ""}`,
        `Practice: ${week.practice || ""}`,
        `Deliverable: ${week.deliverable || ""}`,
        `Success Check: ${week.business_impact || ""}`,
      ],
    })),
    books: externalResources
      .filter((item) => String(item.type || "").toLowerCase().includes("book"))
      .map((item) => item.name || ""),
    videos: externalResources
      .filter((item) => String(item.type || "").toLowerCase().includes("video"))
      .map((item) => item.name || ""),
    projectTitle: "Practice Tasks",
    project: (structuredPlan.practice_tasks || []).map(
      (task) =>
        `${task.title || "Task"} (${task.difficulty || "Medium"}, ~${task.estimated_hours || 1}h) - ${
          task.success_metric || "Complete and review outcomes."
        }`
    ),
    nextAction: structuredPlan.next_action ? [structuredPlan.next_action] : [],
    followUpQuestions: (structuredPlan.mini_quiz || []).map((quiz) => quiz.question || ""),
  };
}

function toDisplayCase(value) {
  return String(value || "")
    .trim()
    .replace(/\s+/g, " ")
    .split(" ")
    .filter(Boolean)
    .map((word) => {
      const normalized = word.toLowerCase();
      return normalized.charAt(0).toUpperCase() + normalized.slice(1);
    })
    .join(" ");
}

function buildRoadmapTitle(role, goal) {
  const cleanRole = toDisplayCase(role);
  const cleanGoal = String(goal || "").trim().replace(/\s+/g, " ");

  if (cleanRole && cleanGoal) {
    return `${cleanRole} Roadmap For ${cleanGoal}`;
  }

  if (cleanRole) {
    return `${cleanRole} Roadmap`;
  }

  return "AI Learning Roadmap";
}

function buildRoadmapSubtitle(role, goal) {
  const cleanRole = toDisplayCase(role);
  const cleanGoal = String(goal || "").trim().replace(/\s+/g, " ");

  if (cleanRole && cleanGoal) {
    return `${cleanRole} learning path for ${cleanGoal}`;
  }

  if (cleanGoal) {
    return `${cleanGoal} learning path`;
  }

  return "Personalized AI-guided learning path";
}

export default function LearningPath({
  sectionId,
  steps,
  planText,
  structuredPlan,
  plans,
  selectedPlanId,
  loading,
  error,
  onGenerate,
  onUpdateProgress,
  onSelectPlan,
  canEdit,
}) {
  const activePlan = plans?.find((plan) => plan.id === selectedPlanId) || plans?.[0];
  const guide = parseStructuredPlan(structuredPlan) || parsePlanGuide(planText);
  const roadmapTitle = buildRoadmapTitle(guide.role || activePlan?.role, guide.goal || activePlan?.goal);
  const roadmapSubtitle = buildRoadmapSubtitle(
    guide.role || activePlan?.role,
    guide.goal || activePlan?.goal
  );

  return (
    <section className="panel panel--wide" id={sectionId}>
      <div className="panel-heading">
        <div>
          <p className="eyebrow">{roadmapSubtitle}</p>
          <h2>{roadmapTitle}</h2>
        </div>
        <button type="button" className="ghost-button" onClick={onGenerate} disabled={loading}>
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {error ? <p className="feedback feedback--error">{error}</p> : null}

      {!planText && !loading ? (
        <div className="empty-state">
          <h3>Generate your first roadmap</h3>
          <p>Use the planner above to create a structured 4-week plan.</p>
        </div>
      ) : null}

      {loading ? <div className="skeleton-block" /> : null}

      {guide.summary ? (
        <article className="guide-summary">
          <p className="eyebrow">Coach Summary</p>
          <h3>What this plan is optimizing for</h3>
          <p>{guide.summary}</p>
        </article>
      ) : null}

      {guide.role || guide.goal || guide.currentLevel || guide.timeAvailable ? (
        <section className="guide-meta-grid">
          {guide.role ? (
            <article className="guide-meta-card">
              <span>Role</span>
              <strong>{guide.role}</strong>
            </article>
          ) : null}
          {guide.goal ? (
            <article className="guide-meta-card">
              <span>Goal</span>
              <strong>{guide.goal}</strong>
            </article>
          ) : null}
          {guide.currentLevel ? (
            <article className="guide-meta-card">
              <span>Current level</span>
              <strong>{guide.currentLevel}</strong>
            </article>
          ) : null}
          {guide.timeAvailable ? (
            <article className="guide-meta-card">
              <span>Time available</span>
              <strong>{guide.timeAvailable}</strong>
            </article>
          ) : null}
        </section>
      ) : null}

      {guide.nextAction.length ? (
        <article className="guide-action">
          <p className="eyebrow">Start Here</p>
          <h3>Best next action</h3>
          {guide.nextAction.map((item) => (
            <p key={item}>{item}</p>
          ))}
        </article>
      ) : null}

      {guide.weeks.length ? (
        <div className="timeline">
          {guide.weeks.map((week, index) => (
            <article key={week.id} className="timeline-item">
              <span className="timeline-index">{String(index + 1).padStart(2, "0")}</span>
              <div>
                <h3>{week.title || `Week ${index + 1}`}</h3>
                <div className="week-detail-list">
                  {week.details.map((detail) => (
                    <article key={detail} className="week-detail-item">
                      <strong>{detail.split(":")[0] || "Detail"}</strong>
                      <p>{detail.includes(":") ? detail.split(":").slice(1).join(":").trim() : detail}</p>
                    </article>
                  ))}
                </div>
              </div>
            </article>
          ))}
        </div>
      ) : steps.length ? (
        <div className="timeline">
          {steps.map((step, index) => (
            <article key={step.id} className="timeline-item">
              <span className="timeline-index">{String(index + 1).padStart(2, "0")}</span>
              <div>
                <h3>{step.title}</h3>
                <p>{step.detail}</p>
              </div>
            </article>
          ))}
        </div>
      ) : null}

      {guide.books.length || guide.videos.length ? (
        <section className="resource-shelf">
          {guide.books.length ? (
            <div className="resource-group">
              <p className="eyebrow">Books</p>
              {guide.books.map((item) => (
                <article key={item} className="resource-card">
                  <p>{item}</p>
                </article>
              ))}
            </div>
          ) : null}
          {guide.videos.length ? (
            <div className="resource-group">
              <p className="eyebrow">Videos</p>
              {guide.videos.map((item) => (
                <article key={item} className="resource-card">
                  <p>{item}</p>
                </article>
              ))}
            </div>
          ) : null}
        </section>
      ) : null}

      {guide.project.length ? (
        <article className="guide-action">
          <p className="eyebrow">{guide.projectTitle}</p>
          <h3>{guide.projectTitle === "Project" ? "What to build" : guide.projectTitle}</h3>
          {guide.project.map((item) => (
            <p key={item}>{item}</p>
          ))}
        </article>
      ) : null}

      {guide.followUpQuestions.length ? (
        <section className="guide-follow-up">
          <p className="eyebrow">Follow-Up Questions</p>
          <div className="prompt-row">
            {guide.followUpQuestions.map((item) => (
              <span key={item} className="chip-button">
                {item}
              </span>
            ))}
          </div>
        </section>
      ) : null}

      {plans?.length ? (
        <div className="stored-plans">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Saved plans</p>
              <h2>Tracked progress</h2>
            </div>
          </div>

          {plans.map((plan) => (
            <article
              key={plan.id}
              className={`stored-plan-card ${plan.id === activePlan?.id ? "stored-plan-card--active" : ""}`}
            >
              <div>
                <h3>{plan.role}</h3>
                <p>{plan.goal}</p>
              </div>
              <div className="stored-plan-meta">
                <span>{plan.completed_steps}/{plan.total_steps} steps</span>
                <span>{plan.progress_percent}% complete</span>
                <span>{plan.hours_spent}h logged</span>
              </div>
              <button
                type="button"
                className="chip-button"
                onClick={() => onSelectPlan(plan)}
              >
                {plan.id === activePlan?.id ? "Viewing now" : "View roadmap"}
              </button>
              {canEdit ? (
                <form
                  className="progress-form"
                  onSubmit={(event) => {
                    event.preventDefault();
                    const form = new FormData(event.currentTarget);
                    onUpdateProgress(
                      plan.id,
                      Number(form.get("completed_steps") || 0),
                      Number(form.get("hours_spent") || 0)
                    );
                  }}
                >
                  <label>
                    <span>Completed steps</span>
                    <input
                      name="completed_steps"
                      type="number"
                      min="0"
                      max={plan.total_steps}
                      defaultValue={plan.completed_steps}
                    />
                  </label>
                  <label>
                    <span>Hours spent</span>
                    <input
                      name="hours_spent"
                      type="number"
                      min="0"
                      defaultValue={plan.hours_spent}
                    />
                  </label>
                  <button type="submit" className="ghost-button">
                    Update progress
                  </button>
                </form>
              ) : null}
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}
