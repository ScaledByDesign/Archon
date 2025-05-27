import { useState, useEffect } from 'react';

/**
 * useFetch(url: string, deps?: any[]): { data, loading, error }
 */
export function useFetch(url, deps = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(url)
      .then(r => r.json())
      .then(json => !cancelled && setData(json))
      .catch(err => !cancelled && setError(err))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, deps);

  return { data, loading, error };
}
