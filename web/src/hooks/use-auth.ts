import { useSyncExternalStore } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getSession,
  subscribeAuth,
  loadIdentity,
  revokeSession,
  clearPrivateStorage,
} from "@/lib/api/auth";
export const useAuth = () => {
  const session = useSyncExternalStore(subscribeAuth, getSession);
  const client = useQueryClient();
  const identity = useQuery({
    queryKey: ["identity", session?.workspace_id],
    queryFn: ({ signal }) => loadIdentity(signal),
    enabled: !!session && navigator.onLine,
    staleTime: 30000,
    retry: false,
  });
  const logoutMutation = useMutation({
    mutationFn: async () => {
      const token = getSession()?.token;
      await client.cancelQueries();
      try {
        await revokeSession();
      } finally {
        if (!getSession() || getSession()?.token === token) {
          client.clear();
          clearPrivateStorage();
        }
      }
    },
  });
  return {
    session,
    identity,
    logout: logoutMutation.mutateAsync,
    signingOut: logoutMutation.isPending,
  };
};
