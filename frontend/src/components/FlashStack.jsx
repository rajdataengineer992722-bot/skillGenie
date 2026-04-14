export default function FlashStack({ items, onDismiss }) {
  if (!items.length) {
    return null;
  }

  return (
    <div className="flash-stack" aria-live="polite" aria-atomic="true">
      {items.map((item) => (
        <article
          key={item.id}
          className={`flash-card flash-card--${item.tone || "info"}`}
        >
          <div>
            {item.title ? <strong>{item.title}</strong> : null}
            <p>{item.message}</p>
          </div>
          <button
            type="button"
            className="flash-dismiss"
            onClick={() => onDismiss(item.id)}
            aria-label="Dismiss notification"
          >
            x
          </button>
        </article>
      ))}
    </div>
  );
}
