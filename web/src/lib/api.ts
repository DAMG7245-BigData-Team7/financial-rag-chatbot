// Typed client for the AURELIA FastAPI backend (see app/models.py).
// The browser calls the API directly so long generations aren't capped by
// a serverless function timeout.

export const API_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080"
).replace(/\/$/, "");

export type SourceType = "fintbx" | "wikipedia";

export interface ConceptNote {
  concept: string;
  definition: string;
  key_points: string[];
  matlab_functions?: string[] | null;
  examples?: string[] | null;
  formulas?: string[] | null;
  related_concepts?: string[] | null;
  practical_applications?: string[] | null;
}

export interface QueryResponse {
  concept: string;
  note: ConceptNote;
  source: SourceType;
  cached: boolean;
  generated_at?: string | null;
  cached_at?: string | null;
  sources_used: string[];
  relevance_score?: number | null;
}

export interface HealthResponse {
  status: string;
  pinecone: string;
  postgres: string;
}

export interface StatsResponse {
  total_cached_concepts: number;
  source_breakdown: Record<string, number>;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
  ) {
    super(message);
  }
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  timeoutMs = 60_000,
): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init.headers },
      signal: AbortSignal.timeout(timeoutMs),
    });
  } catch (e) {
    if (e instanceof DOMException && e.name === "TimeoutError") {
      throw new ApiError("The request timed out. Please try again.");
    }
    throw new ApiError("Couldn't reach the API. It may be starting up.");
  }

  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {}
    throw new ApiError(detail, res.status);
  }
  return res.json() as Promise<T>;
}

export const queryConcept = (concept: string) =>
  request<QueryResponse>(
    "/query",
    { method: "POST", body: JSON.stringify({ concept, force_refresh: false }) },
    90_000,
  );

export const getHealth = () => request<HealthResponse>("/health", {}, 60_000);

export const getStats = () => request<StatsResponse>("/stats", {}, 20_000);
