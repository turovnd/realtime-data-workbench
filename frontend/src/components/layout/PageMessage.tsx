import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { Inbox } from "lucide-react";

import {
  Button,
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui";

type Props = {
  title: string;
  description: string;
  backTo?: string;
  children?: ReactNode;
};

export const PageMessage = ({
  title,
  description,
  backTo,
  children,
}: Props) => (
  <section className="flex min-h-[55svh] items-center justify-center">
    <Empty>
      <EmptyHeader>
        <EmptyMedia variant="icon">
          <Inbox />
        </EmptyMedia>
        <EmptyTitle>{title}</EmptyTitle>
        <EmptyDescription>{description}</EmptyDescription>
      </EmptyHeader>
      <EmptyContent className="flex-row justify-center">
        {children}
        {backTo && (
          <Button asChild>
            <Link to={backTo}>Back to feedback</Link>
          </Button>
        )}
      </EmptyContent>
    </Empty>
  </section>
);
