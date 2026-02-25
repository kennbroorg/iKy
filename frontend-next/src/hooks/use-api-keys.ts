import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchApiKeys, writeApiKeys } from "@/lib/api-client";
import { useApiKeyStore } from "@/stores/apikey-store";
import type { ApiKey } from "@/types/api";

export function useApiKeys() {
  const queryClient = useQueryClient();
  const { setKeys, setLoading } = useApiKeyStore();

  const query = useQuery({
    queryKey: ["apikeys"],
    queryFn: async () => {
      setLoading(true);
      try {
        const res = await fetchApiKeys();
        setKeys(res.keys);
        return res.keys;
      } finally {
        setLoading(false);
      }
    },
  });

  const mutation = useMutation({
    mutationFn: (keys: ApiKey[]) => writeApiKeys(keys),
    onSuccess: (data) => {
      setKeys(data.keys);
      queryClient.invalidateQueries({ queryKey: ["apikeys"] });
    },
  });

  return { query, save: mutation.mutate, isSaving: mutation.isPending };
}
