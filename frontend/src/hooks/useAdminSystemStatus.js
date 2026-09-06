import { useEffect, useState } from "react";
import { fetchAdminSystemStatus } from "../lib/api";

function useAdminSystemStatus(token) {
  const [status, setStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!token) {
      return undefined;
    }

    let isMounted = true;

    fetchAdminSystemStatus(token)
      .then((data) => {
        if (isMounted) {
          setStatus(data);
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

  return { status, isLoading, error };
}

export default useAdminSystemStatus;
