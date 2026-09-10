# Phase 2-1: Input Validation の拡充(Pydantic)(作業単位 2-1)

## この章のゴール

`Phase-0-6.md` §2.1 の 2 段階のうち **① Input Validation**(構文・型・単項の値域 +
フィールド間・コレクションの整合)を Pydantic に寄せきる。Phase 1 では `ShiftSlot` の
`start_hour` / `end_hour` を個別に `Field(ge/le)` で縛っただけで、「`end_hour > start_hour`」
のような **2 フィールドの関係** は未チェックだった(`Phase-1-1.md` §2.3 に「Phase 2 で
`model_validator` を足す」と書いてある)。ここでそれを足す。

- `ShiftSlot` に `end_hour > start_hour` の `model_validator`
- `ShiftSlot` に `day` を ISO 日付に限定する `field_validator`(`Phase-2-4` の連続勤務日数の検証がここをパースするので、崩れた日付は入口で弾く)
- `ShiftData` に slot id / staff id の重複を弾く `model_validator`(`Phase-2-2` / `Phase-2-4`は id で索引を作るため)

route 側は Phase 1 の `Field(ge=0)`(エッジ weight)で足りるので **新しい Input Validation は
無い**。この非対称は route のデータ構造が単純だからで、それ自体が設計の説明になる。

**この章で作成 / 更新するファイル**: なし。
**既存ファイルへの変更**: `app/domain/problems/shift_scheduler.py`(Phase 1 で作成した葉モジュール。
Phase 2 の現行版が `textbook/samples/app/domain/problems/shift_scheduler.py`。Phase 1 側には「以降 Phase で修正予定」マーカーを付ける)。

対応サンプル: `textbook/samples/app/domain/problems/shift_scheduler.py`。
テストは `textbook/samples/tests/unit/test_shift_input_validation.py`。
設計は `Phase-0-6.md` §2.1 / §2.2。

---

## 1. `field_validator` と `model_validator` の使い分け

|                                  | 何を見る                             | いつ書く                          |
| -------------------------------- | -------------------------------- | ----------------------------- |
| `Field(ge=, le=, ...)`           | 1 フィールドの値域。宣言的                   | まずこれで済むなら十分                   |
| `@field_validator("x")`          | 1 フィールドの値を、宣言では書けない条件で(パース可能性など) | `day` が ISO 日付か               |
| `@model_validator(mode="after")` | **複数フィールドの関係**、コレクション全体          | `end_hour > start_hour`、id 重複 |

`mode="after"` はすべてのフィールドが型変換済みの状態で呼ばれるので、`self.end_hour` のように普通に属性アクセスできる。`ValueError` を投げれば Pydantic が `ValidationError`(FastAPI 経由なら **422**)にまとめてくれる。

---

## 2. `ShiftSlot` ── 単項 + フィールド間

```python
# app/domain/problems/shift_scheduler.py(要点。全文は samples)
from datetime import date
from pydantic import BaseModel, Field, field_validator, model_validator


class ShiftSlot(BaseModel):
    id: str
    day: str                                  # ISO 日付 "2026-09-01"
    start_hour: int = Field(ge=0, le=23)      # 単項の値域は Field のまま
    end_hour: int = Field(ge=1, le=24)
    required_headcount: int = Field(ge=1)
    required_skills: list[str] = Field(default_factory=list)

    @field_validator("day") #dayフィールドの値を検証する関数であることを宣言
    @classmethod
    def _day_is_iso_date(cls, value: str) -> str:
        try:
            date.fromisoformat(value)               # パースできなければ ValueError
        except ValueError as exc:
            raise ValueError(f"day must be an ISO date (YYYY-MM-DD), got {value!r}") from exc
        return value

    @model_validator(mode="after")
    def _end_after_start(self) -> "ShiftSlot":
        if self.end_hour <= self.start_hour:       # ここは 2 フィールドの関係
            raise ValueError(...)
        return self
```

> `field_validator` は `@classmethod` にする(値だけを受け取り、インスタンスはまだ無い)。
> `model_validator(mode="after")` は `self` を受け取り `self` を返す。

> **@classmethodは、「インスタンスではなく、クラスを操作するためのメソッド」**
> 
> | 種類              | 第1引数   | クラス・インスタンスへのアクセス |
> | --------------- | ------ | ---------------- |
> | 通常のメソッド         | `self` | インスタンスにアクセス      |
> | `@classmethod`  | `cls`  | クラスにアクセス         |
> | `@staticmethod` | なし     | どちらにも自動アクセスしない   |

---

## 3. `ShiftData` ── コレクションの整合

```python
# app/domain/problems/shift_scheduler.py(つづき)
class ShiftData(BaseModel):
    problem_type: Literal["shift_scheduling"] = "shift_scheduling"
    staff: list[Staff]
    slots: list[ShiftSlot]
    max_weekly_hours: float = 40
    max_consecutive_days: int = 5

    @model_validator(mode="after")
    def _unique_ids(self) -> "ShiftData":
        # Semantic Validation(2-2)と Verification(2-4)は {id: obj} の辞書を作る。
        # 重複があると後段が黙って壊れるので、明らかに崩れた入力としてここで弾く
        slot_ids = [s.id for s in self.slots]
        staff_ids = [s.id for s in self.staff]
        if len(slot_ids) != len(set(slot_ids)):
            raise ValueError("slot ids must be unique")
        if len(staff_ids) != len(set(staff_ids)):
            raise ValueError("staff ids must be unique")
        return self
```

**なぜ Input Validation に置くか**: id の一意性は「この入力が壊れているか」の判定で、問題ドメインの知識(スタッフが足りるか等 = Semantic、`Phase-2-2`)ではない。Pydantic モデルを構築した時点で保証できるものは Pydantic に寄せる、が `Phase-0-6.md` §2.2 の原則。

---

## 4. route 側に足すものが無い理由

`RouteEdge.weight = Field(ge=0)` は Phase 1 で入れた(負辺は Dijkstra の前提を壊す)。
`start` / `goal` が nodes に居るか、エッジ端点が nodes に居るか、は **問題全体を見ないと
分からない**ので Semantic Validation(`Phase-2-2`)の領分。route の Input Validation は
Phase 1 で完了している。

「shift は Input Validation が増え、route は増えない」── これはデータ構造の複雑さの差で、
`domain/` のどのモデルにどれだけ validator が付くかは、そのモデルが表す現実の複雑さを映す。

---

## 5. 既存への変更の当て方(写経手順)

1. `textbook/samples/app/domain/problems/shift_scheduler.py` を `decitima-api/backend/app/domain/problems/shift_scheduler.py` に上書き写経(Phase 1 版との差分は import 3 つと validator 3 つ)。
2. 共有 `textbook/samples/app/domain/problems/shift_scheduler.py` は冒頭コメントに `改訂 Phase 2` があり、`op` → `operator` の是正は `# (Phase 2-1)` タグで示される(進行のルール #12。旧: Phase 1 samples 本体に「サンプル修正」マーカーを付けていた)。
3. `uv run pytest tests/unit/test_shift_input_validation.py` → 緑。既存の `test_problem_schema.py` も緑のまま(fixture の日付・時刻はすべて妥当)。

---

## 6. テスト観点(`textbook/samples/tests/unit/test_shift_input_validation.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> 
> - **対象**: `ShiftSlot` / `ShiftData` の `field_validator` / `model_validator`
> - **ドライバ**: テスト関数(`pytest.raises(ValidationError, match=...)`)
> - **スタブ**: **不要** ── 対象は純粋な値オブジェクトで、DB・I/O・時刻・乱数を一切呼ばない
>   (`Phase-0-3.md` の純粋レイヤー)。スタブが要る = その依存に結合しているサイン。

| ケース                          | 期待                                                                   |
| ---------------------------- | -------------------------------------------------------------------- |
| 妥当なスロット                      | 構築成功                                                                 |
| `start_hour=14, end_hour=14` | `ValidationError`(`match="end_hour"`)                                |
| `day="Sept 1"`               | `ValidationError`(`match="ISO date"`)                                |
| `start_hour=-1`              | `ValidationError`(単項値域は `Field(ge=0)` が担う ── `model_validator` ではない) |
| slot id 重複 / staff id 重複     | `ValidationError`(`match="... ids must be unique"`)                  |

`uv run pytest tests/unit/test_shift_input_validation.py` と、可能なら
`uvx pyright app/domain/problems`(standard, 0 errors)。

---

## 7. まとめ

- Input Validation は Pydantic に寄せる。`Field` で足りなければ `field_validator`(単項)/
  `model_validator`(フィールド間・コレクション)。
- `ShiftSlot`: `end_hour > start_hour` と `day` の ISO 日付。`ShiftData`: id 重複を弾く。
- route は Phase 1 で Input Validation が完了しているので追加なし。この非対称はデータ構造の
  複雑さの差。
- Semantic Validation(問題全体の整合)は次章。

次章([Phase-2-2](./Phase-2-2.md))では、作業単位 2-2 ── Semantic Validation を problem_type
ごとの検査関数レジストリに切り出し、`services/validation.py` をそれを回すだけの形にする。
