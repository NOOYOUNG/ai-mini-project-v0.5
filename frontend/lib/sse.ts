import type { AgentEvent } from "./events";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

/**
 * POST /api/chat 를 호출하고, 도착하는 SSE 이벤트를 하나씩 onEvent 로 전달합니다.
 * SSE 형식: "data: {json}\n\n" 이 반복됩니다.
 */
export async function streamChat(
  body: { item_id: string; query: string; test_mode: boolean },
  onEvent: (ev: AgentEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok || !res.body) throw new Error(`요청 실패: ${res.status}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // 이벤트 구분자(빈 줄) 단위로 잘라서 처리하고, 덜 도착한 마지막 조각은 buffer 에 남깁니다.
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      const line = part.split("\n").find((l) => l.startsWith("data: "));
      if (line) onEvent(JSON.parse(line.slice(6)) as AgentEvent);
    }
  }
}
