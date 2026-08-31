# Phase 1-2: AlgorithmStrategy と registry(作業単位 1-2)

## この章のゴール

「問題まるごとを解く」アルゴリズムが従う契約と、`problem_type` から候補を引く仕組みを作る。

- `AlgorithmStrategy` プロトコル(`app/algorithms/base.py`)
- `registry`(`app/algorithms/registry.py`)── `REGISTRY` / `get_strategies` / `find_strategy`
- `select_strategy`(`app/services/algorithm_selection.py`)と、なぜ services 層に置くか
- `NoAlgorithmError` を `app/services/errors.py` に追加

**この章で新規作成するファイル**: `app/algorithms/base.py`、`app/algorithms/registry.py`、`app/services/algorithm_selection.py`。**既存ファイルへの追記**: `app/services/errors.py`(§4)。

対応サンプル: `samples/app/algorithms/base.py`, `registry.py`,
`samples/app/services/algorithm_selection.py`。テストは `samples/tests/unit/test_registry.py`。
`app/services/errors.py` は既存ファイルへの追記(§4)で samples には含めない。設計は `Phase-0-4.md`。

---

## 1. `AlgorithmStrategy` プロトコル

```python
# app/algorithms/base.py
from typing import Protocol, runtime_checkable

from app.domain.problems.problem import OptimizationProblem
from app.domain.solutions.solution import AlgorithmMeta, CandidateSolution


@runtime_checkable
class AlgorithmStrategy(Protocol):
    """1つのアルゴリズムが満たす契約。problem を受けて候補解を返すだけ。"""

    meta: AlgorithmMeta

    def solve(self, problem: OptimizationProblem) -> CandidateSolution:
        """OptimizationProblem を決定論的に解いて CandidateSolution を返す。検証はしない。"""
        ...
```

- **`Protocol`(ABC ではない)**: 継承を強制しない。手実装・ライブラリラッパー・テスト用
  フェイクの 3 種が「`meta` と `solve` を持つ」だけで契約を満たす(`Phase-0-4.md` §2.1)。
- **`@runtime_checkable`**: `isinstance(obj, AlgorithmStrategy)` を実行時に使えるようにする。
  
  > 例）
  > 
  > ```
  > class GreedyAlgorithm:
  >     meta = AlgorithmMeta(...)
  > 
  >     def solve(
  >         self,
  >         problem: OptimizationProblem
  >     ) 
  > 
  > algorithm = GreedyAlgorithm()
  > isinstance(algorithm, AlgorithmStrategy)
  > ```
  > 
  > の場合、結果はTrueとなる
  > 
  > algorithm は AlgorithmStrategy か？
  >  ↓
  > meta を持っている？
  > solve を持っている？
  >  ↓
  > Yes
  >  ↓
  > True

- **`solve` は純粋**: 入力は `OptimizationProblem` のみ、出力は `CandidateSolution` のみ。
  DB・時刻・グローバル状態に触れない。乱数は `problem.metadata["seed"]` から取る。
- **`solve` は検証しない**: 解を作るだけ。制約充足の判定は Verification の仕事。
  ただし「解が存在しない」と判断できたら `status="infeasible"` を返してよい(`Phase-0-4.md` §2.3)。

---

## 2. `registry` ── problem_type → 候補

```python
# app/algorithms/registry.py   ← このファイルは「純粋」(app.domain と標準ライブラリのみ)
from app.algorithms.base import AlgorithmStrategy

# 作業単位 1-4 で次行のコメントを外す(進行ルール #15)
# from app.algorithms.graph.dijkstra import DijkstraStrategy
from app.domain.problems.problem import OptimizationProblem

REGISTRY: dict[str, list[AlgorithmStrategy]] = {
    "route_planning": [
        # DijkstraStrategy(),     ← 作業単位 1-4 で有効化
        # AStarStrategy(), NetworkxShortestPath()   ← Phase 4
    ],
    "shift_scheduling": [
        # GreedyShiftStrategy(), BacktrackingShiftStrategy()   ← Phase 5
    ],
}


def get_strategies(problem_type: str) -> list[AlgorithmStrategy]:
    """problem_type に対応するアルゴリズム候補。未登録なら空リスト。"""
    return REGISTRY.get(problem_type, [])


def all_strategies() -> list[tuple[str, AlgorithmStrategy]]:
    """(problem_type, strategy) の全ペア。GET /api/v1/algorithms が使う。"""
    return [(pt, s) for pt, ss in REGISTRY.items() for s in ss]


def find_strategy(problem, requested=None) -> AlgorithmStrategy | None:
    """rule-based 選択(純粋版)。該当が無ければ None を返す(送出しない)。
    - requested があれば meta.name 一致を最優先
    - MVP の rule は「候補の先頭」(問題特性による分岐は Phase 4/5)
    """
    candidates = get_strategies(problem.problem_type)
    if not candidates:
        return None
    if requested is not None:
        return next((s for s in candidates if s.meta.name == requested), None)
    return candidates[0]
```

- **エントリはモジュールロード時に 1 回だけ生成**(`DijkstraStrategy()` のように)。`solve` が
  インスタンス状態を持たない純粋関数なので安全(`Phase-0-4.md` §4.2)。
- 新アルゴリズムの追加は **リストに 1 行**。既存コードに触れない(オープン・クローズドの原則)。
- **前方参照はコメントアウトで出荷する**(進行ルール #15)。`registry` は全 strategy を集約する
  ので、作成順の都合で未作成の strategy を参照しがち。`DijkstraStrategy` は作業単位 1-4 で作る
  ので、この章では import ごとコメントアウトし、1-4 でコメントを外す。**1-2 の時点で `REGISTRY`
  は route / shift とも空**。
  
  > オープン・クローズドの原則：
  > ソフトウェアの構成要素は「拡張に対して開いていて、変更に対して閉じている」べきである。
  
  > | 文字    | 原則                              | 日本語           | 一言でいうと                |
  > | ----- | ------------------------------- | ------------- | --------------------- |
  > | **S** | Single Responsibility Principle | 単一責任の原則       | **1つのクラスに1つの責任**      |
  > | **O** | Open/Closed Principle           | オープン・クローズドの原則 | **拡張しやすく、変更しなくて済む**   |
  > | **L** | Liskov Substitution Principle   | リスコフの置換原則     | **親を子に置き換えても正しく動く**   |
  > | **I** | Interface Segregation Principle | インターフェース分離の原則 | **使わない機能まで実装させない**    |
  > | **D** | Dependency Inversion Principle  | 依存性逆転の原則      | **具体的な実装ではなく抽象に依存する** |
- Phase 1 で `REGISTRY` に載る(コメントを外す)のは `DijkstraStrategy` だけで、それは
  **作業単位 1-4**([Phase-1-4](./Phase-1-4.md) §7)。Linear/Binary Search・BFS・DFS は
  **プリミティブ**なので載せない([Phase-1-3](./Phase-1-3.md))。

---

## 3. `select_strategy` は services 層に置く(Phase 0-4 スケッチからの変更)

`Phase-0-4.md` §6 のスケッチは `select_strategy` を `registry.py` に置き、
候補が無いとき `NoAlgorithmError` を送出していた。しかし:

- `NoAlgorithmError` は HTTP 400 に対応する **`AppError` 派生**で、`app/services/errors.py` に置く
  (`Phase-0-6.md` §4)。
- それを `app/algorithms/` が import すると **「algorithms → services」の逆流**になる
  (`Phase-0-3.md` §2.2 の依存方向。algorithms は domain と標準ライブラリしか import しない)。

そこで Phase 1 では 2 つに分ける:

```python
# app/services/algorithm_selection.py
from app.algorithms.registry import find_strategy
from app.services.errors import NoAlgorithmError


def select_strategy(problem, requested=None) -> AlgorithmStrategy:
    """find_strategy(純粋)を呼び、該当が無ければ NoAlgorithmError(400)を送出する。"""
    strategy = find_strategy(problem, requested)
    if strategy is None:
        if requested is not None:
            raise NoAlgorithmError(f"algorithm {requested!r} is not registered ...")
        raise NoAlgorithmError(f"no algorithm registered for {problem.problem_type!r}")
    return strategy
```

| ファイル                                  | 層        | 責務                                                                           |
| ------------------------------------- | -------- | ---------------------------------------------------------------------------- |
| `app/algorithms/registry.py`          | 純粋       | `REGISTRY` / `get_strategies` / `all_strategies` / `find_strategy`(None を返す) |
| `app/services/algorithm_selection.py` | services | `select_strategy`(None のとき `NoAlgorithmError`)                               |

> この変更はルート `CLAUDE.md` の Notes に記録する(進行のルール #4 / #10)。

---

## 4. `NoAlgorithmError` を追加

`app/services/errors.py` は既存の leaf モジュール。**samples には入れず、既存ファイルに次を足す**:

```python
# app/services/errors.py
from typing import ClassVar                       # ← 追加

from app.core.errors import (
    AppError,        # ← 追加
    BadGatewayError,
    BadRequestError,  # ← 追加
    ConflictError,
    NotFoundError,
    TooManyRequestsError,
    UnauthorizedError,
)

# ... 既存クラス(InvalidCredentialsError 〜 GenerationFailedError)はそのまま ...

# ---- Phase 1 で追加(DeciTima の solve パイプライン用。設計は Phase-0-6.md §4)----

class ProblemValidationError(BadRequestError):
    """OptimizationProblem がセマンティック検査に通らなかった場合に送出する(HTTP 400)。"""

class InfeasibleProblemError(BadRequestError):
    """条件を満たす解が原理的に存在しないと Validation 段階で判明した場合に送出する(HTTP 400)。"""

class NoAlgorithmError(BadRequestError):
    """registry に該当アルゴリズムが無い場合に送出する(HTTP 400)。

    problem_type が未対応、または requested のアルゴリズム名が登録されていないとき。
    """

class SolveTimeoutError(AppError):
    """アルゴリズムの実行が規定時間を超えた場合に送出する(HTTP 504)。"""

    status_code: ClassVar[int] = 504
```

4 クラスまとめて足しておくと [Phase-1-6](./Phase-1-6.md) で追記が要らない。
`VerificationFailedError` は**作らない** ── 解の制約違反は例外ではなく
`status="invalid"` で返す(`Phase-0-6.md` §4)。

---

## 5. テスト観点(`samples/tests/unit/test_registry.py`)

> **テスト対象 / ドライバ / スタブ**(進行ルール #14):
>
> - **対象**: (a) `AlgorithmStrategy` Protocol の構造的判定 / (b) registry の機構
>   (`get_strategies` / `all_strategies` / `find_strategy` / `select_strategy` の照会・選択・送出)
> - **ドライバ**: テスト関数
> - **スタブ / テストダブル**: (a) は不要 ── フェイク strategy は「Protocol を構造的に満たすか」を
>   確かめる**検査対象そのもの**。(b) は `_FakeStrategy` を `monkeypatch.setitem(REGISTRY, ...)` で
>   差し込む ── これは「登録済みの strategy」の**代役**で、具体アルゴリズム(1-4 で作る `Dijkstra`)に
>   依存せず選択ロジックだけを試すためのもの。実体が route_planning から引けることの確認は 1-4。

- フェイク(`meta` + `solve` を持つだけ)が `isinstance(x, AlgorithmStrategy)` を通る
- fixture でフェイクを登録 → `get_strategies` / `all_strategies` に現れる((pt, strategy) のペア形)
- `select_strategy(route_problem)` が既定で先頭候補(フェイク)を返す
- `requested="fake"` でそのフェイクが返る / `requested="a_star"`(未登録)で `NoAlgorithmError`
- `shift_scheduling`(候補ゼロ)で `NoAlgorithmError`
- `find_strategy(...)` は「候補ゼロ」でも「名前不一致」でも送出せず `None`
- **dijkstra が実際に登録されることの確認は [Phase-1-4](./Phase-1-4.md) §7**(registry.py のコメント解除後)

---

## 6. まとめ

- `AlgorithmStrategy` は `typing.Protocol`。`meta` + 純粋・非検証の `solve` を持てば契約成立。
- `registry.py` は純粋。`REGISTRY` は追加 1 行。エントリはロード時に 1 回だけ生成。
- `select_strategy` は services 層(`AppError` を送出するため)。`registry.find_strategy` は
  純粋版(`None` を返す)。Phase 0-4 スケッチからの変更点。
- `app/services/errors.py` に 4 つの `AppError` 派生を追加。

次章([Phase-1-3](./Phase-1-3.md))では、作業単位 1-3 ── 探索プリミティブ
(Linear / Binary Search・BFS・DFS)を実装する。
