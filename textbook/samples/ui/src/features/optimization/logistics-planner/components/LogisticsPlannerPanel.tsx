// DeciTima samples │ Phase 9(改訂 Phase 11: usePendingProblemHydration / Phase 12: 推薦カード / Phase 13: 説明カード / Phase 14: LLM比較カード)
"use client";

import { Paragraph, Spinner, Text, XStack, YStack } from "tamagui";
import { StyledButton } from "@/components/ui/primitives/StyledButton";
import { AlgorithmRecommendationCard } from "@/features/optimization/components/AlgorithmRecommendationCard";
import { BenchmarkTable } from "@/features/optimization/components/BenchmarkTable";
import { ComparisonCard } from "@/features/optimization/components/ComparisonCard";
import { ExplanationCard } from "@/features/optimization/components/ExplanationCard";
import { ProblemJsonEditor } from "@/features/optimization/components/ProblemJsonEditor";
import { useJobPolling } from "@/features/optimization/hooks/useJobPolling";
import { usePendingProblemHydration } from "@/features/optimization/hooks/usePendingProblemHydration";
import { LogisticsRouteView } from "@/features/optimization/logistics-planner/components/LogisticsRouteView";
import { useLogisticsPlanner } from "@/features/optimization/logistics-planner/hooks/useLogisticsPlanner";
import { LOGISTICS_SAMPLES } from "@/features/optimization/logistics-planner/sample-problems";

/**
 * Logistics Optimizer 画面の中核。デポ・車両・配送先を編集 →「配送計画を作る」で
 * knapsack_dp(容量だけを見た上界)の結果を車両ごとに可視化、「使用台数を最小化(PuLP)」で
 * ビンパッキング MILP の解を、「ジョブとして投げる」で /jobs 経由の非同期実行(結果は
 * ポーリングで反映)を試せる。「5 strategy を比較」で knapsack_dp/greedy/branch_and_bound/
 * brute_force/pulp_milp を横並び実測する。
 */
export function LogisticsPlannerPanel() {
  const lp = useLogisticsPlanner();
  usePendingProblemHydration("logistics_planning", lp.setProblem); // (Phase 11-9)
  const data = lp.problem.problem_type === "logistics_planning" ? lp.problem.data : null;
  const { job, error: jobPollError } = useJobPolling(lp.jobId);

  return (
    <YStack gap="$4" padding="$4" maxWidth={960}>
      <YStack gap="$1">
        <Text fontSize="$6" fontWeight="700">
          Logistics Optimizer
        </Text>
        <Paragraph color="$color11">
          1つのデポから複数車両が出発し、複数の配送先を分担して回ります(CVRP)。knapsack_dp は
          容量だけを見て詰める(移動距離は無視)ため、greedy より総距離で劣ることがあります。
          pulp_milp は総距離でなく「使用台数」を最小化する、別の目的関数を持つ産業ソルバーです。
        </Paragraph>
      </YStack>

      <ProblemJsonEditor value={lp.problem} samples={LOGISTICS_SAMPLES} onChange={lp.setProblem} />

      <AlgorithmRecommendationCard problem={lp.problem} /> {/* (Phase 12-4) */}
      <ExplanationCard problem={lp.problem} /> {/* (Phase 13-4) */}
      <ComparisonCard problem={lp.problem} /> {/* (Phase 14-7) */}

      <XStack gap="$2" flexWrap="wrap">
        <StyledButton
          theme="blue"
          disabled={lp.solveStatus === "loading"}
          onPress={() => void lp.solve()}
        >
          {lp.solveStatus === "loading" ? <Spinner /> : "配送計画を作る"}
        </StyledButton>
        <StyledButton disabled={lp.solveStatus === "loading"} onPress={() => void lp.solve("pulp_milp")}>
          使用台数を最小化(PuLP)
        </StyledButton>
        <StyledButton disabled={lp.compareStatus === "loading"} onPress={() => void lp.compare()}>
          {lp.compareStatus === "loading" ? <Spinner /> : "5 strategy を比較"}
        </StyledButton>
        <StyledButton
          disabled={lp.jobStatus === "loading"}
          onPress={() => void lp.submitAsJob("pulp_milp")}
        >
          {lp.jobStatus === "loading" ? <Spinner /> : "ジョブとして投げる(/jobs)"}
        </StyledButton>
      </XStack>

      {lp.error ? <Text color="$red10">{lp.error}</Text> : null}

      {data && lp.solution ? <LogisticsRouteView data={data} solution={lp.solution} /> : null}

      {lp.jobId ? (
        <YStack gap="$2" borderWidth={1} borderColor="$borderColor" borderRadius="$4" padding="$3">
          <Text fontSize="$3" fontWeight="600">
            ジョブ {lp.jobId} ── {job?.status ?? "queued"}
          </Text>
          {jobPollError ? <Text color="$red10">{jobPollError}</Text> : null}
          {job?.status === "failed" ? <Text color="$red10">{job.error}</Text> : null}
          {/* (Phase 10-4) job.result は simulate ジョブの結果も返せるように型が広がった
              (JobStatusResponse、Phase 9-8→10-4)。solve ジョブの CandidateSolution だけに
              絞る型ガードを足す。*/}
          {job?.status === "succeeded" && job.result && "status" in job.result && data ? (
            <LogisticsRouteView data={data} solution={job.result} />
          ) : null}
        </YStack>
      ) : null}

      {lp.comparison ? <BenchmarkTable entries={lp.comparison.entries} /> : null}
    </YStack>
  );
}
