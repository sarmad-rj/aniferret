import { useState } from "react";
import { Eye, EyeOff, LogIn, MailCheck, UserPlus, X } from "lucide-react";
import useBodyScrollLock from "../hooks/useBodyScrollLock";
import { useAuth } from "../context/useAuth";
import { forgotPassword, resendVerificationEmail } from "../lib/api";

const UNVERIFIED_ERROR_MESSAGE =
  "Please verify your email address before logging in.";

function PasswordInput({ value, onChange, placeholder, disabled }) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div className="relative">
      <input
        type={isVisible ? "text" : "password"}
        required
        minLength={8}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        disabled={disabled}
        className="w-full rounded-md border border-[var(--border)] px-3 py-2 pr-10 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
      />
      <button
        type="button"
        onClick={() => setIsVisible((previous) => !previous)}
        disabled={disabled}
        aria-label={isVisible ? "Hide password" : "Show password"}
        className="absolute right-2 top-1/2 -translate-y-1/2 text-[var(--text-muted)] disabled:opacity-50"
      >
        {isVisible ? (
          <EyeOff className="h-4 w-4" />
        ) : (
          <Eye className="h-4 w-4" />
        )}
      </button>
    </div>
  );
}

function AuthModal({ onClose, onAuthenticated, contextMessage }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [isUnverifiedError, setIsUnverifiedError] = useState(false);
  const [registeredMessage, setRegisteredMessage] = useState(null);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [forgotPasswordEmail, setForgotPasswordEmail] = useState("");
  const [forgotPasswordSent, setForgotPasswordSent] = useState(false);
  const [resendStatus, setResendStatus] = useState(null);

  const { login, register } = useAuth();

  useBodyScrollLock();

  const resetTransientState = () => {
    setError(null);
    setIsUnverifiedError(false);
    setResendStatus(null);
  };

  const handleModeChange = (nextMode) => {
    setMode(nextMode);
    resetTransientState();
    setShowForgotPassword(false);
    setForgotPasswordSent(false);
    setConfirmPassword("");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (isSubmitting) {
      return;
    }

    resetTransientState();

    if (mode === "register" && password !== confirmPassword) {
      setError("Passwords don't match.");
      return;
    }

    setIsSubmitting(true);

    try {
      if (mode === "login") {
        await login(email, password);
        onAuthenticated?.();
        onClose();
      } else {
        const response = await register(
          email,
          password,
          displayName.trim() || undefined,
        );
        setRegisteredMessage(response.message);
      }
    } catch (submitError) {
      if (mode === "login") {
        if (submitError.status === 403) {
          setIsUnverifiedError(true);
          setError(UNVERIFIED_ERROR_MESSAGE);
        } else {
          // Deliberately generic — never reveals whether the email is registered,
          // matching auth_service.InvalidCredentialsError's own reasoning. Don't
          // split this one the way register's error is split below.
          setError("Invalid email or password.");
        }
      } else if (submitError.status === 409) {
        setError("That email is already registered. Try signing in instead.");
      } else if (submitError.status === 422) {
        setError("Password must be at least 8 characters.");
      } else {
        setError(
          "Something went wrong creating that account. Please try again.",
        );
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleForgotPasswordSubmit = async (event) => {
    event.preventDefault();
    if (isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    try {
      await forgotPassword(forgotPasswordEmail);
      setForgotPasswordSent(true);
    } catch {
      // forgot-password always responds 200 regardless of outcome (enumeration
      // safety) — a thrown error here means the request itself failed (network,
      // 5xx), not that the email is unknown.
      setError("Something went wrong sending that link. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResendVerification = async () => {
    if (resendStatus === "sending") {
      return;
    }
    setResendStatus("sending");
    try {
      await resendVerificationEmail(email);
      setResendStatus("sent");
    } catch {
      setResendStatus("error");
    }
  };

  if (registeredMessage) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-[var(--primary)]/40 p-4">
        <div className="w-full max-w-md rounded-lg bg-[var(--surface)] p-6 text-center">
          <button
            type="button"
            onClick={onClose}
            aria-label="Close sign in"
            className="float-right"
          >
            <X className="h-4 w-4 text-[var(--text-muted)]" />
          </button>
          <MailCheck className="mx-auto h-10 w-10 text-[var(--ferret)]" />
          <h2 className="mt-4 text-sm font-semibold text-[var(--primary)]">
            Check your inbox
          </h2>
          <p className="mt-2 text-xs text-[var(--text-muted)]">
            {registeredMessage}
          </p>
          <p className="mt-1 text-xs text-[var(--text-muted)]">
            Verification link sent to your email. Please click the link to
            activate your account.
          </p>
          <button
            type="button"
            onClick={handleResendVerification}
            disabled={resendStatus === "sending"}
            className="mt-4 text-xs font-medium text-[var(--primary)] underline disabled:opacity-50"
          >
            {resendStatus === "sending"
              ? "Sending..."
              : resendStatus === "sent"
                ? "Sent — check your inbox"
                : resendStatus === "error"
                  ? "Something went wrong — try again"
                  : "Didn't get it? Resend verification email"}
          </button>
        </div>
      </div>
    );
  }

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

        {showForgotPassword ? (
          <div>
            <h3 className="mb-3 text-xs font-semibold text-[var(--primary)]">
              Reset your password
            </h3>

            {forgotPasswordSent ? (
              <p className="rounded-md bg-[var(--pink-light)] p-3 text-xs text-[var(--primary)]">
                If an account exists for that email, a reset link has been sent.
              </p>
            ) : (
              <form
                onSubmit={handleForgotPasswordSubmit}
                className="flex flex-col gap-3"
              >
                <input
                  type="email"
                  required
                  value={forgotPasswordEmail}
                  onChange={(event) =>
                    setForgotPasswordEmail(event.target.value)
                  }
                  placeholder="Email"
                  disabled={isSubmitting}
                  className="rounded-md border border-[var(--border)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--primary)] disabled:opacity-50"
                />
                {error && <p className="text-xs text-[var(--pink)]">{error}</p>}
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="rounded-md bg-[var(--primary)] px-3 py-2 text-sm font-medium text-[var(--surface)] disabled:opacity-50"
                >
                  {isSubmitting ? "Sending..." : "Send Reset Link"}
                </button>
              </form>
            )}

            <button
              type="button"
              onClick={() => {
                setShowForgotPassword(false);
                setForgotPasswordSent(false);
                resetTransientState();
              }}
              className="mt-3 text-xs text-[var(--text-muted)] underline"
            >
              Back to login
            </button>
          </div>
        ) : (
          <>
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

              <PasswordInput
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Password (min 8 characters)"
                disabled={isSubmitting}
              />

              {mode === "register" && (
                <PasswordInput
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  placeholder="Confirm password"
                  disabled={isSubmitting}
                />
              )}

              {mode === "login" && (
                <button
                  type="button"
                  onClick={() => {
                    setShowForgotPassword(true);
                    setForgotPasswordEmail(email);
                    resetTransientState();
                  }}
                  className="self-end text-xs text-[var(--text-muted)] underline"
                >
                  Forgot password?
                </button>
              )}

              {error &&
                (isUnverifiedError ? (
                  <div className="rounded-md bg-[var(--pink-light)] p-3">
                    <p className="text-xs text-[var(--primary)]">{error}</p>
                    <button
                      type="button"
                      onClick={handleResendVerification}
                      disabled={resendStatus === "sending"}
                      className="mt-1 text-xs font-medium text-[var(--primary)] underline disabled:opacity-50"
                    >
                      {resendStatus === "sending"
                        ? "Sending..."
                        : resendStatus === "sent"
                          ? "Sent — check your inbox"
                          : resendStatus === "error"
                            ? "Something went wrong — try again"
                            : "Resend verification email"}
                    </button>
                  </div>
                ) : (
                  <p className="text-xs text-[var(--pink)]">{error}</p>
                ))}

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
          </>
        )}
      </div>
    </div>
  );
}

export default AuthModal;
