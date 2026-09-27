import { Demo } from "@/components/Demo";
import { site } from "@/lib/site";

const pipeline = [
  {
    title: "Cache check",
    body: "Every query hits PostgreSQL first. Repeat concepts return in ~140 ms with no model calls.",
  },
  {
    title: "Retrieval",
    body: "On a miss, the concept is embedded with text-embedding-3-large and matched against the MATLAB Financial Toolbox docs in Pinecone.",
  },
  {
    title: "Relevance gate",
    body: "If the top match scores below the threshold, it falls back to Wikipedia, but only for finance-related topics. The UI labels which source was used.",
  },
  {
    title: "Structured generation",
    body: "GPT-4o-mini fills a strict Pydantic schema via Instructor: definition, key points, formulas, MATLAB functions and page citations.",
  },
  {
    title: "Cache & serve",
    body: "The validated note is stored in Postgres, so the next request for it is instant.",
  },
];

const stack = [
  { group: "Backend", items: ["FastAPI", "Pydantic", "Instructor", "LangChain"] },
  { group: "Retrieval", items: ["Pinecone", "OpenAI embeddings", "BM25 (index build)"] },
  { group: "Data", items: ["PostgreSQL", "Airflow DAGs", "PyMuPDF parsing"] },
  { group: "Infra", items: ["Cloud Run", "Terraform", "GitHub Actions", "Vercel"] },
];

function GitHubIcon() {
  return (
    <svg viewBox="0 0 16 16" aria-hidden className="h-4 w-4 fill-current">
      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
    </svg>
  );
}

export default function Home() {
  return (
    <div className="relative isolate overflow-hidden">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[520px] bg-[radial-gradient(ellipse_60%_50%_at_50%_0%,rgba(251,191,36,0.14),transparent)]"
      />

      <nav className="mx-auto flex max-w-5xl items-center justify-between px-6 py-6">
        <span className="font-semibold tracking-[0.2em] text-amber-300">{site.name}</span>
        <div className="flex items-center gap-5 text-sm text-zinc-400">
          <a href="#how-it-works" className="hidden hover:text-zinc-100 sm:inline">How it works</a>
          <a href="#stack" className="hidden hover:text-zinc-100 sm:inline">Stack</a>
          <a href={site.githubUrl} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 hover:text-zinc-100">
            <GitHubIcon /> Source
          </a>
        </div>
      </nav>

      <main className="mx-auto max-w-5xl px-6">
        <header className="pb-12 pt-10 text-center sm:pt-16">
          <p className="mb-4 text-xs font-medium uppercase tracking-[0.25em] text-zinc-500">
            Retrieval-augmented generation · Live demo
          </p>
          <h1 className="mx-auto max-w-3xl text-4xl font-semibold tracking-tight text-white sm:text-6xl">
            {site.tagline}
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-zinc-400">
            Type a finance concept. AURELIA retrieves the relevant pages of the MATLAB Financial
            Toolbox docs and turns them into a structured, cited study note.
          </p>
        </header>

        <section id="demo" className="scroll-mt-8 pb-24">
          <Demo />
        </section>

        <section id="how-it-works" className="scroll-mt-8 border-t border-zinc-800/80 py-16">
          <h2 className="text-2xl font-semibold text-white">How it works</h2>
          <p className="mt-2 max-w-2xl text-zinc-400">
            A cache-first RAG pipeline. It only spends tokens when it has to, and it says when an
            answer didn&apos;t come from the primary source.
          </p>
          <ol className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {pipeline.map((step, i) => (
              <li key={step.title} className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5">
                <span className="font-mono text-xs text-amber-400">0{i + 1}</span>
                <h3 className="mt-2 font-medium text-zinc-100">{step.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-zinc-400">{step.body}</p>
              </li>
            ))}
          </ol>
        </section>

        <section id="stack" className="scroll-mt-8 border-t border-zinc-800/80 py-16">
          <h2 className="text-2xl font-semibold text-white">Tech stack</h2>
          <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {stack.map((s) => (
              <div key={s.group}>
                <h3 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">{s.group}</h3>
                <ul className="mt-3 flex flex-wrap gap-2">
                  {s.items.map((item) => (
                    <li key={item} className="rounded-md border border-zinc-800 bg-zinc-900/60 px-2.5 py-1 text-sm text-zinc-300">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      </main>

      <footer className="border-t border-zinc-800/80">
        <div className="mx-auto flex max-w-5xl flex-col gap-3 px-6 py-8 text-sm text-zinc-500 sm:flex-row sm:items-center sm:justify-between">
          <p>
            {site.author.name} · {site.credits}
          </p>
          <div className="flex gap-5">
            {site.author.linkedinUrl && (
              <a href={site.author.linkedinUrl} target="_blank" rel="noreferrer" className="hover:text-zinc-200">LinkedIn</a>
            )}
            {site.author.portfolioUrl && (
              <a href={site.author.portfolioUrl} target="_blank" rel="noreferrer" className="hover:text-zinc-200">Portfolio</a>
            )}
            <a href={site.githubUrl} target="_blank" rel="noreferrer" className="hover:text-zinc-200">GitHub</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
