import { http, HttpResponse, delay } from "msw";

import {
  MOCK_API_KEYS,
  MOCK_EMAILREP_RESULT,
  MOCK_GITHUB_RESULT,
  MOCK_HOLEHE_RESULT,
  MOCK_MODULES,
  MOCK_SEARCH_RESULT,
  MOCK_TWITTER_RESULT,
  makeMockTaskState,
} from "./data";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:5000";

let taskCounter = 0;
let apiKeys = [...MOCK_API_KEYS];

/** Maps task IDs to the module that dispatched them */
const taskModuleMap = new Map<string, string>();

export const handlers = [
  // GET /tasklist
  http.get(`${API}/tasklist`, () => {
    return HttpResponse.json({ modules: MOCK_MODULES });
  }),

  // POST /<module> -- dispatch a module search
  http.post(`${API}/:module`, async ({ params, request }) => {
    const module = params.module as string;

    // Handle apikey separately
    if (module === "apikey") {
      const body = (await request.json()) as Record<string, unknown>;
      if (body && Object.keys(body).length > 0 && Array.isArray(body)) {
        apiKeys = body.map(
          (k: { id?: string; name?: string; key?: string }) => ({
            id: k.id ?? crypto.randomUUID(),
            name: k.name ?? "",
            key: k.key ?? "",
          }),
        );
      }
      return HttpResponse.json({ keys: apiKeys });
    }

    const body = (await request.json()) as { username?: string };
    const taskId = `mock-task-${++taskCounter}`;
    taskModuleMap.set(taskId, module);
    await delay(200);
    return HttpResponse.json({
      module,
      task: taskId,
      param: body?.username ?? "unknown",
      from_m: "msw-mock",
    });
  }),

  // GET /state/:taskId/:module
  http.get(`${API}/state/:taskId/:module`, async ({ params }) => {
    await delay(300);
    return HttpResponse.json(
      makeMockTaskState(params.taskId as string, params.module as string),
    );
  }),

  // GET /result/:taskId -- return mock result based on dispatched module
  http.get(`${API}/result/:taskId`, async ({ params }) => {
    await delay(200);
    const taskId = params.taskId as string;
    const module = taskModuleMap.get(taskId) ?? "github";

    switch (module) {
      case "twitter":
        return HttpResponse.json(MOCK_TWITTER_RESULT);
      case "holehe":
        return HttpResponse.json(MOCK_HOLEHE_RESULT);
      case "search":
      case "dorks":
        return HttpResponse.json(MOCK_SEARCH_RESULT);
      case "emailrep":
        return HttpResponse.json(MOCK_EMAILREP_RESULT);
      default:
        return HttpResponse.json(MOCK_GITHUB_RESULT);
    }
  }),
];
