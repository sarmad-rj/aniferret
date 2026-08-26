import { useEffect, useState } from "react";
import { fetchAnimeList } from "../lib/api";

function useAnimeCatalog() {
  const [animeList, setAnimeList] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);

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

  return { animeList, isLoading, error };
}

export default useAnimeCatalog;
