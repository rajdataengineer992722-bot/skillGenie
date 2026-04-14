export default function StatsCards({ stats }) {
  return (
    <section className="stats-grid">
      {stats.map((stat) => (
        <article key={stat.label} className={`stat-card stat-card--${stat.tone}`}>
          <p>{stat.label}</p>
          <strong>{stat.value}</strong>
        </article>
      ))}
    </section>
  );
}
