"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  ApiError,
  getHealth,
  getStats,
  queryConcept,
  type QueryResponse,
  type StatsResponse,
} from "@/lib/api";
import { exampleConcepts } from "@/lib/site";
import { ConceptNoteView } from "./ConceptNoteView";

type ApiStatus = "checking" | "waking" | "online" | "degraded" | "offline";

// The backend scales to zero, so the first request after idle can take a
// while. These steps mirror what /query does server-side.
const PIPELINE_STEPS = [
  "Checking the Postgres cache",
  "Embedding the query and searching Pinecone",
  "Scoring relevance against the Financial Toolbox docs",
  "Generating a structured note with GPT-4o-mini",
  "Validating the output schema and caching it",
];

function StatusPill({ status }: { status: ApiStatus }) {
  const map: Record<ApiStatus, { dot: string; label: string }> = {
    checking: { dot: "bg-zinc-500", label: "Connecting to API" },
    waking: { dot: "bg-amber-400 animate-pulse", label: "Waking up the API (free-tier cold start, ~15s)" },
    online: { dot: "bg-emerald-400", label: "API online" },
    degraded: { dot: "bg-amber-400", label: "API online, a dependency is degraded" },
    offline: { dot: "bg-rose-500", label: "API unreachable" },
  };
  const { dot, label } = map[status];
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-zinc-800 bg-zinc-900/80 px-3 py-1 text-xs text-zinc-400">
      <span className={`h-2 w-2 rounded-full ${dot}`} />
      {label}
    </span>
  );
}

function PipelineProgress({ concept }: { concept: string }) {
  const [step, setStep] = useState(0);
  useEffect(() => {
    const id = setInterval(
      () => setStep((s) => Math.min(s + 1, PIPELINE_STEPS.length - 1)),
      2200,
    );
    return () => clearInterval(id);
  }, []);

  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 sm:p-8" aria-live="polite">
      <p className="mb-5 text-sm text-zinc-400">
        Working on <span className="text-zinc-100">{concept}</span>…
      </p>
      <ol className="space-y-3">
        {PIPELINE_STEPS.map((label, i) => (
          <li key={label} className="flex items-center gap-3 text-sm">
            <span
              className={`flex h-5 w-5 items-center justify-center rounded-full border text-[10px] ${
                i < step
                  ? "border-emerald-500/50 bg-emerald-500/10 text-emerald-300"
                  : i === step
                    ? "border-amber-400/60 text-amber-300"
                    : "border-zinc-700 text-zinc-600"
              }`}
            >
              {i < step ? "✓" : i + 1}
            </span>
            <span className={i <= step ? "text-zinc-200" : "text-zinc-600"}>{label}</span>
            {i === step && (
              <span className="h-3 w-3 animate-spin rounded-full border-2 border-amber-400 border-t-transparent" />
            )}
          </li>
        ))}
      </ol>
      <p className="mt-5 text-xs text-zinc-500">
        New concepts take about 5–15 seconds. Cached ones come back almost instantly.
      </p>
    </div>
  );
}

export function Demo() {
  const [status, setStatus] = useState<ApiStatus>("checking");
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [input, setInput] = useState("");
  const [loadingConcept, setLoadingConcept] = useState<string | null>(null);
  const [result, setResult] = useState<{ data: QueryResponse; latencyMs: number } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const resultRef = useRef<HTMLDivElement>(null);

  const refreshStats = useCallback(() => {
    getStats().then(setStats).catch(() => {});
  }, []);

  const run = useCallback(
    async (raw: string) => {
      const concept = raw.trim();
      if (!concept || loadingConcept) return;

      setInput(concept);
      setError(null);
      setResult(null);
      setLoadingConcept(concept);

      const url = new URL(window.location.href);
      url.searchParams.set("q", concept);
      window.history.replaceState(null, "", url);
      requestAnimationFrame(() =>
        resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }),
      );

      const started = performance.now();
      try {
        const data = await queryConcept(concept);
        setResult({ data, latencyMs: performance.now() - started });
        setStatus((s) => (s === "offline" || s === "waking" ? "online" : s));
        if (!data.cached) refreshStats();
      } catch (e) {
        if (e instanceof ApiError && e.status === 404) {
          setError(
            `Couldn't find "${concept}" in the Financial Toolbox docs or finance-related Wikipedia articles. Try one of the examples above.`,
          );
        } else {
          setError(e instanceof Error ? e.message : "Something went wrong.");
        }
      } finally {
        setLoadingConcept(null);
      }
    },
    [loadingConcept, refreshStats],
  );

  // Wake the backend as soon as the page loads, and run any ?q= from a shared link.
  useEffect(() => {
    const wakingTimer = setTimeout(
      () => setStatus((s) => (s === "checking" ? "waking" : s)),
      1500,
    );
    getHealth()
      .then((h) => {
        setStatus(h.status === "healthy" ? "online" : "degraded");
        refreshStats();
      })
      .catch(() => setStatus("offline"))
      .finally(() => clearTimeout(wakingTimer));

    const q = new URLSearchParams(window.location.search).get("q");
    if (q) queueMicrotask(() => run(q));
    return () => clearTimeout(wakingTimer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const busy = loadingConcept !== null;

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <StatusPill status={status} />
        {stats && (
          <p className="text-xs text-zinc-500">
            <span className="text-zinc-300">{stats.total_cached_concepts}</span> notes cached ·{" "}
            <span className="text-zinc-300">{stats.source_breakdown.fintbx ?? 0}</span> from the Toolbox ·{" "}
            <span className="text-zinc-300">{stats.source_breakdown.wikipedia ?? 0}</span> from Wikipedia
          </p>
        )}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          run(input);
        }}
        className="flex flex-col gap-3 sm:flex-row"
      >
        <label htmlFor="concept" className="sr-only">
          Financial concept
        </label>
        <input
          id="concept"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Try a concept, e.g. Sharpe Ratio"
          maxLength={120}
          autoComplete="off"
          className="h-12 flex-1 rounded-xl border border-zinc-700 bg-zinc-900 px-4 text-zinc-100 placeholder:text-zinc-500 outline-none transition focus:border-amber-400/70 focus:ring-2 focus:ring-amber-400/20"
        />
        <button
          type="submit"
          disabled={busy || !input.trim()}
          className="h-12 rounded-xl bg-amber-400 px-6 font-medium text-zinc-950 transition hover:bg-amber-300 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {busy ? "Generating…" : "Generate note"}
        </button>
      </form>

      <div className="flex flex-wrap gap-2">
        {exampleConcepts.map((c) => (
          <button
            key={c}
            onClick={() => run(c)}
            disabled={busy}
            className="rounded-full border border-zinc-800 bg-zinc-900/60 px-3 py-1.5 text-sm text-zinc-300 transition hover:border-amber-400/50 hover:text-amber-200 disabled:opacity-50"
          >
            {c}
          </button>
        ))}
      </div>

      <div ref={resultRef} className="scroll-mt-6">
        {loadingConcept && <PipelineProgress key={loadingConcept} concept={loadingConcept} />}
        {error && (
          <div role="alert" className="rounded-2xl border border-rose-500/30 bg-rose-500/5 p-5 text-sm text-rose-200">
            {error}
          </div>
        )}
        {result && (
          <ConceptNoteView result={result.data} latencyMs={result.latencyMs} onSelectConcept={run} />
        )}
      </div>
    </div>
  );
}
