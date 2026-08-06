"use client";

import { useEffect, useRef, useState } from "react";
import Message from "./Message";
import { streamChat, type ChatMessage } from "@/lib/api";

const SUGGESTIONS = [
  "How do I fix an infinite loop?",
  "Review my sorting function",
  "Explain recursion simply",
];

function generateSessionId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [sessionId, setSessionId] = useState("default");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setSessionId(generateSessionId());
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (override?: string) => {
    const text = (override ?? input).trim();
    if (!text || streaming) return;
    setInput("");
    const history: ChatMessage[] = [...messages, { role: "user", content: text }];
    setMessages(history);
    setStreaming(true);

    let draft = "";
    try {
      for await (const ev of streamChat(sessionId, history)) {
        if (ev.type === "text") {
          draft += ev.content ?? "";
          setMessages([...history, { role: "assistant", content: draft }]);
        } else if (ev.type === "guard" || ev.type === "error") {
          draft = ev.content ?? "";
          setMessages([...history, { role: "assistant", content: draft }]);
        }
      }
      if (!draft) {
        setMessages([...history, { role: "assistant", content: "(no response)" }]);
      }
    } catch {
      setMessages([
        ...history,
        { role: "assistant", content: "Could not reach the backend. Make sure it's running on port 8000." },
      ]);
    } finally {
      setStreaming(false);
    }
  };

  const reset = () => setMessages([]);

  return (
    <section className="flex h-[75vh] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm lg:h-[80vh]">
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          <h2 className="text-sm font-semibold text-slate-900">Smit Tutor</h2>
          <span className="hidden text-xs text-slate-400 sm:inline">
            session {sessionId.slice(0, 8)}
          </span>
        </div>
        <button
          onClick={reset}
          className="text-xs text-slate-500 transition hover:text-slate-800"
        >
          Clear
        </button>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.length === 0 && (
          <div className="mx-auto max-w-md pt-10 text-center">
            <p className="text-sm text-slate-600">
              Ask me anything about programming. I'll guide you with questions,
              review your code, rate it, and hunt bugs with you.
            </p>
            <div className="mt-4 flex flex-wrap justify-center gap-2 text-xs">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="rounded-full border border-slate-300 px-3 py-1 text-slate-600 transition hover:border-indigo-500 hover:text-indigo-600"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <Message key={i} message={m} />
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-slate-200 p-3">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send();
          }}
          className="flex items-end gap-2"
        >
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            rows={2}
            placeholder="Ask the tutor a question..."
            className="flex-1 resize-none rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
          />
          <button
            type="submit"
            disabled={!input.trim() || streaming}
            className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-700 disabled:opacity-40"
          >
            Send
          </button>
        </form>
      </div>
    </section>
  );
}
