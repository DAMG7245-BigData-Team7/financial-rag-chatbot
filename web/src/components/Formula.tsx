import katex from "katex";

const LATEX_HINT = /\\[a-zA-Z]+|[\^_]\{|\\frac|\\sum/;

function stripDelimiters(s: string) {
  return s
    .trim()
    .replace(/^\$\$([\s\S]*)\$\$$/, "$1")
    .replace(/^\$([\s\S]*)\$$/, "$1")
    .replace(/^\\\[([\s\S]*)\\\]$/, "$1")
    .replace(/^\\\(([\s\S]*)\\\)$/, "$1")
    .trim();
}

function renderLatex(value: string): string | null {
  const tex = stripDelimiters(value);
  if (!value.includes("$") && !LATEX_HINT.test(tex)) return null;
  try {
    return katex.renderToString(tex, { displayMode: true, throwOnError: true });
  } catch {
    return null;
  }
}

// The LLM returns formulas as a mix of LaTeX and plain text. Render LaTeX
// with KaTeX when it parses; otherwise show the raw string in monospace.
export function Formula({ value }: { value: string }) {
  const html = renderLatex(value);

  if (html) {
    return (
      <div
        className="overflow-x-auto py-1 text-zinc-100"
        dangerouslySetInnerHTML={{ __html: html }}
      />
    );
  }

  return (
    <code className="block overflow-x-auto whitespace-pre-wrap font-mono text-sm text-zinc-200">
      {value}
    </code>
  );
}
