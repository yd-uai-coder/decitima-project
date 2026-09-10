// DeciTima samples │ 初出 Phase 3 │ 改訂 Phase 4,5,6,7
export type AsyncStatus = "idle" | "loading" | "success" | "error";

// ── DeciTima backend の DTO
// backend の app/schemas/optimization.py・app/domain/ と対応(OpenAPI 生成はしない ──
// Phase-0-3.md §6.2。TS 型 ↔ app/schemas の突き合わせをこの 1 ファイルに閉じる)。

export type AlgorithmMeta = {
  name: string;
  family: string;
  implementation: string;
  time_complexity?: string | null;
  space_complexity?: string | null;
};

// ── route_planning ──────────────────────────────────────────────
export type RouteNode = { id: string; label?: string | null; x?: number | null; y?: number | null };

export type RouteEdge = {
  id: string;
  source: string;
  target: string;
  weight: number;
  directed?: boolean;
};

export type RouteData = {
  problem_type: "route_planning";
  nodes: RouteNode[];
  edges: RouteEdge[];
  start: string;
  goal: string;
  allow_negative?: boolean; // Phase 4: 負辺を許可(Bellman-Ford 前提)
};

export type RouteSolution = {
  problem_type: "route_planning";
  path_node_ids: string[];
  path_edge_ids: string[];
  total_weight: number;
};

// ── network_design(MST。Phase 5)───────────────────────────────
export type NetworkNode = { id: string; label?: string | null };
export type NetworkLink = { id: string; endpoints: [string, string]; weight: number };

export type NetworkDesignData = {
  problem_type: "network_design";
  nodes: NetworkNode[];
  links: NetworkLink[];
};

export type NetworkDesignSolution = {
  problem_type: "network_design";
  selected_link_ids: string[];
  total_weight: number;
};

// ── shift_scheduling(Phase 6)──────────────────────────────────
export type Staff = {
  id: string;
  name?: string | null;
  hourly_wage: number;
  skills?: string[];
  available_slot_ids?: string[];
  requested_days_off?: string[];
};

export type ShiftSlot = {
  id: string;
  day: string; // ISO 日付
  start_hour: number;
  end_hour: number;
  required_headcount: number;
  required_skills?: string[];
};

export type ShiftData = {
  problem_type: "shift_scheduling";
  staff: Staff[];
  slots: ShiftSlot[];
  max_weekly_hours?: number;
  max_consecutive_days?: number;
};

export type ShiftSolution = {
  problem_type: "shift_scheduling";
  assignments: Record<string, string[]>; // slot_id -> [staff_id, ...]
};

// ── travel_planning(Knapsack DP。Phase 7）──────────────────────
export type Place = {
  id: string;
  name?: string | null;
  value: number;
  cost: number;
  duration: number;
};

export type TravelLeg = {
  id: string;
  endpoints: [string, string]; // 常に無向
  travel_cost: number;
  travel_time: number;
};

export type TravelData = {
  problem_type: "travel_planning";
  places: Place[];
  legs: TravelLeg[];
  budget: number;
  time_budget: number;
  start?: string | null;
  preferences?: Record<string, number>;
};

export type TravelSolution = {
  problem_type: "travel_planning";
  selected_place_ids: string[];
  visit_order: string[];
  total_value: number;
  total_cost: number;
  total_time: number;
};

// ── 共通スキーマ ────────────────────────────────────────────────
export type Objective = { sense: "minimize" | "maximize"; target: string; weight?: number };
export type Constraint = { kind: string; severity?: "hard" | "soft"; [key: string]: unknown };

export type OptimizationProblem =
  | {
      problem_type: "route_planning";
      objectives: Objective[];
      constraints?: Constraint[];
      data: RouteData;
    }
  | {
      problem_type: "network_design";
      objectives: Objective[];
      constraints?: Constraint[];
      data: NetworkDesignData;
    }
  | {
      problem_type: "shift_scheduling";
      objectives: Objective[];
      constraints?: Constraint[];
      data: ShiftData;
    }
  | {
      problem_type: "travel_planning";
      objectives: Objective[];
      constraints?: Constraint[];
      data: TravelData;
    };

export type ConstraintViolation = {
  constraint_kind: string;
  severity: "hard" | "soft";
  message: string;
};

export type CandidateSolution = {
  status: "valid" | "invalid" | "infeasible";
  assignments: RouteSolution | NetworkDesignSolution | ShiftSolution | TravelSolution;
  metrics: Record<string, number>;
  violations: ConstraintViolation[];
  produced_by: AlgorithmMeta;
};

// ── solve ──────────────────────────────────────────────────────
export type SolveRequest = {
  problem: OptimizationProblem;
  algorithm?: string | null;
  persist?: boolean;
};

export type SolveResponse = {
  solution: CandidateSolution;
  problem_id: string | null;
  solution_id: string | null;
};

// ── benchmark ──────────────────────────────────────────────────
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

// ここまで DeciTima backend の DTO

// backend の app/schemas/auth.py と対応
export type TokenPair = { access_token: string; refresh_token: string };
export type AccessToken = { access_token: string };
