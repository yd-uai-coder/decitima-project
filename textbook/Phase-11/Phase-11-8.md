# Phase 11-8: UI ── 自然言語入力 + 確認カード + 確定用共有ストア(作業単位 11-8)

## この章のゴール

README §11「Human-in-the-loop」を実演する UI を作る:自然言語入力フォーム → 「AIが理解した条件」の確認カード → 確定。確定の遷移先(既存6ドメインページ)へ問題を受け渡す共有ストアもこの章で作る(11-9 が使う側)。

**この章で作成するファイル**: `ui/src/features/structuring/**`(新規)、
`ui/src/features/optimization/stores/pending-problem-store.ts`・
`ui/src/features/optimization/hooks/usePendingProblemHydration.ts`(新規、共有)、
`ui/src/lib/api/types.ts`・`ui/src/lib/menu-tree.ts`(現行版)、
`ui/src/app/(pages)/optimization/structuring/page.tsx`(新規)。

---

## 1. 型とAPIクライアント

```ts
// lib/api/types.ts(追記)
export type StructuringRequest = { text: string; conversation_id?: string | null };
export type StructuringResponse = {
  conversation_id: string;
  problem_type: string;
  problem: OptimizationProblem;
  notes: string[];
};
```

```ts
// features/structuring/api/structure.ts(全文)
export function submitStructuring(request: StructuringRequest): Promise<StructuringResponse> {
  return apiFetch<StructuringResponse>("/api/v1/structure", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
```

既存の `apiFetch<T>()`(`lib/api/client.ts`)をそのまま使う ── 認証トークンの付与・
401時のサイレントリフレッシュは共通処理に乗る。

---

## 2. `structuring-store` ── 確認カードでの「修正」は再度 LLM を呼ばない

```ts
// features/structuring/stores/structuring-store.ts(要点)
type StructuringStore = {
  text: string;
  conversationId: string | null;
  problem: OptimizationProblem | null;
  notes: string[];
  status: AsyncStatus;
  error: string | null;
  setText: (text: string) => void;
  setProblem: (problem: OptimizationProblem) => void;  // 確認カードでの手直し用
  submit: () => Promise<void>;
  reset: () => void;
};
```

`setProblem` は `submitStructuring` を呼ばず、local state を更新するだけ ── README §11の「修正する」を、既存共有 `ProblemJsonEditor`(Phase 4 由来)での値の手直しとして実現する(独自のリッチフォームは作らない、Phase 10 のシナリオエディタと同じ判断)。`submit` は他のドメインストア(`travel-planner-store` 等)と同じ `AsyncStatus` パターン。

---

## 3. `domainSummaries.ts` ── backend の `EXTRACTORS` と対の設計

```ts
// features/structuring/components/domainSummaries.ts(要点)
export function summarize(problem: OptimizationProblem): SummaryItem[] {
  const items: SummaryItem[] = [{ label: "目的", value: /* objectives を整形 */ }];
  if (problem.constraints && problem.constraints.length > 0) {
    items.push({ label: "制約", value: `${problem.constraints.length} 件` });
  }
  switch (problem.data.problem_type) {
    case "travel_planning":
      items.push({ label: "予算", value: `¥${problem.data.budget.toLocaleString()}` });
      // ...
      break;
    // ... 他5ドメイン
  }
  return items;
}

export const PROBLEM_TYPE_ROUTES: Record<OptimizationProblem["problem_type"], string> = {
  route_planning: "/optimization/route-planner",
  // ... 他5ドメイン
};
```

`summarize` は README §11 モック(「予算/期間/必須訪問先/優先事項/最小化目的」)を
ドメインごとに実装する ── backend の `EXTRACTORS`(problem_type → 抽出スキーマ)と同じ「problem_type → 表示ロジック」レジストリの思想を UI 側に写した対の設計。
`PROBLEM_TYPE_ROUTES` は確定ボタンの遷移先(11-9 で使う)。

---

## 4. `StructuredProblemCard` ── 確認 → 修正 → 確定

```tsx
// features/structuring/components/StructuredProblemCard.tsx(要点)
export function StructuredProblemCard() {
  const { problem, notes, setProblem } = useStructuring();
  const router = useRouter();
  const setPending = usePendingProblemStore((s) => s.setPending);

  if (!problem) return null;

  const confirm = () => {
    setPending(problem);
    router.push(PROBLEM_TYPE_ROUTES[problem.problem_type]);
  };

  return (
    <YStack ...>
      <Text>AIが理解した条件</Text>
      {summarize(problem).map((item) => <XStack key={item.label}>{item.label}: {item.value}</XStack>)}
      {notes.length > 0 ? notes.map((note) => <Paragraph key={note}>注記: {note}</Paragraph>) : null}
      <ProblemJsonEditor value={problem} samples={[]} onChange={setProblem} />
      <StyledButton onPress={confirm}>この条件で最適化する</StyledButton>
    </YStack>
  );
}
```

**新しい solve ビューアはここで作らない**。確定は `usePendingProblemStore.setPending(problem)`
で問題を共有ストアに置き、`router.push` で該当ドメインページへ遷移するだけ ── Phase 4〜9 で作った `GraphCanvas`/`TravelPlanCanvas`/`ProjectGanttView` 等の可視化・比較機能をそのまま活かす設計判断(ゼロから汎用ソルブビューアを作ると Phase 4〜9 の投資の二重化になる)。

---

## 5. `pending-problem-store` / `usePendingProblemHydration` ── 共有ストア(11-9 が使う側)

```ts
// features/optimization/stores/pending-problem-store.ts(全文)
export const usePendingProblemStore = create<PendingProblemStore>((set, get) => ({
  pending: null,
  setPending: (problem) => set({ pending: problem }),
  consumePending: (problemType) => {
    const pending = get().pending;
    if (!pending || pending.problem_type !== problemType) return null;
    set({ pending: null });  // 取り出すと同時に消費(戻る等での再適用を防ぐ)
    return pending;
  },
}));
```

```ts
// features/optimization/hooks/usePendingProblemHydration.ts(全文)
export function usePendingProblemHydration(
  problemType: OptimizationProblem["problem_type"],
  setProblem: (problem: OptimizationProblem) => void
): void {
  const consumePending = usePendingProblemStore((s) => s.consumePending);
  useEffect(() => {
    const pending = consumePending(problemType);
    if (pending) setProblem(pending);
  }, [problemType, consumePending, setProblem]);
}
```

**この章で共有ストア/フックを作る理由**(11-9 との章割り): `StructuredProblemCard`
(本章)が `setPending` の最初の消費者であり、`usePendingProblemHydration`(consumePendingを呼ぶ側)は11-9 の6ページが使う。進行のルール #15「前方 import の禁止」に沿い、両方とも本章で作っておく ── 11-9 は「使う側」の配線(6ページへの1行追加)だけに専念する。

`consumePending` は problem_type が一致しない場合 `null` を返し、pending をそのまま残す ──複数タブや誤った遷移で他ドメインの pending が誤消費されるのを防ぐ。

---

## まとめ

- 新規スライス `features/structuring/` は既存6ドメインスライスと並列の横断機能
  (Phase 10 の `features/optimization/simulation/` と同じ位置づけ)。
- `domainSummaries.ts` は backend の `EXTRACTORS` と対称的な「problem_type → 表示」レジストリ。
- 確定は新しいビューアを作らず、共有 `pending-problem-store` 経由で既存ドメインページへ問題を受け渡す(`router.push`)。
- `pending-problem-store`/`usePendingProblemHydration` は本章で作り、11-9 は「使う側」の配線に専念する(前方 import を避けるための章割り)。

## テスト観点

> **対象**: `structuring-store`(store)、`pending-problem-store`(store)、
> `usePendingProblemHydration`(hook)、`domainSummaries.ts`(純粋関数)
> **ドライバ**: Vitest。store は node env、hook は jsdom env(`renderHook`)
> **スタブ**: `structuring-store` のテストは `vi.mock` で `api/structure.ts` をモック
> (既存 `travel-planner-store.test.ts` と同型)。`pending-problem-store`/`domainSummaries`
> は純粋なのでスタブ不要

| ケース                                                                    | 期待                                                 |
| ---------------------------------------------------------------------- | -------------------------------------------------- |
| `submit()` 成功                                                          | `problem`/`conversationId`/`notes`/`status` が結果を反映 |
| `submit()` 失敗                                                          | `status === "error"`、`problem` は `null` のまま        |
| `setProblem(edited)`                                                   | local state が更新され、API は呼ばれない                       |
| `consumePending("travel_planning")`(何も無い)                              | `null`                                             |
| `setPending(P)` 後 `consumePending("travel_planning")`(P と一致)           | `P` を返し `pending` は `null` に                       |
| `setPending(P)` 後 `consumePending("route_planning")`(P と不一致)           | `null` を返し `pending` は `P` のまま                     |
| `usePendingProblemHydration("route_planning", setProblem)`(pending 無し) | `setProblem` は呼ばれない                                |
| 同上(一致する pending 有り)                                                    | `setProblem` が呼ばれ、`pending` が消費される                 |
| 同上(不一致の pending 有り)                                                    | `setProblem` は呼ばれず、`pending` は残る                   |
| `summarize(travel問題)`                                                  | `{label:"予算", value:"¥50,000"}` 等を含む               |
| `summarize(objectives が空)`                                             | `{label:"目的", value:"(抽出できませんでした)"}`               |

```bash
npx vitest run src/features/structuring src/features/optimization/stores src/features/optimization/hooks
npx tsc --noEmit
npx eslint src/features/structuring src/features/optimization/stores src/features/optimization/hooks
```

---

次章([Phase-11-9](./Phase-11-9.md))では、作業単位 11-9 ── 6ドメインページの Panel
コンポーネントに `usePendingProblemHydration` を1行ずつ配線し、README §11 の「確定 →最適化」の遷移を完成させる。
