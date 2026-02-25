import React from "react";
import { createBrowserRouter, Navigate } from "react-router";

import { AppLayout } from "./layout";

const GathererPage = React.lazy(() => import("@/pages/gatherer/page"));
const ProfilePage = React.lazy(() => import("@/pages/profile/page"));
const TimelinePage = React.lazy(() => import("@/pages/timeline/page"));
const ApiKeysPage = React.lazy(() => import("@/pages/apikeys/page"));

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/gatherer" replace /> },
      { path: "gatherer", element: <GathererPage /> },
      { path: "profile", element: <ProfilePage /> },
      { path: "timeline", element: <TimelinePage /> },
      { path: "apikeys", element: <ApiKeysPage /> },
    ],
  },
]);
