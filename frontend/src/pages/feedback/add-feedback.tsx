import { useEffect, useRef, useState, type FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useLocation, useNavigate } from "react-router-dom";
import { FileText, LoaderCircle } from "lucide-react";

import { feedbackPath } from "@/router/paths";
import { adapter, getSession, type FeedbackInput } from "@/api";
import { submitFeedback, type FeedbackSubmission } from "@/api/feedback";
import {
  Alert,
  AlertDescription,
  Button,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Textarea,
} from "@/components/ui";

import { exampleFeedback } from "./example-feedback";

type Props = {
  initialText: string;
  liveAnalysis: boolean;
  onOpenChange: (open: boolean) => void;
  onCloseFocus: () => void;
};

export const AddFeedback = ({
  initialText,
  liveAnalysis,
  onOpenChange,
  onCloseFocus,
}: Props) => {
  const navigate = useNavigate();
  const location = useLocation();
  const client = useQueryClient();
  const [text, setText] = useState(initialText);
  const [channel, setChannel] = useState<FeedbackInput["channel"]>("Support");
  const [identity, setIdentity] = useState(() => crypto.randomUUID());
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const create = useMutation({
    mutationFn: (submission: FeedbackSubmission) =>
      submitFeedback(submission, {
        adapter,
        getSession,
        isOnline: () => navigator.onLine,
      }),
    onSuccess: async (record, submission) => {
      if (
        !submission.session ||
        submission.session.token !== getSession()?.token
      )
        return;
      const workspace = submission.session.workspace_id;
      client.setQueryData(["feedback-record", workspace, record.id], record);
      await client.resetQueries({ queryKey: ["feedback", workspace] });
      await client.invalidateQueries({
        queryKey: ["feedback-status", workspace],
      });
      if (!mounted.current || submission.session.token !== getSession()?.token)
        return;
      onOpenChange(false);
      navigate(`${feedbackPath(record.id)}${location.search}`);
    },
  });

  const changeOpen = (next: boolean) => {
    if (create.isPending) return;
    if (!next) {
      setText("");
      setChannel("Support");
      setIdentity(crypto.randomUUID());
      create.reset();
    }
    onOpenChange(next);
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (text.trim() && !create.isPending)
      create.mutate({
        input: { identity, text: text.trim(), channel },
        session: getSession(),
      });
  };

  return (
    <Dialog open onOpenChange={changeOpen}>
      <DialogContent
        className="max-h-[90svh] overflow-y-auto sm:max-w-xl"
        onCloseAutoFocus={event => {
          event.preventDefault();
          onCloseFocus();
        }}
      >
        <DialogHeader>
          <DialogTitle>Add feedback</DialogTitle>
          <DialogDescription>
            {liveAnalysis
              ? "Add a message to get an AI summary, topic and supporting quotes."
              : "Save a customer message to explore the feedback workflow."}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} className="flex flex-col gap-6">
          <FieldGroup>
            <Field>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <FieldLabel htmlFor="feedback-text">
                  Customer feedback
                </FieldLabel>
                {!text.trim() && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    disabled={create.isPending}
                    onClick={() => {
                      setText(exampleFeedback.text);
                      setChannel(exampleFeedback.channel);
                      create.reset();
                    }}
                  >
                    <FileText data-icon="inline-start" />
                    Use an example
                  </Button>
                )}
              </div>
              <Textarea
                id="feedback-text"
                placeholder="What did the customer say?"
                className="min-h-48"
                autoFocus
                value={text}
                maxLength={4000}
                required
                disabled={create.isPending}
                onChange={event => {
                  setText(event.target.value);
                  if (create.isError) setIdentity(crypto.randomUUID());
                }}
              />
              <FieldDescription>
                {text === exampleFeedback.text
                  ? "Synthetic example. You can edit it before submitting."
                  : `${text.length.toLocaleString()} / 4,000 characters`}
              </FieldDescription>
            </Field>
            <Field>
              <FieldLabel htmlFor="feedback-source">Source</FieldLabel>
              <Select
                value={channel}
                onValueChange={value => {
                  setChannel(value as FeedbackInput["channel"]);
                  if (create.isError) setIdentity(crypto.randomUUID());
                }}
                disabled={create.isPending}
              >
                <SelectTrigger id="feedback-source" className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    {["Support", "In-app", "Community"].map(source => (
                      <SelectItem key={source} value={source}>
                        {source}
                      </SelectItem>
                    ))}
                  </SelectGroup>
                </SelectContent>
              </Select>
            </Field>
          </FieldGroup>
          {create.error && (
            <Alert variant="destructive">
              <AlertDescription>{create.error.message}</AlertDescription>
            </Alert>
          )}
          <p className="text-xs text-muted-foreground">
            {liveAnalysis
              ? "Submitting sends this text to our AI provider. Use sample or non-sensitive feedback."
              : "This mode uses sample analysis. No message is sent to an AI provider."}
          </p>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => changeOpen(false)}
              disabled={create.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={!text.trim() || create.isPending}>
              {create.isPending && (
                <LoaderCircle
                  className="animate-spin"
                  data-icon="inline-start"
                />
              )}
              {create.isPending
                ? "Saving…"
                : liveAnalysis
                  ? "Analyze feedback"
                  : "Save feedback"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
