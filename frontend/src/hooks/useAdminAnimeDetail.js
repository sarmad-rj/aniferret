import { useCallback, useEffect, useState } from "react";
import { fetchAdminAnimeDetail } from "../lib/api";

function useAdminAnimeDetail(token, animeId) {
  const [anime, setAnime] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const refetch = useCallback(() => {
    if (!token || !animeId) {
      return Promise.resolve(null);
    }
    setIsLoading(true);
    setError(null);

    return fetchAdminAnimeDetail(token, animeId)
      .then((data) => {
        setAnime(data);
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

    fetchAdminAnimeDetail(token, animeId)
      .then((data) => {
        if (isMounted) {
          setAnime(data);
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

  return { anime, isLoading, error, refetch };
}

export default useAdminAnimeDetail;
