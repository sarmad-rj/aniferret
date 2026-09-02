import { useState } from "react";
import { LogIn, UserPlus, X } from "lucide-react";
import useBodyScrollLock from "../hooks/useBodyScrollLock";
import { useAuth } from "../context/useAuth";

function AuthModal({ onClose, onAuthenticated, contextMessage }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const { login, register } = useAuth();

  useBodyScrollLock();

  const handleModeChange = (nextMode) => {
    setMode(nextMode);
    setError(null);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (isSubmitting) {
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(email, password, displayName.trim() || undefined);
      }
      onAuthenticated?.();
      onClose();
    } catch {
      setError(
        mode === "login"
          ? "Invalid email or password."
          : "Could not create that account — the email may already be registered, or the password needs to be at least 8 characters.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[var(--primary)]/40 p-4">
      <div className="w-full max-w-md rounded-lg bg-[var(--surface)] p-5">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {mode === "login" ? (
              <LogIn className="h-4 w-4 text-[var(--ferret)]" />
            ) : (
              <UserPlus className="h-4 w-4 text-[var(--ferret)]" />
            )}
            <h2 className="text-sm font-semibold text-[var(--primary)]">
              Sign In
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            aria-label="Close sign in"
          >
            <X className="h-4 w-4 text-[var(--text-muted)]" />
          </button>
        </div>

        {contextMessage && (
          <p className="mb-4 rounded-md bg-[var(--pink-light)] p-3 text-xs text-[var(--primary)]">
            {contextMessage}
          </p>
        )}

        <div className="mb-4 flex rounded-md border border-[var(--border)] p-1">
          <button
            type="button"
            onClick={() => handleModeChange("login")}
            className={`flex-1 rounded-md px-3 py-1.5 text-xs font-medium ${
              mode === "login"
                ? "bg-[var(--primary)] text-[var(--surface)]"
                : "text-[var(--text-muted)]"
            }`}
          >
            Login
          </button>
          <button
            type="button"
            onClick={() => handleModeChange("register")}
            className={`flex-1 rounded-md px-3 py-1.5 text-xs font-medium ${
              mode === "register"
                ? "bg-[var(--primary)] text-[var(--surface)]"
                : "text-[var(--text-muted)]"
            }`}
          >
            Register
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          {mode === "register" && (
            <input
              type="text"
              value={displayName}
              onChange={(event) => setDisplayName(event.target.value)}
              placeholder="Display name (optional)"
              disabled={isSubmitting}
              className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
            />
          )}

          <input
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="Email"
            disabled={isSubmitting}
            className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
          />

          <input
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Password (min 8 characters)"
            disabled={isSubmitting}
            className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
          />

          {error && <p className="text-xs text-[var(--pink)]">{error}</p>}

          <button
            type="submit"
            disabled={isSubmitting}
            className="mt-1 rounded-md bg-[var(--primary)] px-3 py-2 text-sm font-medium text-[var(--surface)] disabled:opacity-50"
          >
            {isSubmitting
              ? mode === "login"
                ? "Signing in..."
                : "Creating account..."
              : mode === "login"
                ? "Sign In"
                : "Create Account"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default AuthModal;
