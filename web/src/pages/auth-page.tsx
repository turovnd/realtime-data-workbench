import { useState, type FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { MessageSquareText, ArrowRight } from "lucide-react";
import { authenticate, baseUrl, clearPrivateStorage } from "@/lib/api/auth";
import { resetPreview } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import {
  Field,
  FieldGroup,
  FieldLabel,
  FieldDescription,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
export const AuthPage = () => {
  const client = useQueryClient();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
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
          : {
              email: email.trim().toLowerCase(),
              password,
            },
      );
    },
  });
  const submit = (event: FormEvent) => {
    event.preventDefault();
    mutation.mutate(mode);
  };
  return (
    <main className="flex min-h-svh items-center justify-center p-6">
      <div className="flex w-full max-w-sm flex-col gap-6">
        <div className="flex items-center justify-center gap-2">
          <MessageSquareText className="size-5" />
          <span className="font-semibold">Feedback Desk</span>
        </div>
        <Card>
          <CardHeader>
            <CardTitle>Find recurring product issues.</CardTitle>
            <CardDescription>
              Organize customer feedback by topic, inspect the original messages
              and compare updated results.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-5">
            <Tabs
              value={mode}
              onValueChange={(value) => {
                if (value === "login" || value === "register") {
                  setMode(value);
                  mutation.reset();
                  setPassword("");
                }
              }}
            >
              <TabsList className="w-full">
                <TabsTrigger
                  value="login"
                  className="flex-1"
                  disabled={mutation.isPending}
                >
                  Sign in
                </TabsTrigger>
                <TabsTrigger
                  value="register"
                  className="flex-1"
                  disabled={mutation.isPending}
                >
                  Create account
                </TabsTrigger>
              </TabsList>
            </Tabs>
            {!baseUrl && (
              <Alert>
                <AlertTitle>Browser preview</AlertTitle>
                <AlertDescription>
                  Try the isolated demo below. Account sign-in becomes available
                  when this UI is connected to its API.
                </AlertDescription>
              </Alert>
            )}
            <form onSubmit={submit}>
              <FieldGroup>
                <Field>
                  <FieldLabel htmlFor="email">Email</FieldLabel>
                  <Input
                    id="email"
                    type="email"
                    autoComplete="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
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
                      mode === "register" ? "new-password" : "current-password"
                    }
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    required
                    minLength={12}
                    maxLength={128}
                    disabled={!baseUrl || mutation.isPending}
                  />
                  <FieldDescription>
                    Use 12–128 characters. This account is only for Feedback
                    Desk.
                  </FieldDescription>
                </Field>
                <Button type="submit" disabled={!baseUrl || mutation.isPending}>
                  {mutation.isPending
                    ? "Please wait…"
                    : mode === "login"
                      ? "Sign in"
                      : "Create account"}
                </Button>
              </FieldGroup>
            </form>
            {mutation.error && (
              <Alert variant="destructive">
                <AlertTitle>Unable to continue</AlertTitle>
                <AlertDescription>{mutation.error.message}</AlertDescription>
              </Alert>
            )}
            <Separator />
            <Button
              variant="outline"
              disabled={mutation.isPending}
              onClick={() => mutation.mutate("demo")}
            >
              Try an isolated demo <ArrowRight data-icon="inline-end" />
            </Button>
          </CardContent>
          <CardFooter>
            <p className="text-xs text-muted-foreground">
              Synthetic data only. Demo access is separate from your account.
            </p>
          </CardFooter>
        </Card>
      </div>
    </main>
  );
};
