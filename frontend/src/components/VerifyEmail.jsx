import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import { verifyEmail } from "../lib/api";
import { useAuth } from "../context/useAuth";

const REDIRECT_DELAY_MS = 1500;

function VerifyEmail() {
  const [status, setStatus] = useState("verifying");

  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { completeSession } = useAuth();

  useEffect(() => {
    let isMounted = true;
    const token = searchParams.get("token");
    if (!token) {
      setStatus("error");
      return undefined;
    }

    verifyEmail(token)
      .then(async (tokenResponse) => {
        await completeSession(tokenResponse);
        if (!isMounted) {
          return;
        }
        setStatus("success");
        setTimeout(
          () => navigate("/app", { replace: true }),
          REDIRECT_DELAY_MS,
        );
      })
      .catch(() => {
        if (isMounted) {
          setStatus("error");
        }
      });

    return () => {
      isMounted = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- runs once against the
    // token present at mount; searchParams/completeSession/navigate are stable
    // enough here that re-running on their identity changes isn't meaningful.
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--background)] p-4">
      <div className="w-full max-w-sm rounded-lg bg-[var(--surface)] p-6 text-center">
        {status === "verifying" && (
          <>
            <Loader2 className="mx-auto h-8 w-8 animate-spin text-[var(--primary)]" />
            <p className="mt-4 text-sm text-[var(--text-muted)]">
              Verifying your email...
            </p>
          </>
        )}

        {status === "success" && (
          <>
            <CheckCircle2 className="mx-auto h-8 w-8 text-[var(--sky)]" />
            <h1 className="mt-4 text-sm font-semibold text-[var(--primary)]">
              Email verified!
            </h1>
            <p className="mt-2 text-xs text-[var(--text-muted)]">
              Taking you into AniFerret...
            </p>
          </>
        )}

        {status === "error" && (
          <>
            <XCircle className="mx-auto h-8 w-8 text-[var(--pink)]" />
            <h1 className="mt-4 text-sm font-semibold text-[var(--primary)]">
              Verification link is invalid or expired
            </h1>
            <p className="mt-2 text-xs text-[var(--text-muted)]">
              Please sign in and request a new verification email.
            </p>
            <button
              type="button"
              onClick={() => navigate("/")}
              className="mt-4 rounded-md bg-[var(--primary)] px-4 py-2 text-sm font-medium text-[var(--surface)]"
            >
              Back to Login
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export default VerifyEmail;
