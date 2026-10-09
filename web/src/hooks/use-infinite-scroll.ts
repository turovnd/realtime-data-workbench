import { useEffect, useRef } from "react";

/** One request per visible intersection; the button remains the accessible fallback. */
export const useInfiniteScroll = (enabled: boolean, loadMore: () => void) => {
  const sentinel = useRef<HTMLDivElement>(null);
  const requested = useRef(false);
  useEffect(() => {
    const element = sentinel.current;
    if (!element || typeof IntersectionObserver === "undefined") return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) {
          requested.current = false;
          return;
        }
        if (enabled && !requested.current) {
          requested.current = true;
          loadMore();
        }
      },
      { rootMargin: "160px" },
    );
    observer.observe(element);
    return () => observer.disconnect();
  }, [enabled, loadMore]);
  return sentinel;
};
