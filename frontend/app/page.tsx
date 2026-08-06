import Chat from "@/components/Chat";
import CodeLab from "@/components/CodeLab";

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-6 p-4 lg:p-8">
      <header className="text-center">
        <h1 className="text-2xl font-bold text-slate-900">Smit Teaching Agent</h1>
        <p className="text-sm text-slate-500">
          Socratic guidance, code reviews, complexity analysis, and bug hunts — from beginner to advanced.
        </p>
      </header>
      <div className="grid flex-1 grid-cols-1 gap-6 lg:grid-cols-[1fr_400px]">
        <Chat />
        <CodeLab />
      </div>
    </main>
  );
}
