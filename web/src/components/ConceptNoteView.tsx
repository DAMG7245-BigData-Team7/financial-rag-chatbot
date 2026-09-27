import type { ReactNode } from "react";
import type { QueryResponse } from "@/lib/api";
import { Formula } from "./Formula";

function looksLikeCode(s: string) {
  return s.includes("```") || /[=(]/.test(s);
}

function stripFences(s: string) {
  return s.replace(/^```\w*\n?/, "").replace(/\n?```$/, "");
}

function formatCitation(c: string) {
  const page = c.match(/^page_(.+)$/);
  if (page) return `p. ${page[1]}`;
  return c.replace(/^wikipedia:/, "");
}

function formatLatency(ms: number) {
  return ms < 1000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(1)} s`;
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="border-t border-zinc-800 pt-6">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-zinc-500">
        {title}
      </h3>
      {children}
    </section>
  );
}

function Bullets({ items }: { items: string[] }) {
  return (
    <ul className="space-y-2">
      {items.map((item, i) => (
        <li key={i} className="flex gap-3 leading-relaxed text-zinc-300">
          <span className="mt-2.5 h-1 w-1 shrink-0 rounded-full bg-amber-400" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

function Badge({ tone, children }: { tone: "emerald" | "sky" | "amber" | "zinc"; children: ReactNode }) {
  const tones = {
    emerald: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
    sky: "border-sky-500/30 bg-sky-500/10 text-sky-300",
    amber: "border-amber-500/30 bg-amber-500/10 text-amber-300",
    zinc: "border-zinc-700 bg-zinc-800/60 text-zinc-300",
  };
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${tones[tone]}`}>
      {children}
    </span>
  );
}

export function ConceptNoteView({
  result,
  latencyMs,
  onSelectConcept,
}: {
  result: QueryResponse;
  latencyMs: number;
  onSelectConcept: (concept: string) => void;
}) {
  const { note, source, cached, sources_used, relevance_score } = result;
  const fromToolbox = source === "fintbx";

  return (
    <article className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 shadow-2xl shadow-black/30 sm:p-8">
      <header className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center gap-2">
          {fromToolbox ? (
            <Badge tone="emerald">Grounded in MATLAB Financial Toolbox</Badge>
          ) : (
            <Badge tone="amber">Wikipedia fallback</Badge>
          )}
          <Badge tone={cached ? "sky" : "zinc"}>
            {cached ? "Served from cache" : "Freshly generated"} · {formatLatency(latencyMs)}
          </Badge>
          {relevance_score != null && (
            <Badge tone="zinc">Retrieval score {relevance_score.toFixed(2)}</Badge>
          )}
        </div>
        <h2 className="text-3xl font-semibold tracking-tight text-white">{note.concept}</h2>
        <p className="text-lg leading-relaxed text-zinc-300">{note.definition}</p>
      </header>

      <div className="mt-8 space-y-8">
        {note.key_points?.length > 0 && (
          <Section title="Key points">
            <Bullets items={note.key_points} />
          </Section>
        )}

        {note.formulas && note.formulas.length > 0 && (
          <Section title="Formulas">
            <div className="space-y-3">
              {note.formulas.map((f, i) => (
                <div key={i} className="rounded-xl border border-zinc-800 bg-zinc-950/60 px-4 py-3">
                  <Formula value={f} />
                </div>
              ))}
            </div>
          </Section>
        )}

        {note.matlab_functions && note.matlab_functions.length > 0 && (
          <Section title="MATLAB functions">
            <div className="flex flex-wrap gap-2">
              {note.matlab_functions.map((fn, i) => (
                <code key={i} className="rounded-md border border-zinc-800 bg-zinc-950 px-2 py-1 font-mono text-sm text-amber-200">
                  {fn}
                </code>
              ))}
            </div>
          </Section>
        )}

        {note.examples && note.examples.length > 0 && (
          <Section title="Examples">
            <div className="space-y-3">
              {note.examples.map((ex, i) =>
                looksLikeCode(ex) ? (
                  <pre key={i} className="overflow-x-auto rounded-xl border border-zinc-800 bg-zinc-950 p-4 font-mono text-sm leading-relaxed text-zinc-200">
                    {stripFences(ex)}
                  </pre>
                ) : (
                  <p key={i} className="leading-relaxed text-zinc-300">{ex}</p>
                ),
              )}
            </div>
          </Section>
        )}

        {note.practical_applications && note.practical_applications.length > 0 && (
          <Section title="Practical applications">
            <Bullets items={note.practical_applications} />
          </Section>
        )}

        {note.related_concepts && note.related_concepts.length > 0 && (
          <Section title="Related concepts">
            <div className="flex flex-wrap gap-2">
              {note.related_concepts.map((c) => (
                <button
                  key={c}
                  onClick={() => onSelectConcept(c)}
                  className="rounded-full border border-zinc-700 px-3 py-1 text-sm text-zinc-300 transition hover:border-amber-400/60 hover:text-amber-200"
                >
                  {c} →
                </button>
              ))}
            </div>
          </Section>
        )}

        {sources_used.length > 0 && (
          <Section title="Sources">
            <p className="text-sm text-zinc-400">
              {fromToolbox ? "MATLAB Financial Toolbox documentation, " : "Wikipedia: "}
              {sources_used.map(formatCitation).join(", ")}
            </p>
          </Section>
        )}
      </div>
    </article>
  );
}
