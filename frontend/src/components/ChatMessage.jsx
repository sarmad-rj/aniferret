import { Lock } from "lucide-react";

function ChatMessage({ message }) {
  const isUser = message.role === "user";

  return (
    <li className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
          isUser
            ? "bg-[var(--primary)] text-[var(--surface)]"
            : "bg-[var(--surface-warm)] text-[var(--text)]"
        }`}
      >
        <p>{message.text}</p>

        {!isUser && message.locked && (
          <span className="mt-2 inline-flex items-center gap-1 rounded-full bg-[var(--pink-light)] px-2.5 py-1 text-xs font-medium text-[var(--primary)]">
            <Lock className="h-3 w-3 text-[var(--pink)]" />
            Locked at current progress
          </span>
        )}

        {!isUser && message.citations?.length > 0 && (
          <ul className="mt-2 flex flex-wrap gap-1.5">
            {message.citations.map((citation) => (
              <li
                key={citation}
                className="rounded-full bg-[var(--sky)] px-2.5 py-1 text-xs text-[var(--primary)]"
              >
                {citation}
              </li>
            ))}
          </ul>
        )}
      </div>
    </li>
  );
}

export default ChatMessage;
