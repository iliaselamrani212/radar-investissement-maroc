"use client";

import { useRef, useState, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { askProjectRag } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MessagesSquare, Send, Loader2, BrainCircuit, X } from "lucide-react";

interface Turn {
  role: "user" | "assistant";
  content: string;
}

const SUGGESTIONS = [
  "Quel est le contexte macro-financier de ce projet ?",
  "Comment ce montant se compare-t-il au secteur ?",
  "Quels risques ou points d'attention suivre ?",
];

const cleanDisplayText = (text: string) =>
  text
    .replace(/SDG\s+Capital/gi, "")
    .replace(/data\.gov\.ma/gi, "")
    .replace(/\n?##\s+Sources\s*&\s*fiabilit\S*[\s\S]*$/i, "")
    .replace(/\s\[\d+\]/g, "")
    .replace(/\s{2,}/g, " ")
    .trim();

export default function ProjectRagChat({ projectId }: { projectId: string }) {
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [open, setOpen] = useState(true);
  const endRef = useRef<HTMLDivElement>(null);

  const mutation = useMutation({
    mutationFn: (q: string) => askProjectRag(projectId, q),
    onSuccess: (data) => {
      setTurns((t) => [
        ...t,
        { role: "assistant", content: cleanDisplayText(data.reponse) },
      ]);
    },
    onError: () => {
      setTurns((t) => [
        ...t,
        {
          role: "assistant",
          content:
            "Erreur : le backend ou Ollama est indisponible. Verifiez que le serveur tourne et que l'index IA est pret.",
        },
      ]);
    },
  });

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, mutation.isPending]);

  const submit = (q: string) => {
    const cleaned = q.trim();
    if (!cleaned || mutation.isPending) return;
    setTurns((t) => [...t, { role: "user", content: cleaned }]);
    setQuestion("");
    mutation.mutate(cleaned);
  };

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-40 flex items-center gap-2 rounded-full bg-primary px-5 py-3 text-sm font-medium text-primary-foreground shadow-lg transition-transform hover:scale-105"
      >
        <MessagesSquare className="h-5 w-5" />
        Analyse IA
      </button>
    );
  }

  return (
    <Card className="fixed bottom-6 right-6 top-24 z-40 flex w-[420px] flex-col border-slate-200 shadow-2xl">
      <CardHeader className="flex shrink-0 flex-row items-center justify-between space-y-0 border-b border-slate-100 pb-3">
        <CardTitle className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
          <MessagesSquare className="h-4 w-4" />
          Analyse IA
        </CardTitle>
        <button
          onClick={() => setOpen(false)}
          aria-label="Fermer"
          className="rounded-md p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
        >
          <X className="h-4 w-4" />
        </button>
      </CardHeader>

      <CardContent className="flex min-h-0 flex-1 flex-col pt-5">
        <div className="mb-4 min-h-[260px] flex-1 space-y-4 overflow-y-auto pr-1">
          {turns.length === 0 && (
            <div className="rounded-lg border border-dashed border-slate-200 p-5 text-center">
              <BrainCircuit className="mx-auto mb-2 h-6 w-6 text-slate-300" />
              <p className="text-sm text-slate-500">
                Posez une question sur le contexte, les risques ou la pertinence du projet.
              </p>
            </div>
          )}

          {turns.map((turn, i) => (
            <div
              key={i}
              className={turn.role === "user" ? "flex justify-end" : "flex justify-start"}
            >
              <div
                className={
                  turn.role === "user"
                    ? "max-w-[80%] rounded-lg bg-slate-800 px-4 py-2.5 text-sm text-white"
                    : "max-w-[90%] rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700"
                }
              >
                <p className="whitespace-pre-wrap leading-6">
                  {cleanDisplayText(turn.content)}
                </p>
              </div>
            </div>
          ))}

          {mutation.isPending && (
            <div className="flex justify-start">
              <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500">
                <Loader2 className="h-4 w-4 animate-spin" />
                Analyse en cours...
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        {turns.length === 0 && (
          <div className="mb-3 flex shrink-0 flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => submit(s)}
                className="rounded-full border border-slate-200 px-3 py-1 text-xs text-slate-600 hover:bg-slate-50"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        <form
          onSubmit={(e) => {
            e.preventDefault();
            submit(question);
          }}
          className="flex shrink-0 gap-2"
        >
          <Input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Posez une question sur ce projet..."
            disabled={mutation.isPending}
          />
          <Button type="submit" disabled={mutation.isPending || !question.trim()}>
            {mutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
