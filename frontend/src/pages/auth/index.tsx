import { useEffect } from "react";
import { ArrowRight, Check, MessageSquareText } from "lucide-react";
import { Navigate, useLocation } from "react-router-dom";

import { Path } from "@/router/paths";
import { useAuth } from "@/hooks";
import {
  Alert,
  AlertDescription,
  AlertTitle,
  Badge,
  Button,
  Separator,
} from "@/components/ui";

import { AuthForm } from "./auth-form";
import { getAuthDestination } from "./auth-redirect";
import { useAuthForm } from "./use-auth-form";

export const AuthPage = () => {
  const auth = useAuth();
  const location = useLocation();
  const register = location.pathname === Path.Register;
  const form = useAuthForm(register);
  const from = getAuthDestination(location.state);

  useEffect(() => {
    document.title = `${register ? "Create account" : "Sign in"} · Feedback Desk`;
  }, [register]);

  if (auth.session) {
    return (
      <Navigate
        to={register || auth.session.kind !== "account" ? Path.Feedback : from}
        replace
      />
    );
  }

  return (
    <main className="min-h-svh bg-background">
      <header className="mx-auto flex max-w-6xl items-center gap-3 px-6 py-7">
        <span className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <MessageSquareText className="size-5" />
        </span>
        <span className="font-semibold tracking-tight">Feedback Desk</span>
      </header>
      <div className="mx-auto grid max-w-6xl items-center gap-10 px-6 pb-12 pt-5 lg:min-h-[75svh] lg:grid-cols-2 lg:gap-20">
        <section className="flex flex-col items-start gap-6">
          <Badge variant="secondary">
            From customer message to clear insight
          </Badge>
          <h1 className="max-w-lg text-4xl font-semibold leading-tight tracking-tight lg:text-5xl">
            Find the issue.
            <br />
            Keep the context.
          </h1>
          <p className="max-w-md text-base leading-relaxed text-muted-foreground">
            Turn detailed customer messages into a concise summary and topic.
            Check the supporting quotes before deciding what needs attention.
          </p>
          <Button size="lg" onClick={form.openDemo} disabled={form.pending}>
            {form.demoPending ? "Opening your demo…" : "Try the demo"}
            <ArrowRight data-icon="inline-end" />
          </Button>
          <p className="text-sm text-muted-foreground">
            Sample feedback. No account needed.
          </p>
          {form.demoError && (
            <Alert variant="destructive">
              <AlertTitle>Couldn’t open demo</AlertTitle>
              <AlertDescription>{form.demoError}</AlertDescription>
            </Alert>
          )}
          <Separator className="max-w-md" />
          <ul className="flex flex-col gap-3 text-sm">
            {[
              "Start with an example or your own message",
              "Run AI analysis and follow its progress",
              "Verify the result against the original words",
            ].map(item => (
              <li key={item} className="flex items-center gap-3">
                <Check className="size-4 text-primary" />
                {item}
              </li>
            ))}
          </ul>
        </section>
        <div className="w-full max-w-md justify-self-center lg:justify-self-end">
          <AuthForm
            register={register}
            returnState={location.state}
            form={form}
          />
        </div>
      </div>
    </main>
  );
};
