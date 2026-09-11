// DeciTima samples │ Phase 9
// @vitest-environment jsdom
import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { JobStatusResponse } from "@/lib/api/types";

const getJobStatus = vi.fn();
vi.mock("@/features/optimization/api/jobs", () => ({
  getJobStatus: (...a: unknown[]) => getJobStatus(...a),
}));

import { useJobPolling } from "./useJobPolling";

function _status(status: JobStatusResponse["status"]): JobStatusResponse {
  return {
    job_id: "job-1",
    problem_type: "logistics_planning",
    status,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  };
}

/** フェイクタイマーを進めつつ、保留中の Promise(モックした非同期関数の解決)と React の
 * 状態更新(act)もまとめて flush する。@testing-library/react の waitFor はフェイクタイマー
 * 環境だと内部の実タイマーポーリングでデッドロックするため使わず、これで代用する。 */
async function advance(ms: number): Promise<void> {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}

describe("useJobPolling", () => {
  beforeEach(() => {
    getJobStatus.mockReset();
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("does nothing while jobId is null", () => {
    const { result } = renderHook(() => useJobPolling(null));
    expect(result.current.job).toBeNull();
    expect(getJobStatus).not.toHaveBeenCalled();
  });

  it("fetches immediately and keeps polling while the job is not finished", async () => {
    getJobStatus.mockResolvedValue(_status("queued"));
    const { result } = renderHook(() => useJobPolling("job-1"));

    await advance(0); // 初回呼び出し(useEffect 内の即時 tick())を flush
    expect(getJobStatus).toHaveBeenCalledTimes(1);
    expect(result.current.job?.status).toBe("queued");

    await advance(1500);
    expect(getJobStatus).toHaveBeenCalledTimes(2);
  });

  it("stops polling once the job succeeds", async () => {
    getJobStatus.mockResolvedValue(_status("succeeded"));
    const { result } = renderHook(() => useJobPolling("job-1"));

    await advance(0);
    expect(result.current.job?.status).toBe("succeeded");
    const callsAfterFirstTick = getJobStatus.mock.calls.length;

    await advance(5000);
    expect(getJobStatus).toHaveBeenCalledTimes(callsAfterFirstTick); // それ以上増えない
  });

  it("records an error and stops polling when the fetch fails", async () => {
    getJobStatus.mockRejectedValue(new Error("boom"));
    const { result } = renderHook(() => useJobPolling("job-1"));

    await advance(0);
    expect(result.current.error).not.toBeNull();
    const callsAfterFailure = getJobStatus.mock.calls.length;

    await advance(5000);
    expect(getJobStatus).toHaveBeenCalledTimes(callsAfterFailure);
  });
});
