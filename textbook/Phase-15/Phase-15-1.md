# Phase 15-1: 性能テスト基盤 + Testing階層監査(作業単位 15-1)

## この章のゴール

README §15「Performance」の実質的な作業(15-2〜15-6)を始める前に、大規模入力を使った実測を書ける土台を作る。加えて README §15「Testing」の6種別(Unit/Integration/API/E2E/Algorithm/Constraint)を、既存のどのファイルが既に担っているかを一度棚卸しし、Phase 15 で本当に新規に書くべき責務を絞り込む。

**この章で作成 / 更新するファイル**: `tests/performance/__init__.py`・
`tests/performance/generators.py`・`tests/performance/conftest.py`・
`tests/performance/test_generators.py`(すべて新規)、`pyproject.toml`(`performance`マーカー追記)。
**追補(§2.1、ユーザー写経で発覚)**: `tests/analysis/conftest.py`(新規)、
`pyproject.toml`(`analysis`マーカー追記)。

---

## 1. Testing階層監査 ── README §15の6種別は、実はほぼ揃っている

| README §15 の種別                | 既に担っているもの                                                                                                                             | Phase 15 で足すもの         |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- |
| Unit Test                     | `tests/unit/**`(220件超、Phase 1〜14)                                                                                                     | なし                     |
| Integration Test              | `tests/integration/**`(`@pytest.mark.integration`、実PostgreSQL/Redis)                                                                  | なし                     |
| API Test                      | `tests/api/**`(全エンドポイント)                                                                                                              | なし                     |
| Algorithm Test                | 各 `tests/unit/test_*_strategies.py`(手実装 vs 産業ソルバー vs 正解オラクルの突き合わせ)                                                                    | なし                     |
| Constraint Test               | `tests/unit/test_constraint_checkers.py`・`test_verification_service.py`                                                               | なし                     |
| **E2E Test**                  | **無し**(`textbook/Phase-0/Phase-0-9.md` のテストピラミッド図に「E2E(Phase 15)」と予告のみ)                                                               | **15-8/15-9 で新設**      |
| **(README に明記無いが必要)大規模入力テスト** | `tests/fixtures/optimization.py` の `build_scaled_*` 系フィクスチャ(規模を振れる問題ジェネレータ、Phase 3/6/7/8/9 で追加)はあるが、**それを使って実際に「壊れるか」を確認する専用テスト層が無い** | **本章 + 15-2/15-3 で新設** |

結論: README §15 の6種別のうち5つは Phase 0〜14 が既に実装済み。Phase 15 の Testing柱で新規に書くのは **E2E**(15-8/15-9)と、Performance柱の実測を支える **大規模入力テスト層**(本章)の2つだけに絞られる。

## 2. `tests/performance/` ── 大規模入力の「壊れ方」を確認する専用ディレクトリ

`tests/integration/` が `@pytest.mark.integration` で既定実行から除外されるのと同じ形で、`tests/performance/` も `performance` マーカーで除外する(実行に数秒〜十数秒かかるため)。

```toml
# pyproject.toml(改訂)
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["."]
addopts = "-m 'not integration and not performance'"
markers = [
    "integration: requires live PostgreSQL and Redis (see docker compose)",
    "performance: large-input timing/behavior tests, slow by design (see Phase 15)",
]
```

> **写経の罠**: `addopts` の `-m` 式を `'not integration'` のまま `performance` を書き忘れると、`uv run pytest`(既定実行)が毎回大規模入力テストまで回して数十秒遅くなる。両方を1つの `-m` 式に入れること(`and` でつなぐ、`-m 'not integration' -m 'not performance'`
> という2引数形式は後勝ちで `not integration` が無視される)。

> addopts : pytest を実行するたびに自動的に追加するコマンドラインオプション
> コマンド) pytest -> 自動でpytest -m "not integration and not performance" 
> として実行される。
> - integration → 実行しない
> - performance → 実行しない
> - それ以外 → 実行する
> 
> integration: **統合テスト**
> performance: **性能テスト**
> 
> 統合、性能テストが必要な時に
> pytest -m integration
> の様に指定して実行する

### 2.1 追補(ユーザー写経で発覚)── `tests/analysis/` にも同型のマーカーが要った

`decitima-api` の Docker コンテナ(`docker compose run --rm --no-deps backend uv run pytest
--collect-only`)で実際に写経を検証したところ、`tests/analysis/test_plots.py`
(`matplotlib` を import)が `ImportError` で collection ごと中断した。原因: analysis
依存群(pandas/matplotlib、`[dependency-groups].analysis`)は Docker イメージに意図的に
含めていない(README §8「NumPy/SciPy/pandas はコア層に入れない」)── `tests/analysis/` は
本来 `integration`/`performance` と同じく「特定の環境でだけ動く」テスト層なのに、
マーカーによる除外が漏れていた。

```toml
# pyproject.toml(さらに改訂)
addopts = "-m 'not integration and not performance and not analysis'"
markers = [
    "integration: requires live PostgreSQL and Redis (see docker compose)",
    "performance: large-input timing/behavior tests, slow by design (see Phase 15)",
    "analysis: requires the analysis dependency group (pandas/matplotlib) — see tests/analysis/",
]
```

```python
# tests/analysis/conftest.py(新規、全文)
def pytest_collection_modifyitems(items: Sequence[pytest.Item]) -> None:
    for item in items:
        if _THIS_DIR in item.path.parents:
            item.add_marker(pytest.mark.analysis)
```

> **写経の罠**: `pytest_collection_modifyitems` は「歴史的フック」── どの conftest.py に
> 書いても、収集された items **全件**(他ディレクトリ含む)を受け取る。フィクスチャのような
> ディレクトリスコープの自動絞り込みは無い。最初の実装で `if _THIS_DIR in item.path.parents`
> の絞り込みを忘れ、**全テストに `analysis` マーカーが付いて既定実行が0件収集**になる
> 事故を起こした(overlay で `no tests collected (645 deselected)` として発覚)。
> ディレクトリ単位で挙動を変えるフックは、必ず `item.path`/`item.fspath` で対象を絞り込む。

overlay 再検証: `uv run pytest`(既定)601 passed / 44 deselected(analysis 35 +
performance 3 + integration 6)、`uv run pytest -m analysis` 35 passed。ユーザーの実
Docker コンテナでも `docker compose run --rm --no-deps backend uv run pytest
--collect-only` が 568/572 collected・エラー無しで完走することを確認した。

## 3. `generators.py` ── 既存フィクスチャを再利用し、無い形状だけ足す

進行のルール #17(既存を共通化のために触ってよいかの判断)をここでも適用する。
`tests/fixtures/optimization.py` には Phase 3/6/7/8/9 で追加された `build_scaled_route_problem`
/ `build_scaled_shift_problem` / `build_scaled_travel_problem` / `build_scaled_project_problem`
/ `build_scaled_logistics_problem` が既にある ── **これらを複製せず、そのまま import して使う**。

新規に要るのは2つだけ:

1. **`topological_sort` の最悪形状**(線形チェーン)── 既存 `build_scaled_project_problem` は
   依存を `i < j` の中からランダムに1〜2本張るだけなので、最長経路が `n` に届かず
   再帰の深さを検証できない(15-3 で詳しく検証)。
2. **travel の `budget`/`time_budget` を独立して振れる形**── 既存
   `build_scaled_travel_problem(n_places, seed)` は `budget=20, time_budget=20` に固定
   されており、`_MAX_KNAPSACK_DP_CELLS` の実測(15-2)に必要な「大きな budget」を作れない。
   これは `tests/fixtures/optimization.py` 側の**関数への引数追加**で解決する(15-2 で実施、
   本章では触らない ── 「触る章」は最初の消費者に寄せる、進行のルール #17)。

```python
# tests/performance/generators.py(新規、全文)
"""大規模入力ジェネレータ ── Phase 15 の性能テスト専用。

既存 `tests/fixtures/optimization.py::build_scaled_*` で作れる形状は再利用する(ここには
書かない)。ここに置くのは、既存フィクスチャでは作れない「最悪ケースの形状」だけ。

3トラック制約(NumPy/SciPy/pandas はコア層に入れない、README §8)を守り、素の Python
(`random` 標準ライブラリ)のみで書く。
"""

from __future__ import annotations


def linear_chain_successors(n: int) -> dict[str, list[str]]:
    """T0 -> T1 -> T2 -> ... -> T(n-1) の一直線 DAG(隣接辞書)を作る。

    `topological_sort` の DFS 実装にとって最も深い再帰を誘発する形 ── 各タスクの後続は
    高々1つなので、枝分かれによる再帰の分散が起きず、深さがそのまま n になる。
    `build_scaled_project_problem`(ランダム DAG)は依存が分散するため、この最悪形状を
    再現できない(15-3 で実測して確認する)。
    """
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    return {f"T{i}": [f"T{i + 1}"] if i < n - 1 else [] for i in range(n)}
```

```python
# tests/performance/conftest.py(新規、全文)
"""性能テスト共通のフィクスチャ。"""

from collections.abc import Callable
from typing import TypeVar

import pytest

from app.services.measurement import Measurement, measure_call

T = TypeVar("T")


@pytest.fixture
def measure() -> Callable[[Callable[[], T], int], tuple[T, Measurement]]:
    """`measure_call` をそのまま返す薄いフィクスチャ。

    Phase 3 の計測コアを性能テストでも再利用する(スタブ不要 ── measure_call 自体が
    対象の callable を直接実行する薄いラッパーで、独自の外部依存を持たないため)。
    """
    return measure_call
```

---

## まとめ

- README §15 の Testing柱は、Phase 15 で新規に書くべきものが E2E と大規模入力テスト層の2つだけに絞られると分かった(Unit/Integration/API/Algorithm/Constraint は既存資産で充足)。
- `tests/performance/` を `integration` と同型のマーカーで新設した。
- 大規模入力は既存 `build_scaled_*` フィクスチャの再利用を基本とし、それで作れない「最悪形状」だけを `generators.py` に足した(重複を作らない、ルール #17)。
- **追補**: `tests/analysis/` にも同型の `analysis` マーカーを新設した(ユーザー写経で
  `ImportError` による collection 中断が実際に発覚 ── §2.1)。`pytest_collection_
  modifyitems` は items 全件を受け取る「歴史的フック」であることを踏まえ、
  `item.path` で対象ディレクトリを明示的に絞り込む必要がある。

## テスト観点(`tests/performance/test_generators.py`)

> **対象**: `linear_chain_successors`
> **ドライバ**: このテスト関数
> **スタブ不要** ── 対象が純粋(副作用なし)で外部依存を呼ばないため

| ケース                          | 期待                                                                   |
| ---------------------------- | -------------------------------------------------------------------- |
| `linear_chain_successors(5)` | `{"T0": ["T1"], "T1": ["T2"], "T2": ["T3"], "T3": ["T4"], "T4": []}` |
| `linear_chain_successors(1)` | `{"T0": []}`                                                         |
| `linear_chain_successors(0)` | `ValueError`                                                         |

```bash
uv run pytest tests/performance/test_generators.py -v   # 3 passed(このテスト自体は軽いので performance マーカーは付けない)
uv run pytest --collect-only 2>&1 | tail -5              # 既定実行に含まれることを確認
```

> **写経の罠**: `tests/performance/` に置くテスト全部に機械的に `@pytest.mark.performance`
> を付けたくなるが、本章の `test_generators.py` は純粋関数のテストで一瞬で終わる ──
> マーカーを付けると `addopts` の除外条件に引っかかり既定実行から漏れてしまう。
> マーカーが要るのは実際に大規模入力を計測する 15-2/15-3 のテストだけ。

> uv run pytest --collect-only 2>&1 | tail -5    
> pytestが実際にテストを実行せず、「実行対象として認識したテスト一覧」を確認する

---

次章([Phase-15-2](./Phase-15-2.md))では、この章の `measure` フィクスチャを使って
`_MAX_KNAPSACK_DP_CELLS` を実測再検証する。
