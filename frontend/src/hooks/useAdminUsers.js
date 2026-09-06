import { useCallback, useEffect, useState } from "react";
import { fetchAdminUsers } from "../lib/api";

function useAdminUsers(token) {
  const [users, setUsers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const refetch = useCallback(() => {
    if (!token) {
      return Promise.resolve(null);
    }
    setIsLoading(true);
    setError(null);

    return fetchAdminUsers(token)
      .then((data) => {
        setUsers(data);
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

    fetchAdminUsers(token)
      .then((data) => {
        if (isMounted) {
          setUsers(data);
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

  return { users, isLoading, error, refetch };
}

export default useAdminUsers;
