export default function Recommendations({ items }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Focus areas</p>
          <h2>Recommended next moves</h2>
        </div>
      </div>

      <div className="recommendation-grid">
        {items.map((item) => (
          <article key={item.id} className="recommendation-card">
            <strong>{item.title}</strong>
            <p>{item.description}</p>
            {item.meta ? <span className="recommendation-meta">{item.meta}</span> : null}
            {item.action ? <p className="recommendation-action">{item.action}</p> : null}
          </article>
        ))}
      </div>
    </section>
  );
}
