import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "react-router";

import { Providers } from "./app/providers";
import { router } from "./app/router";

import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";
import "@fontsource/jetbrains-mono/400.css";
import "@fontsource/jetbrains-mono/500.css";
import "./index.css";

async function enableMocking() {
  if (import.meta.env.DEV && import.meta.env.VITE_ENABLE_MOCKS === "true") {
    const { worker } = await import("./mocks/browser");
    return worker.start({ onUnhandledRequest: "bypass" });
  }
}

enableMocking().then(() => {
  ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
      <Providers>
        <RouterProvider router={router} />
      </Providers>
    </React.StrictMode>,
  );
});
