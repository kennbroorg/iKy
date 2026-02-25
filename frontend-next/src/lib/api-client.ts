import type {
  ApiKey,
  ApiKeyResponse,
  TaskDispatchResponse,
  TaskListResponse,
  TaskResultResponse,
  TaskStateResponse,
} from "@/types/api";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:5000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export function fetchTaskList(): Promise<TaskListResponse> {
  return request("/tasklist");
}

export function dispatchModule(
  module: string,
  params: { username: string; from?: string; [key: string]: unknown },
): Promise<TaskDispatchResponse> {
  return request(`/${module}`, {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export function fetchTaskState(
  taskId: string,
  module: string,
): Promise<TaskStateResponse> {
  return request(`/state/${taskId}/${module}`);
}

export function fetchTaskResult(taskId: string): Promise<TaskResultResponse> {
  return request(`/result/${taskId}`);
}

export function fetchApiKeys(): Promise<ApiKeyResponse> {
  return request("/apikey", { method: "POST", body: JSON.stringify({}) });
}

export function writeApiKeys(keys: ApiKey[]): Promise<ApiKeyResponse> {
  return request("/apikey", {
    method: "POST",
    body: JSON.stringify(keys),
  });
}
