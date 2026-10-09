import { lazy, Suspense } from "react";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
const AuthPage = lazy(() =>
  import("@/pages/auth-page").then((page) => ({ default: page.AuthPage })),
);
const FeedbackPage = lazy(() =>
  import("@/pages/feedback-page").then((page) => ({
    default: page.FeedbackPage,
  })),
);
const PageLoading = () => (
  <main className="flex min-h-svh items-center justify-center">
    <Skeleton className="h-36 w-80" aria-label="Loading page" />
  </main>
);

export const App = () => {
  const auth = useAuth();
  if (!auth.session)
    return (
      <Suspense fallback={<PageLoading />}>
        <AuthPage />
      </Suspense>
    );
  if (auth.identity.isPending && navigator.onLine)
    return (
      <main className="flex min-h-svh items-center justify-center">
        <Skeleton className="h-36 w-80" aria-label="Checking session" />
      </main>
    );
  if (auth.identity.error && navigator.onLine)
    return (
      <main className="mx-auto max-w-md p-6">
        <Alert variant="destructive">
          <AlertTitle>Cannot verify this session</AlertTitle>
          <AlertDescription>
            <p>{auth.identity.error.message}</p>
            <Button
              variant="outline"
              onClick={() => void auth.identity.refetch()}
            >
              Retry connection
            </Button>
            <Button
              variant="ghost"
              disabled={auth.signingOut}
              onClick={() => void auth.logout().catch(() => undefined)}
            >
              Sign out
            </Button>
          </AlertDescription>
        </Alert>
      </main>
    );
  return (
    <Suspense fallback={<PageLoading />}>
      <FeedbackPage
        key={auth.session.workspace_id}
        identity={auth.identity.data ?? auth.session}
        signingOut={auth.signingOut}
        onLogout={() => void auth.logout().catch(() => undefined)}
      />
    </Suspense>
  );
};
