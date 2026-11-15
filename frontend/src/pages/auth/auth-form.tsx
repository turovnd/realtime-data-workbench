import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

import { Path } from "@/router/paths";
import { baseUrl } from "@/api";
import {
  Alert,
  AlertDescription,
  AlertTitle,
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
} from "@/components/ui";

import type { AuthFormState } from "./use-auth-form";

type Props = {
  register: boolean;
  returnState: unknown;
  form: AuthFormState;
};

export const AuthForm = ({ register, returnState, form }: Props) => (
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
      <form onSubmit={form.submit} className="flex flex-col gap-5">
        <FieldGroup>
          <Field>
            <FieldLabel htmlFor="email">Email</FieldLabel>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="you@company.com"
              value={form.email}
              onChange={event => form.setEmail(event.target.value)}
              required
              maxLength={254}
              disabled={!baseUrl || form.pending}
            />
          </Field>
          <Field>
            <FieldLabel htmlFor="password">Password</FieldLabel>
            <Input
              id="password"
              type="password"
              autoComplete={register ? "new-password" : "current-password"}
              value={form.password}
              onChange={event => form.setPassword(event.target.value)}
              required
              minLength={register ? 10 : undefined}
              maxLength={128}
              disabled={!baseUrl || form.pending}
            />
            {register && (
              <FieldDescription>Use at least 10 characters.</FieldDescription>
            )}
          </Field>
        </FieldGroup>
        <Button type="submit" disabled={!baseUrl || form.pending}>
          {form.accountPending
            ? "Please wait…"
            : register
              ? "Create account"
              : "Sign in"}
          <ArrowRight data-icon="inline-end" />
        </Button>
        {!baseUrl && (
          <p className="text-sm text-muted-foreground">
            This preview uses the demo. Account access is available in the
            connected app.
          </p>
        )}
        {form.accountError && (
          <Alert variant="destructive">
            <AlertTitle>Couldn’t continue</AlertTitle>
            <AlertDescription>{form.accountError}</AlertDescription>
          </Alert>
        )}
      </form>
    </CardContent>
    <CardFooter className="justify-center">
      <p className="text-sm text-muted-foreground">
        {register ? "Already have an account? " : "New to Feedback Desk? "}
        <Link
          className="font-medium text-primary underline-offset-4 hover:underline"
          to={register ? Path.Login : Path.Register}
          state={returnState}
          aria-disabled={form.pending}
          onClick={event => {
            if (form.pending) {
              event.preventDefault();
              return;
            }
            form.reset();
          }}
        >
          {register ? "Sign in" : "Create account"}
        </Link>
      </p>
    </CardFooter>
  </Card>
);
