import { Navigate, Outlet, useLocation, useNavigate } from "react-router-dom";

import { useAuth, useOnline } from "@/hooks";
import { WorkspaceShell, PageLoading, PageMessage } from "@/components/layout";
import { Button } from "@/components/ui";

import { Path } from "./paths";

export const ProtectedWorkspace = () => {
  const auth = useAuth();
  const online = useOnline();
  const location = useLocation();
  const navigate = useNavigate();

  if (!auth.session) {
    return (
      <Navigate
        to={Path.Login}
        state={{ from: location.pathname + location.search }}
        replace
      />
    );
  }

  if (auth.identity.isPending && online) {
    return <PageLoading label="Opening your workspace" />;
  }

  if (auth.identity.error && online) {
    return (
      <PageMessage
        title="We couldn’t open your workspace"
        description="Check your connection and try again."
      >
        <Button onClick={() => void auth.identity.refetch()}>Try again</Button>
        <Button
          variant="outline"
          disabled={auth.signingOut}
          onClick={() => void auth.logout().catch(() => undefined)}
        >
          Sign out
        </Button>
      </PageMessage>
    );
  }

  return (
    <WorkspaceShell
      key={auth.session.workspace_id}
      identity={auth.identity.data ?? auth.session}
      signingOut={auth.signingOut}
      onLogout={() =>
        void auth
          .logout()
          .catch(() => undefined)
          .finally(() => navigate(Path.Login, { replace: true, state: null }))
      }
    >
      <Outlet />
    </WorkspaceShell>
  );
};
