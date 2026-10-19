import { Skeleton } from "@/components/ui";

type Props = { label: string; embedded?: boolean };

export const PageLoading = ({ label, embedded = false }: Props) => (
  <div
    role="status"
    aria-label={label}
    className={
      embedded
        ? "flex flex-col gap-5 py-8"
        : "mx-auto flex min-h-svh max-w-3xl flex-col justify-center gap-5 px-6"
    }
  >
    <Skeleton className="h-8 w-44" />
    <Skeleton className="h-12 w-full" />
    <Skeleton className="h-72 w-full" />
    <span className="sr-only">{label}</span>
  </div>
);
