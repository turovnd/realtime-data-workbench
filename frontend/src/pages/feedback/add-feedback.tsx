import { useEffect, useRef, useState, type FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useLocation, useNavigate } from "react-router-dom";
import { LoaderCircle } from "lucide-react";

import { adapter, getSession, type FeedbackInput } from "@/api";
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

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCloseFocus: () => void;
};

export const AddFeedback = ({ open, onOpenChange, onCloseFocus }: Props) => {
  const navigate = useNavigate();
  const location = useLocation();
  const client = useQueryClient();
  const [text, setText] = useState("");
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
    mutationFn: ({
      input,
    }: {
      input: FeedbackInput;
      session: ReturnType<typeof getSession>;
    }) => adapter.create(input),
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
      navigate(`/feedback/${encodeURIComponent(record.id)}${location.search}`);
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
    <Dialog open={open} onOpenChange={changeOpen}>
      <DialogContent
        onCloseAutoFocus={event => {
          event.preventDefault();
          onCloseFocus();
        }}
      >
        <DialogHeader>
          <DialogTitle>Add feedback</DialogTitle>
          <DialogDescription>
            Paste a customer message. We’ll organize and summarize it for you.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} className="flex flex-col gap-6">
          <FieldGroup>
            <Field>
              <FieldLabel htmlFor="feedback-text">Customer feedback</FieldLabel>
              <Textarea
                id="feedback-text"
                placeholder="What did the customer say?"
                className="min-h-36"
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
              {create.isPending ? "Saving…" : "Save feedback"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
