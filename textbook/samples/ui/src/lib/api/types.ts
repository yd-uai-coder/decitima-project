// DeciTima samples │ 初出 Phase 3 │ 改訂 Phase 4,5,6,7,8,9,10,11,12,13,14
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

// ── project_scheduling(Topological Sort / CPM / RCPSP。Phase 8）───
export type ProjectTask = {
  id: string;
  name?: string | null;
  duration: number;
  resource?: number;
};

export type TaskDependency = { id: string; predecessor: string; successor: string };

export type ProjectData = {
  problem_type: "project_scheduling";
  tasks: ProjectTask[];
  dependencies: TaskDependency[];
  resource_capacity?: number | null;
};

export type ScheduledTask = {
  task_id: string;
  start: number;
  finish: number;
  slack: number;
};

export type ProjectSolution = {
  problem_type: "project_scheduling";
  task_order: string[];
  schedule: ScheduledTask[];
  critical_path: string[];
  makespan: number;
};

// ── logistics_planning(CVRP。Phase 9）───────────────────────────
export type LogisticsNode = { id: string; label?: string | null; x?: number | null; y?: number | null };

export type RoadSegment = {
  id: string;
  source: string;
  target: string;
  distance: number;
  directed?: boolean;
};

export type Vehicle = { id: string; capacity_weight: number; capacity_volume: number };

export type DeliveryStop = {
  id: string;
  node_id: string;
  demand_weight: number;
  demand_volume: number;
};

export type LogisticsData = {
  problem_type: "logistics_planning";
  depot_id: string;
  nodes: LogisticsNode[];
  segments: RoadSegment[];
  vehicles: Vehicle[];
  deliveries: DeliveryStop[];
};

export type VehicleRoute = { vehicle_id: string; stop_ids: string[]; distance: number };

export type LogisticsSolution = {
  problem_type: "logistics_planning";
  routes: VehicleRoute[];
  total_distance: number;
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
    }
  | {
      problem_type: "project_scheduling";
      objectives: Objective[];
      constraints?: Constraint[];
      data: ProjectData;
    }
  | {
      problem_type: "logistics_planning";
      objectives: Objective[];
      constraints?: Constraint[];
      data: LogisticsData;
    };

export type ConstraintViolation = {
  constraint_kind: string;
  severity: "hard" | "soft";
  message: string;
};

export type CandidateSolution = {
  status: "valid" | "invalid" | "infeasible";
  assignments:
    | RouteSolution
    | NetworkDesignSolution
    | ShiftSolution
    | TravelSolution
    | ProjectSolution
    | LogisticsSolution;
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

// ── algorithm recommendation(problem_type に依存しない。Phase 12）─
export type AlgorithmRecommendation = AlgorithmMeta & {
  description: string;
  is_rule_preferred: boolean;
  llm_rank?: number | null;
  llm_comment?: string | null;
};

export type RecommendationResponse = {
  problem_type: string;
  rule_preferred: string;
  recommendations: AlgorithmRecommendation[];
  notes: string[];
};

// ── result explanation(problem_type に依存しない。Phase 13）───────
export type ExplanationResponse = {
  solution_id: string;
  problem_type: string;
  algorithm_name: string;
  why_this_solution: string;
  key_constraints: string;
  algorithm_rationale: string;
  alternatives_comparison: string;
  improvement_notes: string;
  notes: string[];
};

// ── LLM vs Algorithm comparison(problem_type に依存しない。Phase 14）─
export type ComparisonRequest = {
  problem: OptimizationProblem;
  algorithm?: string | null;
  llm_runs?: number;
};

export type RunOutcome = {
  status: string | null;
  metrics: Record<string, number>;
  hard_violations: number;
  soft_violations: number;
  elapsed_ms: number;
  error: string | null;
  structure_hash: string | null;
};

export type ComparisonMetrics = {
  constraint_compliance_rate_algorithm: number;
  constraint_compliance_rate_llm: number;
  optimality_avg_quality_ratio_llm: number | null;
  reproducibility_distinct_solutions_llm: number;
  execution_time_ms_algorithm: number;
  execution_time_ms_llm_median: number;
  error_rate_llm: number;
};

export type ComparisonNarrative = {
  summary: string;
  constraint_compliance_note: string;
  optimality_note: string;
  reproducibility_note: string;
  verifiability_note: string;
};

export type ComparisonResponse = {
  problem_type: string;
  algorithm_used: AlgorithmMeta;
  algorithm_result: RunOutcome;
  llm_results: RunOutcome[];
  metrics: ComparisonMetrics;
  narrative: ComparisonNarrative | null;
  notes: string[];
};

// ── jobs(problem_type に依存しない非同期実行。Phase 9-8）────────
export type JobSubmitResponse = { job_id: string; status: string };

export type JobStatusResponse = {
  job_id: string;
  problem_type: string;
  status: "queued" | "running" | "succeeded" | "failed";
  // (Phase 9-8)
  // result?: CandidateSolution | null;
  // (Phase 10-4) simulate ジョブの結果(SimulationResult)も返せるように型を広げる
  result?: CandidateSolution | SimulationResult | null;
  problem_id?: string | null;
  solution_id?: string | null;
  error?: string | null;
  created_at: string;
  updated_at: string;
};

// ── simulate(What-if Simulation。Phase 10）─────────────────────
export type ScenarioOverride = { label: string; overrides: Record<string, unknown> };

export type SensitivitySpec = {
  field_path: string;
  low: number;
  high: number;
  target_metric: string;
  threshold: number;
  mode?: "at_most" | "at_least";
};

export type SimulationRequest = {
  problem: OptimizationProblem;
  algorithm?: string | null;
  scenarios: ScenarioOverride[];
  sensitivity?: SensitivitySpec | null;
};

export type ScenarioResult = {
  label: string;
  status: "valid" | "invalid" | "infeasible" | "invalid_scenario";
  metrics: Record<string, number>;
  algorithm_name: string | null;
  error?: string | null;
};

export type SensitivityResult = {
  threshold_value: number | null;
  evaluated: Record<string, number>; // key はパラメータ値(number を JSON key にした文字列)
};

export type SimulationResult = {
  base: ScenarioResult;
  scenarios: ScenarioResult[];
  sensitivity?: SensitivityResult | null;
};

// ── structure(LLM Problem Structuring。Phase 11）───────────────
export type StructuringRequest = { text: string; conversation_id?: string | null };

export type StructuringResponse = {
  conversation_id: string;
  problem_type: string;
  problem: OptimizationProblem;
  notes: string[];
};

// ここまで DeciTima backend の DTO

// backend の app/schemas/auth.py と対応
export type TokenPair = { access_token: string; refresh_token: string };
export type AccessToken = { access_token: string };
