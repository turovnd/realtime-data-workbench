import { lazy } from "react";
import { Navigate } from "react-router-dom";
import type { RouteObject } from "react-router-dom";

import { PageMessage } from "@/components/layout";

import { Path } from "./paths";

const FeedbackPage = lazy(() =>
  import("@/pages/feedback").then(page => ({ default: page.FeedbackPage }))
);
const DetailsPage = lazy(() =>
  import("@/pages/feedback-details").then(page => ({
    default: page.DetailsPage,
  }))
);
const ActivityPage = lazy(() =>
  import("@/pages/activity").then(page => ({ default: page.ActivityPage }))
);

export const mainRoutes: RouteObject[] = [
  { index: true, element: <Navigate to={Path.Feedback} replace /> },
  { path: Path.Feedback, element: <FeedbackPage /> },
  { path: Path.FeedbackDetails, element: <DetailsPage /> },
  { path: Path.Activity, element: <ActivityPage /> },
  {
    path: Path.NotFound,
    element: (
      <PageMessage
        title="Page not found"
        description="This page may have moved. Return to your inbox to continue."
        backTo={Path.Feedback}
      />
    ),
  },
];
