export default function Progress({ data }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Momentum</p>
          <h2>Progress overview</h2>
        </div>
      </div>

      <div className="progress-ring" aria-label={`Progress ${data.percent}%`}>
        <div className="progress-ring__value">{data.percent}%</div>
      </div>

      <div className="progress-stats">
        <article>
          <span>Completed steps</span>
          <strong>
            {data.completed}/{data.total}
          </strong>
        </article>
        <article>
          <span>Estimated hours</span>
          <strong>{data.hours}h</strong>
        </article>
        <article>
          <span>Saved plans</span>
          <strong>{data.totalPlans}</strong>
        </article>
        <article>
          <span>Chat history</span>
          <strong>{data.messages}</strong>
        </article>
        <article>
          <span>Best progress</span>
          <strong>{data.bestProgress}%</strong>
        </article>
        <article>
          <span>Focus score</span>
          <strong>{data.focusScore}%</strong>
        </article>
      </div>
    </section>
  );
}
