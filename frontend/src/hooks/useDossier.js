import { useEffect, useState } from "react";
import { fetchDossier } from "../lib/api";

function useDossier(animeSlug, checkpoint) {
  const [dossier, setDossier] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!animeSlug || !checkpoint) {
      return undefined;
    }

    let isMounted = true;
    setIsLoading(true);
    setError(null);

    fetchDossier(animeSlug, checkpoint)
      .then((data) => {
        if (isMounted) {
          setDossier(data);
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
  }, [animeSlug, checkpoint]);

  return { dossier, isLoading, error };
}

export default useDossier;
