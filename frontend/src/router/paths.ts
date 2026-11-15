export const Path = {
  Home: "/",
  Login: "/login",
  Register: "/register",
  Feedback: "/feedback",
  FeedbackDetails: "/feedback/:id",
  Activity: "/activity",
  NotFound: "*",
} as const;

export const feedbackPath = (id: string): string =>
  `${Path.Feedback}/${encodeURIComponent(id)}`;
