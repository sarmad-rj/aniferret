import { useCallback, useEffect, useState } from "react";
import { fetchAdminAnimeFactions } from "../lib/api";

function useAdminFactions(token, animeId) {
  const [factions, setFactions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const refetch = useCallback(() => {
    if (!token || !animeId) {
      return Promise.resolve(null);
    }
    setIsLoading(true);
    setError(null);

    return fetchAdminAnimeFactions(token, animeId)
      .then((data) => {
        setFactions(data);
        return data;
      })
      .catch((fetchError) => {
        setError(fetchError);
        throw fetchError;
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [token, animeId]);

  useEffect(() => {
    if (!token || !animeId) {
      return undefined;
    }

    let isMounted = true;

    fetchAdminAnimeFactions(token, animeId)
      .then((data) => {
        if (isMounted) {
          setFactions(data);
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
  }, [token, animeId]);

  return { factions, isLoading, error, refetch };
}

export default useAdminFactions;
