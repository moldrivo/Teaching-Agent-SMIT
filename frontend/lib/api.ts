export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface StreamEvent {
  type: "text" | "guard" | "error" | "done";
  action?: string;
  content?: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function* streamChat(
  sessionId: string,
  messages: ChatMessage[]
): AsyncGenerator<StreamEvent> {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, messages }),
  });
  if (!res.ok || !res.body) {
    throw new Error(`Backend responded ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let sep: number;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      const raw = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      if (raw.startsWith("data: ")) {
        yield JSON.parse(raw.slice(6)) as StreamEvent;
      }
    }
  }
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Backend responded ${res.status}`);
  return res.json() as Promise<T>;
}

export interface RatingResult {
  overall: number;
  readability: number;
  performance: number;
  security: number;
  breakdown: string;
}

export interface ComplexityResult {
  time_complexity: string;
  space_complexity: string;
  explanation: string;
}

export interface BugFinding {
  severity: string;
  line: number;
  message: string;
  hint: string;
}

export interface BugResult {
  bugs: BugFinding[];
}

export const rateCode = (code: string) => post<RatingResult>("/api/code/rate", { code });
export const analyzeCode = (code: string) => post<ComplexityResult>("/api/code/analyze", { code });
export const findBugs = (code: string) => post<BugResult>("/api/code/bugs", { code });
