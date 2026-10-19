import {
  BrowserRouter,
  Navigate,
  Outlet,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";

import { useAuth, useOnline } from "@/hooks";
import { WorkspaceShell, PageLoading, PageMessage } from "@/components/layout";
import { Button } from "@/components/ui";

import { AuthPage } from "@/pages/auth";
import { FeedbackPage } from "@/pages/feedback";
import { DetailsPage } from "@/pages/feedback-details";
import { ActivityPage } from "@/pages/activity";

const Workspace = () => {
  const auth = useAuth();
  const online = useOnline();
  const location = useLocation();
  const navigate = useNavigate();

  if (!auth.session) {
    return (
      <Navigate
        to="/login"
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
          .finally(() => navigate("/login", { replace: true, state: null }))
      }
    >
      <Outlet />
    </WorkspaceShell>
  );
};

export const App = () => (
  <BrowserRouter>
    <Routes>
      <Route path="/login" element={<AuthPage />} />
      <Route path="/register" element={<AuthPage />} />
      <Route element={<Workspace />}>
        <Route index element={<Navigate to="/feedback" replace />} />
        <Route path="/feedback" element={<FeedbackPage />} />
        <Route path="/feedback/:id" element={<DetailsPage />} />
        <Route path="/activity" element={<ActivityPage />} />
        <Route
          path="*"
          element={
            <PageMessage
              title="Page not found"
              description="This page may have moved. Return to your inbox to continue."
              backTo="/feedback"
            />
          }
        />
      </Route>
    </Routes>
  </BrowserRouter>
);
