"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import CodeBlock from "./CodeBlock";

export default function Message({ message }: { message: { role: string; content: string } }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? "bg-indigo-600 text-white"
            : "border border-slate-200 bg-white shadow-sm"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : message.content ? (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{ code: CodeBlock as any }}
          >
            {message.content}
          </ReactMarkdown>
        ) : (
          <span className="inline-flex gap-1 py-1">
            <span className="dot" />
            <span className="dot" />
            <span className="dot" />
          </span>
        )}
      </div>
    </div>
  );
}
