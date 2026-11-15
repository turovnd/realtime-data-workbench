import { lazy } from "react";
import type { RouteObject } from "react-router-dom";

import { Path } from "./paths";

const AuthPage = lazy(() =>
  import("@/pages/auth").then(page => ({ default: page.AuthPage }))
);

export const authRoutes: RouteObject[] = [
  { path: Path.Login, element: <AuthPage /> },
  { path: Path.Register, element: <AuthPage /> },
];
