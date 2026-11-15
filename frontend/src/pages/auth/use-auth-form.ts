import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { authenticate, clearPrivateStorage, resetPreview } from "@/api";

type Mode = "demo" | "login" | "register";

type Submission = {
  mode: Mode;
  email: string;
  password: string;
};

export const useAuthForm = (register: boolean) => {
  const client = useQueryClient();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const mutation = useMutation({
    mutationFn: async (submission: Submission) => {
      await client.cancelQueries();
      client.clear();
      clearPrivateStorage();

      if (submission.mode === "demo") {
        resetPreview();
      }

      return authenticate(
        submission.mode,
        submission.mode === "demo"
          ? undefined
          : {
              email: submission.email.trim().toLowerCase(),
              password: submission.password,
            }
      );
    },
  });

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (mutation.isPending) {
      return;
    }

    mutation.mutate({ mode: register ? "register" : "login", email, password });
  };

  const openDemo = () => {
    if (mutation.isPending) {
      return;
    }

    mutation.mutate({ mode: "demo", email: "", password: "" });
  };

  const reset = () => {
    mutation.reset();
    setPassword("");
  };

  const demo = mutation.variables?.mode === "demo";

  return {
    email,
    password,
    setEmail,
    setPassword,
    submit,
    openDemo,
    reset,
    pending: mutation.isPending,
    accountPending: mutation.isPending && !demo,
    demoPending: mutation.isPending && demo,
    accountError: !demo ? mutation.error?.message : undefined,
    demoError: demo ? mutation.error?.message : undefined,
  };
};

export type AuthFormState = ReturnType<typeof useAuthForm>;
