import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { CheckCircle2, XCircle } from "lucide-react";
import { resetPassword } from "../lib/api";

const REDIRECT_DELAY_MS = 1800;

function ResetPassword() {
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [isDone, setIsDone] = useState(false);

  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token");

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (isSubmitting) {
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Passwords don't match.");
      return;
    }
    if (!token) {
      setError("This reset link is missing its token.");
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      await resetPassword(token, newPassword);
      setIsDone(true);
      setTimeout(() => navigate("/", { replace: true }), REDIRECT_DELAY_MS);
    } catch {
      setError("This reset link is invalid or has expired.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--background)] p-4">
      <div className="w-full max-w-sm rounded-lg bg-[var(--surface)] p-6">
        {isDone ? (
          <div className="text-center">
            <CheckCircle2 className="mx-auto h-8 w-8 text-[var(--sky)]" />
            <h1 className="mt-4 text-sm font-semibold text-[var(--primary)]">
              Password reset
            </h1>
            <p className="mt-2 text-xs text-[var(--text-muted)]">
              Taking you back to sign in...
            </p>
          </div>
        ) : (
          <>
            <h1 className="mb-4 text-sm font-semibold text-[var(--primary)]">
              Choose a new password
            </h1>

            {!token && (
              <div className="mb-4 flex items-center gap-2 rounded-md bg-[var(--pink-light)] p-3 text-xs text-[var(--primary)]">
                <XCircle className="h-4 w-4 shrink-0 text-[var(--pink)]" />
                This link is missing its reset token.
              </div>
            )}

            <form onSubmit={handleSubmit} className="flex flex-col gap-3">
              <input
                type="password"
                required
                minLength={8}
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
                placeholder="New password (min 8 characters)"
                disabled={isSubmitting}
                className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
              />
              <input
                type="password"
                required
                minLength={8}
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                placeholder="Confirm new password"
                disabled={isSubmitting}
                className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
              />

              {error && <p className="text-xs text-[var(--pink)]">{error}</p>}

              <button
                type="submit"
                disabled={isSubmitting || !token}
                className="mt-1 rounded-md bg-[var(--primary)] px-3 py-2 text-sm font-medium text-[var(--surface)] disabled:opacity-50"
              >
                {isSubmitting ? "Resetting..." : "Reset Password"}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}

export default ResetPassword;
