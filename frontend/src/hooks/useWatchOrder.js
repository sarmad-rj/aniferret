import { useEffect, useState } from "react";
import { fetchWatchOrder } from "../lib/api";

function useWatchOrder(franchiseSlug) {
  const [watchOrder, setWatchOrder] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!franchiseSlug) {
      return undefined;
    }

    let isMounted = true;
    setIsLoading(true);
    setError(null);

    fetchWatchOrder(franchiseSlug)
      .then((data) => {
        if (isMounted) {
          setWatchOrder(data);
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
  }, [franchiseSlug]);

  return { watchOrder, isLoading, error };
}

export default useWatchOrder;
