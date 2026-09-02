import { useEffect, useState } from "react";
import {
  fetchCurrentUser,
  loginUser,
  registerUser,
  saveWatchProgress,
} from "../lib/api";
import { clearGuestProgress, getAllGuestProgress } from "../lib/guestProgress";
import { AuthContext } from "./authContext";

const TOKEN_STORAGE_KEY = "aniferret_token";

function readStoredToken() {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

function writeStoredToken(token) {
  try {
    if (token) {
      localStorage.setItem(TOKEN_STORAGE_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
    }
  } catch {
    // Storage unavailable — the session just won't survive a refresh.
  }
}

async function syncGuestProgressToAccount(token) {
  const entries = getAllGuestProgress();
  if (entries.length === 0) {
    return;
  }
  try {
    await saveWatchProgress(token, entries);
    clearGuestProgress();
  } catch {
    // Non-fatal: the guest progress just stays in localStorage, unsynced, and the
    // user is still successfully logged in either way.
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(readStoredToken);
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      return;
    }
    let isMounted = true;
    fetchCurrentUser(token)
      .then((fetchedUser) => {
        if (isMounted) {
          setUser(fetchedUser);
        }
      })
      .catch(() => {
        if (isMounted) {
          writeStoredToken(null);
          setToken(null);
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
        }
      });
    return () => {
      isMounted = false;
    };
  }, [token]);

  const applySession = async (tokenResponse) => {
    writeStoredToken(tokenResponse.access_token);
    setToken(tokenResponse.access_token);
    setUser(tokenResponse.user);
    await syncGuestProgressToAccount(tokenResponse.access_token);
  };

  const login = async (email, password) => {
    const tokenResponse = await loginUser({ email, password });
    await applySession(tokenResponse);
  };

  const register = async (email, password, displayName) => {
    const tokenResponse = await registerUser({ email, password, displayName });
    await applySession(tokenResponse);
  };

  const logout = () => {
    writeStoredToken(null);
    setToken(null);
    setUser(null);
  };

  const value = {
    user,
    token,
    isAuthenticated: Boolean(user),
    isLoading,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
