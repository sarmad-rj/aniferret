import { useCallback, useEffect, useState } from "react";
import { fetchAdminAnimeList } from "../lib/api";

function useAdminAnime(token) {
  const [animeList, setAnimeList] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const refetch = useCallback(() => {
    if (!token) {
      return Promise.resolve(null);
    }
    setIsLoading(true);
    setError(null);

    return fetchAdminAnimeList(token)
      .then((data) => {
        setAnimeList(data);
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

    fetchAdminAnimeList(token)
      .then((data) => {
        if (isMounted) {
          setAnimeList(data);
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

  return { animeList, isLoading, error, refetch };
}

export default useAdminAnime;
