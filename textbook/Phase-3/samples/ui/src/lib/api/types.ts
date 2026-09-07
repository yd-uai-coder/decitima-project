export type AsyncStatus = "idle" | "loading" | "success" | "error";

// ── 認証(JWT)── backend の app/schemas/auth.py と対応 ──
// login は access + refresh を返すが、refresh エンドポイントは access だけを返す
// (backend はリフレッシュトークンをローテーションしない)。
export type TokenPair = { access_token: string; refresh_token: string };
export type AccessToken = { access_token: string };

// ── DeciTima backend の DTO(手書き。MVP は OpenAPI 生成しない ── Phase-0-3 §6.2)──
// backend の app/schemas/optimization.py・app/domain/ と対応させる。ズレたら手で直す。

export type AlgorithmMeta = {
  name: string;
  family: string;
  implementation: string;
  time_complexity?: string | null;
  space_complexity?: string | null;
};

// benchmark に渡す最小の問題形。route_planning のみ(shift は Phase 6 で追加)。
export type RouteNode = { id: string; label?: string | null; x?: number | null; y?: number | null };
export type RouteEdge = {
  id: string;
  source: string;
  target: string;
  weight: number;
  directed?: boolean;
};
export type OptimizationProblem = {
  problem_type: "route_planning";
  objectives: { sense: "minimize" | "maximize"; target: string; weight?: number }[];
  constraints?: Record<string, unknown>[];
  data: {
    problem_type: "route_planning";
    nodes: RouteNode[];
    edges: RouteEdge[];
    start: string;
    goal: string;
  };
};

export type BenchmarkRequest = {
  problem: OptimizationProblem;
  algorithms?: string[] | null;
  runs?: number;
  persist?: boolean;
};

export type BenchmarkEntry = {
  algorithm: AlgorithmMeta;
  solution_status: string;
  metrics: Record<string, number>;
  elapsed_ms_median: number;
  elapsed_ms_p25: number;
  elapsed_ms_p75: number;
  peak_memory_kb: number;
  operation_count: number | null;
  hard_violations: number;
  soft_violations: number;
  quality_ratio: number | null;
};

export type BenchmarkResponse = {
  entries: BenchmarkEntry[];
  benchmark_id: string | null;
};

export type BenchmarkRunRead = {
  id: string;
  problem_type: string;
  created_at: string;
  payload: { problem: unknown; entries: BenchmarkEntry[]; runs: number };
};
