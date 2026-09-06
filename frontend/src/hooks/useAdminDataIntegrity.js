import { useCallback, useEffect, useState } from "react";
import { fetchAdminDataIntegrityReport } from "../lib/api";

function useAdminDataIntegrity(token) {
  const [report, setReport] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const refetch = useCallback(() => {
    if (!token) {
      return Promise.resolve(null);
    }
    setIsLoading(true);
    setError(null);

    return fetchAdminDataIntegrityReport(token)
      .then((data) => {
        setReport(data);
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

    fetchAdminDataIntegrityReport(token)
      .then((data) => {
        if (isMounted) {
          setReport(data);
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

  return { report, isLoading, error, refetch };
}

export default useAdminDataIntegrity;
