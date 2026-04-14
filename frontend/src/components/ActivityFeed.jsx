function formatTimestamp(value) {
  if (!value) {
    return "Just now";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Recent";
  }

  return date.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}


export default function ActivityFeed({ items, sectionId }) {
  return (
    <section className="panel" id={sectionId}>
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Recent activity</p>
          <h2>Progress timeline</h2>
        </div>
      </div>

      {items?.length ? (
        <div className="activity-list">
          {items.map((item) => (
            <article key={item.id} className="activity-item">
              <div>
                <strong>{item.role}</strong>
                <p>{item.goal}</p>
              </div>
              <div className="activity-meta">
                <span>{item.progress_percent}% complete</span>
                <span>{item.completed_steps} steps done</span>
                <span>{item.hours_spent}h logged</span>
                <span>{formatTimestamp(item.created_at)}</span>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <h3>No tracked activity yet</h3>
          <p>Generate a roadmap and update progress to build your activity timeline.</p>
        </div>
      )}
    </section>
  );
}
