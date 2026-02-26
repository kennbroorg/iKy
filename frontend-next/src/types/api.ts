/** Response from POST /<module> */
export interface TaskDispatchResponse {
  module: string;
  task: string;
  param: string;
  from_m: string;
}

/** Response from GET /state/<task_id>/<module> */
export interface TaskStateResponse {
  state: "PENDING" | "STARTED" | "SUCCESS" | "FAILURE" | "RETRY" | "REVOKED";
  task_id: string;
  task_app: string;
}

export interface RawError {
  status: "Warning" | "Fail";
  reason: string;
  traceback?: string;
}

export interface GraphicItem {
  details?: unknown[];
  social?: unknown[];
  cal_actual?: string;
  cal_previous?: string;
  [key: string]: unknown;
}

export interface ProfileItem {
  email?: string;
  name?: string;
  organization?: string;
  location?: string;
  geo?: { lat: number; lng: number };
  photos?: { src: string; caption?: string }[];
  presence?: { source: string; url: string; name?: string }[];
  social?: { source: string; url: string; name?: string }[];
  [key: string]: unknown;
}

export interface TimelineEvent {
  date: string;
  action: string;
  icon?: string;
  desc?: string;
}

export interface TaskReference {
  module: string;
  param: string;
}

/** Parsed module result (from the backend's array format) */
export interface ModuleResultRaw {
  module: string;
  param: string;
  validation: "hard" | "soft" | "no" | "not_used";
  raw: Record<string, unknown> | RawError[] | string[];
  graphic: GraphicItem[];
  profile: ProfileItem[];
  timeline: TimelineEvent[];
  tasks: TaskReference[];
  /** GhostProject stores leak data at the top level instead of in graphic[] */
  leaks?: { email: string; password: string }[];
}

/** Response from GET /result/<task_id> */
export interface TaskResultResponse {
  result: Record<string, unknown>[];
  error?: string;
}

export interface ApiKey {
  id: string;
  name: string;
  key: string;
}

export interface ApiKeyResponse {
  keys: ApiKey[];
}

export interface TaskListResponse {
  modules: string[];
}
