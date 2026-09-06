import { useCallback, useEffect, useState } from "react";
import { fetchAdminAnimeCharacters } from "../lib/api";

function useAdminCharacters(token, animeId) {
  const [characters, setCharacters] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const refetch = useCallback(() => {
    if (!token || !animeId) {
      return Promise.resolve(null);
    }
    setIsLoading(true);
    setError(null);

    return fetchAdminAnimeCharacters(token, animeId)
      .then((data) => {
        setCharacters(data);
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

    fetchAdminAnimeCharacters(token, animeId)
      .then((data) => {
        if (isMounted) {
          setCharacters(data);
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

  return { characters, isLoading, error, refetch };
}

export default useAdminCharacters;
