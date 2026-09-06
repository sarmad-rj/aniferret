import { useCallback, useEffect, useState } from "react";
import { fetchProfile } from "../lib/api";

function useProfile(token) {
  const [profile, setProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const refetch = useCallback(() => {
    if (!token) {
      return Promise.resolve(null);
    }
    setIsLoading(true);
    setError(null);

    return fetchProfile(token)
      .then((data) => {
        setProfile(data);
        return data;
      })
      .catch((fetchError) => {
        setError(fetchError);
        throw fetchError;
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [token]);

  useEffect(() => {
    if (!token) {
      return undefined;
    }

    let isMounted = true;

    fetchProfile(token)
      .then((data) => {
        if (isMounted) {
          setProfile(data);
        }
      })
      .catch((fetchError) => {
        if (isMounted) {
          setError(fetchError);
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

  return { profile, isLoading, error, refetch };
}

export default useProfile;
