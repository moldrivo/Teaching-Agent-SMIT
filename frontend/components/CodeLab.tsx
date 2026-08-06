"use client";

import { useState } from "react";
import { analyzeCode, findBugs, rateCode } from "@/lib/api";

type Result = { kind: string; title: string; content: string };

export default function CodeLab() {
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [results, setResults] = useState<Result[]>([]);

  const run = async (kind: "rate" | "analyze" | "bugs") => {
    if (!code.trim() || busy) return;
    setBusy(true);
    try {
      let res: Result;
      if (kind === "rate") {
        const r = await rateCode(code);
        res = {
          kind,
          title: "Code Rating",
          content: [
            `Overall: ${r.overall}/10`,
            `Readability: ${r.readability} | Performance: ${r.performance} | Security: ${r.security}`,
            "",
            r.breakdown || "No notes — looks clean.",
          ].join("\n"),
        };
      } else if (kind === "analyze") {
        const r = await analyzeCode(code);
        res = {
          kind,
          title: "Complexity Analysis",
          content: `Time:  ${r.time_complexity}\nSpace: ${r.space_complexity}\n\n${r.explanation}`,
        };
      } else {
        const r = await findBugs(code);
        const body = r.bugs.length
          ? r.bugs
              .map(
                (b) =>
                  `[${b.severity.toUpperCase()}] L${b.line}: ${b.message}\n   \u2192 ${b.hint}`
              )
              .join("\n")
          : "No obvious bugs found by heuristics.\nAsk the tutor to review it in chat.";
        res = { kind, title: "Bug Hunt", content: body };
      }
      setResults((prev) => [res, ...prev]);
    } catch {
      setResults((prev) => [
        { kind, title: "Error", content: "Could not reach the backend API." },
        ...prev,
      ]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <aside className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div>
        <h2 className="text-sm font-semibold text-slate-900">Code Lab</h2>
        <p className="text-xs text-slate-500">
          Paste code for instant analysis — works fully offline.
        </p>
      </div>
      <textarea
        value={code}
        onChange={(e) => setCode(e.target.value)}
        placeholder="# Paste your Python code here..."
        spellCheck={false}
        className="h-48 resize-none rounded-xl border border-slate-300 bg-slate-50 p-3 font-mono text-xs focus:border-indigo-500 focus:outline-none"
      />
      <div className="grid grid-cols-3 gap-2">
        <button
          onClick={() => run("rate")}
          disabled={busy}
          className="rounded-lg bg-indigo-600 py-2 text-xs font-medium text-white transition hover:bg-indigo-700 disabled:opacity-50"
        >
          Rate
        </button>
        <button
          onClick={() => run("analyze")}
          disabled={busy}
          className="rounded-lg bg-slate-800 py-2 text-xs font-medium text-white transition hover:bg-slate-900 disabled:opacity-50"
        >
          Complexity
        </button>
        <button
          onClick={() => run("bugs")}
          disabled={busy}
          className="rounded-lg bg-rose-600 py-2 text-xs font-medium text-white transition hover:bg-rose-700 disabled:opacity-50"
        >
          Bug Hunt
        </button>
      </div>
      <div className="flex max-h-72 flex-col gap-2 overflow-y-auto">
        {results.map((r, i) => (
          <div key={i} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
            <p className="mb-1 text-xs font-semibold text-slate-700">{r.title}</p>
            <pre className="whitespace-pre-wrap font-mono text-[11px] leading-relaxed text-slate-600">
              {r.content}
            </pre>
          </div>
        ))}
      </div>
    </aside>
  );
}
