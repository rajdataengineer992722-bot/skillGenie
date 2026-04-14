const items = [
  { label: "Dashboard", target: "#top" },
  { label: "Learning Path", target: "#learning-path" },
  { label: "AI Assistant", target: "#assistant" },
  { label: "Insights", target: "#insights" },
  { label: "Activity", target: "#activity" },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand-block">
        <p className="brand-kicker">SkillGenie AI</p>
        <h2>Career OS</h2>
        <span>Plan, practice, and ship work that proves your growth.</span>
      </div>

      <nav className="sidebar-nav" aria-label="Primary">
        {items.map((item, index) => (
          <a
            key={item.label}
            href={item.target}
            className={index === 0 ? "is-active" : ""}
          >
            {item.label}
          </a>
        ))}
      </nav>
    </aside>
  );
}
