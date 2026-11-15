import { Path } from "@/router/paths";

export const getAuthDestination = (state: unknown): string => {
  if (
    !state ||
    typeof state !== "object" ||
    !("from" in state) ||
    typeof state.from !== "string"
  ) {
    return Path.Feedback;
  }

  return /^\/(feedback(?:\/|\?|$)|activity(?:\?|$))/.test(state.from)
    ? state.from
    : Path.Feedback;
};
