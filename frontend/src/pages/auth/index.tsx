import { useEffect, useState, type FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, Check, MessageSquareText } from "lucide-react";
import { Link, Navigate, useLocation } from "react-router-dom";

import {
  authenticate,
  baseUrl,
  clearPrivateStorage,
  resetPreview,
} from "@/api";
import { useAuth } from "@/hooks";
import {
  Alert,
  AlertDescription,
  AlertTitle,
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
  Input,
  Separator,
} from "@/components/ui";

export const AuthPage = () => {
  const client = useQueryClient();
  const auth = useAuth();
  const location = useLocation();
  const register = location.pathname === "/register";
  const mode = register ? "register" : "login";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const state: unknown = location.state;
  const from =
    state &&
    typeof state === "object" &&
    "from" in state &&
    typeof state.from === "string" &&
    /^\/(feedback(?:\/|\?|$)|activity(?:\?|$))/.test(state.from)
      ? state.from
      : "/feedback";

  const mutation = useMutation({
    mutationFn: async (action: "demo" | "login" | "register") => {
      await client.cancelQueries();
      client.clear();
      clearPrivateStorage();

      if (action === "demo") resetPreview();

      return authenticate(
        action,
        action === "demo"
          ? undefined
          : { email: email.trim().toLowerCase(), password }
      );
    },
  });

  useEffect(() => {
    document.title = `${register ? "Create account" : "Sign in"} · Feedback Desk`;
  }, [register]);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!mutation.isPending) mutation.mutate(mode);
  };

  if (auth.session)
    return (
      <Navigate
        to={register || auth.session.kind !== "account" ? "/feedback" : from}
        replace
      />
    );

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
          <Badge variant="secondary">Customer feedback, in one place</Badge>
          <h1 className="max-w-lg text-4xl font-semibold leading-tight tracking-tight lg:text-5xl">
            Less noise.
            <br />
            Clearer feedback.
          </h1>
          <p className="max-w-md text-base leading-relaxed text-muted-foreground">
            Collect customer messages, find what matters, and keep the original
            context close.
          </p>
          <Button
            size="lg"
            onClick={() => mutation.mutate("demo")}
            disabled={mutation.isPending}
          >
            {mutation.isPending && mutation.variables === "demo"
              ? "Opening your demo…"
              : "Try the demo"}
            <ArrowRight data-icon="inline-end" />
          </Button>
          <p className="text-sm text-muted-foreground">
            Sample feedback. No account needed.
          </p>
          {mutation.error && mutation.variables === "demo" && (
            <Alert variant="destructive">
              <AlertTitle>Couldn’t open demo</AlertTitle>
              <AlertDescription>{mutation.error.message}</AlertDescription>
            </Alert>
          )}
          <Separator className="max-w-md" />
          <ul className="flex flex-col gap-3 text-sm">
            {[
              "Add a customer message",
              "Browse by topic",
              "Read the summary alongside the source",
            ].map(item => (
              <li key={item} className="flex items-center gap-3">
                <Check className="size-4 text-primary" />
                {item}
              </li>
            ))}
          </ul>
        </section>
        <div className="w-full max-w-md justify-self-center lg:justify-self-end">
          <Card>
            <CardHeader>
              <CardTitle className="text-xl">
                {register ? "Create your workspace" : "Welcome back"}
              </CardTitle>
              <CardDescription>
                {register
                  ? "Start collecting feedback with your own account."
                  : "Sign in to your Feedback Desk workspace."}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={submit} className="flex flex-col gap-5">
                <FieldGroup>
                  <Field>
                    <FieldLabel htmlFor="email">Email</FieldLabel>
                    <Input
                      id="email"
                      type="email"
                      autoComplete="email"
                      placeholder="you@company.com"
                      value={email}
                      onChange={event => setEmail(event.target.value)}
                      required
                      maxLength={254}
                      disabled={!baseUrl || mutation.isPending}
                    />
                  </Field>
                  <Field>
                    <FieldLabel htmlFor="password">Password</FieldLabel>
                    <Input
                      id="password"
                      type="password"
                      autoComplete={
                        register ? "new-password" : "current-password"
                      }
                      value={password}
                      onChange={event => setPassword(event.target.value)}
                      required
                      minLength={register ? 10 : undefined}
                      maxLength={128}
                      disabled={!baseUrl || mutation.isPending}
                    />
                    {register && (
                      <FieldDescription>
                        Use at least 10 characters.
                      </FieldDescription>
                    )}
                  </Field>
                </FieldGroup>
                <Button type="submit" disabled={!baseUrl || mutation.isPending}>
                  {mutation.isPending && mutation.variables !== "demo"
                    ? "Please wait…"
                    : register
                      ? "Create account"
                      : "Sign in"}
                  <ArrowRight data-icon="inline-end" />
                </Button>
                {!baseUrl && (
                  <p className="text-sm text-muted-foreground">
                    This preview uses the demo. Account access is available in
                    the connected app.
                  </p>
                )}
                {mutation.error && mutation.variables !== "demo" && (
                  <Alert variant="destructive">
                    <AlertTitle>Couldn’t continue</AlertTitle>
                    <AlertDescription>
                      {mutation.error.message}
                    </AlertDescription>
                  </Alert>
                )}
              </form>
            </CardContent>
            <CardFooter className="justify-center">
              <p className="text-sm text-muted-foreground">
                {register
                  ? "Already have an account? "
                  : "New to Feedback Desk? "}
                <Link
                  className="font-medium text-primary underline-offset-4 hover:underline"
                  to={register ? "/login" : "/register"}
                  state={location.state}
                  aria-disabled={mutation.isPending}
                  onClick={event => {
                    if (mutation.isPending) {
                      event.preventDefault();
                      return;
                    }
                    mutation.reset();
                    setPassword("");
                  }}
                >
                  {register ? "Sign in" : "Create account"}
                </Link>
              </p>
            </CardFooter>
          </Card>
        </div>
      </div>
    </main>
  );
};
