import { Suspense } from "react";
import { createBrowserRouter, Outlet, RouterProvider } from "react-router-dom";
import type { RouteObject } from "react-router-dom";

import { PageLoading } from "@/components/layout";

import { ProtectedWorkspace } from "./protected-workspace";
import { RouteError } from "./route-error";
import { authRoutes } from "./routes-auth";
import { mainRoutes } from "./routes-main";

const routes: RouteObject[] = [
  {
    element: (
      <Suspense fallback={<PageLoading label="Loading page" />}>
        <Outlet />
      </Suspense>
    ),
    errorElement: <RouteError />,
    children: [
      ...authRoutes,
      {
        element: <ProtectedWorkspace />,
        children: mainRoutes,
      },
    ],
  },
];

const router = createBrowserRouter(routes);

export const AppRouter = () => <RouterProvider router={router} />;
