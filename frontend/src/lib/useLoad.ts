import { useCallback, useEffect, useState } from "react";

/** Loads data on mount; `reload` fetches again and `setData` applies a local update. */
export function useLoad<T>(load: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await load());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
    // Loaders are module-level api calls, so they never change between renders.
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { data, error, loading, reload, setData };
}
