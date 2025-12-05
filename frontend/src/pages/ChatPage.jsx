import { useState } from "react";
import { chatQuery } from "../api.js";
import ProductCard from "../components/ProductCard.jsx";
import FormattedMessage from "../components/FormattedMessage.jsx";

function ChatPage() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [recommended, setRecommended] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSend = async (e) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    const userMsg = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setError("");

    try {
      setLoading(true);
      const resp = await chatQuery(text, 8);
      const assistantMsgs = resp.messages || [];
      const lastAssistant = assistantMsgs[assistantMsgs.length - 1];
      if (lastAssistant) {
        setMessages((prev) => [...prev, { role: "assistant", content: lastAssistant.content }]);
      }
      setRecommended(resp.products || []);
    } catch (err) {
      console.error(err);
      setError("Something went wrong while talking to the assistant.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="chat-page">
      <header className="page-header">
        <div>
          <h1>Product Chat</h1>
          <p className="page-subtitle">
            Ask for outfits by activity or occasion (e.g. "gym and meetings", "travel and brunch").
          </p>
        </div>
      </header>

      <div className="chat-layout">
        <div className="chat-panel">
          <div className="chat-messages">
            {messages.length === 0 && (
              <p className="chat-placeholder">
                Start the conversation by typing what you're looking for below.
              </p>
            )}
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={
                  m.role === "user" ? "chat-bubble chat-bubble-user" : "chat-bubble chat-bubble-assistant"
                }
              >
                {m.role === "assistant" ? (
                  <FormattedMessage content={m.content} products={recommended} />
                ) : (
                  m.content
                )}
              </div>
            ))}
            {loading && <p className="chat-status">Thinking…</p>}
            {error && <p className="error-text">{error}</p>}
          </div>

          <form className="chat-input-row" onSubmit={handleSend}>
            <input
              type="text"
              placeholder="Describe what you're looking for…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
            <button type="submit" className="btn-primary" disabled={loading}>
              Send
            </button>
          </form>
        </div>

        <aside className="chat-recommendations">
          <h2>Recommended products</h2>
          {recommended.length === 0 && (
            <p className="chat-placeholder">
              When the assistant suggests items, they will appear here.
            </p>
          )}
          <div className="product-grid compact">
            {recommended.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </aside>
      </div>
    </section>
  );
}

export default ChatPage;


