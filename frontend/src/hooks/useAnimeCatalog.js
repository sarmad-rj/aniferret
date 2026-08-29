import { useCallback, useEffect, useState } from "react";
import { fetchAnimeList } from "../lib/api";

function useAnimeCatalog() {
  const [animeList, setAnimeList] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const refetch = useCallback(() => {
    setIsLoading(true);
    setError(null);

    return fetchAnimeList()
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
  }, []);

  useEffect(() => {
    let isMounted = true;

    fetchAnimeList()
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
  }, []);

  return { animeList, isLoading, error, refetch };
}

export default useAnimeCatalog;
