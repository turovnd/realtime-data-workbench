import { useSyncExternalStore } from "react";

const media = "(max-width: 767px)";
const subscribe = (onChange: () => void) => {
  const query = window.matchMedia(media);
  query.addEventListener("change", onChange);
  return () => query.removeEventListener("change", onChange);
};
export const useIsMobile = () =>
  useSyncExternalStore(
    subscribe,
    () => window.matchMedia(media).matches,
    () => false,
  );
