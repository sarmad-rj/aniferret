import { useEffect, useRef, useState } from "react";
import { Send, Sparkles } from "lucide-react";
import { postQuery } from "../lib/api";
import ChatMessage from "./ChatMessage";

function LoreAssistant({ animeSlug, checkpoint }) {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [isSending, setIsSending] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    if (messages.length > 0) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || isSending) {
      return;
    }

    setMessages((previous) => [
      ...previous,
      { id: crypto.randomUUID(), role: "user", text: trimmedQuestion },
    ]);
    setQuestion("");
    setIsSending(true);

    try {
      const response = await postQuery({
        animeSlug,
        checkpoint,
        question: trimmedQuestion,
      });
      setMessages((previous) => [
        ...previous,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          text: response.answer,
          citations: response.citations,
          locked: response.locked,
        },
      ]);
    } catch {
      setMessages((previous) => [
        ...previous,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          text: "Something went wrong reaching the lore assistant.",
          citations: [],
          locked: false,
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <section className="flex h-[28rem] flex-col rounded-lg border border-[var(--border)] bg-[var(--surface)]">
      <header className="flex items-center gap-2 border-b border-[var(--border)] px-4 py-3">
        <Sparkles className="h-4 w-4 text-[var(--ferret)]" />
        <h2 className="text-sm font-semibold text-[var(--primary)]">
          Lore Assistant
        </h2>
      </header>

      <div className="flex-1 overflow-y-auto px-4 py-3">
        {messages.length === 0 ? (
          <p className="text-xs text-[var(--text-muted)]">
            Ask a question about the story so far. Answers respect your current
            watch progress.
          </p>
        ) : (
          <ul className="flex flex-col gap-3">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
          </ul>
        )}
        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={handleSubmit}
        className="flex items-center gap-2 border-t border-[var(--border)] p-3"
      >
        <input
          type="text"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask about the lore..."
          className="flex-1 rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)]"
        />
        <button
          type="submit"
          disabled={isSending}
          className="inline-flex items-center justify-center rounded-md bg-[var(--primary)] p-2 text-[var(--surface)] disabled:opacity-50"
          aria-label="Send question"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </section>
  );
}

export default LoreAssistant;
