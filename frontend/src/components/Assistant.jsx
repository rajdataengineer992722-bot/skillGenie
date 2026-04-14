import { useState } from "react";

const DEFAULT_QUICK_PROMPTS = [
  "Give me a 7-day study sprint for my current goal",
  "What project should I build first to stand out?",
  "Help me turn my roadmap into a daily schedule",
];

function parseCoachResponse(content) {
  const lines = String(content || "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  const sections = [];
  let current = null;

  for (const line of lines) {
    if (/^[A-Z ]+:$/.test(line)) {
      current = {
        id: `${sections.length}-${line}`,
        title: line.replace(":", "").trim(),
        items: [],
      };
      sections.push(current);
      continue;
    }

    if (current) {
      current.items.push(line.replace(/^-+\s*/, ""));
    }
  }

  return sections;
}

export default function Assistant({ sectionId, messages, loading, error, prompts, onSend }) {
  const [draft, setDraft] = useState("");
  const quickPrompts = prompts?.length ? prompts : DEFAULT_QUICK_PROMPTS;

  async function handleSubmit(event) {
    event.preventDefault();
    const message = draft;
    setDraft("");
    await onSend(message);
  }

  return (
    <section className="panel panel--assistant" id={sectionId}>
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Assistant</p>
          <h2>Ask for guidance</h2>
        </div>
      </div>

      <div className="message-list">
        {messages.map((message) => (
          <article
            key={message.id}
            className={`message-bubble message-bubble--${message.role}`}
          >
            <span>{message.role === "assistant" ? "AI" : "You"}</span>
            {message.role === "assistant" ? (
              (() => {
                const sections = parseCoachResponse(message.content);
                return sections.length ? (
                  <div className="coach-sections">
                    {sections.map((section) => (
                      <div key={section.id} className="coach-card">
                        <strong>{section.title}</strong>
                        {section.items.map((item) => (
                          <p key={item}>{item}</p>
                        ))}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="message-content">{message.content}</p>
                );
              })()
            ) : (
              <p className="message-content">{message.content}</p>
            )}
          </article>
        ))}
      </div>

      <div className="prompt-row">
        {quickPrompts.map((prompt) => (
          <button
            key={prompt}
            type="button"
            className="chip-button"
            onClick={() => setDraft(prompt)}
          >
            {prompt}
          </button>
        ))}
      </div>

      {error ? <p className="feedback feedback--error">{error}</p> : null}

      <form className="assistant-form" onSubmit={handleSubmit}>
        <textarea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Ask about projects, study order, interview prep, or weak areas..."
          rows={4}
        />
        <button type="submit" className="primary-button" disabled={loading}>
          {loading ? "Sending..." : "Send message"}
        </button>
      </form>
    </section>
  );
}
