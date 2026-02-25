import { io, type Socket } from "socket.io-client";

const WS_URL = import.meta.env.VITE_WS_URL ?? "ws://localhost:5000";

let socket: Socket | null = null;

export function getSocket(): Socket {
  if (!socket) {
    socket = io(WS_URL, {
      autoConnect: false,
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
    });
  }
  return socket;
}

export function connectSocket(): void {
  const s = getSocket();
  if (!s.connected) s.connect();
}

export function disconnectSocket(): void {
  if (socket?.connected) socket.disconnect();
}

export function subscribeToTask(
  taskId: string,
  onState: (data: {
    task_id: string;
    module: string;
    state: string;
  }) => void,
  onResult: (data: {
    task_id: string;
    module: string;
    result: unknown[];
  }) => void,
  onError: (data: {
    task_id: string;
    module: string;
    error: string;
  }) => void,
): () => void {
  const s = getSocket();
  const stateEvent = `task:state:${taskId}`;
  const resultEvent = `task:result:${taskId}`;
  const errorEvent = `task:error:${taskId}`;

  s.on(stateEvent, onState);
  s.on(resultEvent, onResult);
  s.on(errorEvent, onError);

  return () => {
    s.off(stateEvent, onState);
    s.off(resultEvent, onResult);
    s.off(errorEvent, onError);
  };
}
