# Phase 2-5: `POST /api/v1/verify`(作業単位 2-5)

## この章のゴール

問題 + 候補解を渡して **検証だけ** 実行するエンドポイントを生やす。`Phase-0-7.md` §2 で
MVP エンドポイントに入っている(`POST /solve` に次ぐ 2 本目)。

- `VerifyRequest` / `VerifyResponse`(`Phase-0-7.md` §3.2)
- `VerifyService`(検証器を HTTP ユースケースに包む。DB を触らない)
- `app/api/routes/verify.py`(薄いルート)
- `verify_router` を集約に追加(進行のルール #15 ── ルートを作る章で集約する)
- `resource="verify"` のレート制限

**この章で新規作成するファイル**: `app/services/verify.py`、`app/api/routes/verify.py`。
`VerifyRequest` / `VerifyResponse` は `app/schemas/optimization.py`(`Phase-1-6` で作成済み)に足す。
**既存ファイルへの追記**: `app/core/config.py`(§1)、`app/api/routes/__init__.py`(§4 ──
`verify_router` の集約)。

対応サンプル: `samples/app/services/verify.py`, `samples/app/api/routes/verify.py`,
`samples/app/schemas/optimization.py`。
テストは `samples/tests/api/test_verify_api.py`。
設計は `Phase-0-7.md` §3.2 / §6。

---

## 1. settings への追記(既存ファイル)

`app/core/config.py` の `class Settings`、`SOLVE_TIMEOUT_SECONDS` の下に 1 行:

```python
# app/core/config.py の class Settings 内
VERIFY_RATE_LIMIT_PER_HOUR: int = 60
```

verify は純粋・軽量(DB もアルゴリズムも動かさない)なので日次上限は要らず、時間上限だけ
やや緩め。任意ペイロードを受けるのでレート制限自体は付ける。

---

## 2. スキーマ(既存ファイルへの追記)

```python
# app/schemas/optimization.py(SolveRequest/Response の下に追記)
class VerifyRequest(BaseModel):
    problem: OptimizationProblem
    solution: CandidateSolution

class VerifyResponse(BaseModel):
    status: str                        # "valid" | "invalid" | "infeasible"
    violations: list[ConstraintViolation]
    metrics: dict[str, float]
```

`VerifyResponse` は **解そのものを返さない** ── クライアントが送ってきたものなので。返すのは
検証の結果(status / violations / metrics)だけ。`ConstraintViolation` は
`app/domain/solutions/solution.py` から import(既に schemas が domain を薄く包む形)。

---

## 3. `VerifyService` とルート

```python
# app/services/verify.py(要点。全文は samples)
class VerifyService:
    def __init__(self, redis: Redis) -> None:
        self._verification = SolutionVerificationService()
        self._rate_limiter = RateLimiter(redis, resource="verify",
            limits=[RateLimit(3600, settings.VERIFY_RATE_LIMIT_PER_HOUR)])

    async def verify(self, *, user_id, request: VerifyRequest, bypass_rate_limit=False) -> CandidateSolution:
        if not bypass_rate_limit:
            await self._rate_limiter.enforce(str(user_id))
        return self._verification.verify(request.problem, request.solution)
```

```python
# app/api/routes/verify.py(要点。全文は samples)
router = APIRouter(prefix="/verify", tags=["verify"])

@router.post("", response_model=VerifyResponse)
async def verify(payload: VerifyRequest, redis: RedisDep, current_user: CurrentUserDep) -> VerifyResponse:
    verified = await VerifyService(redis).verify(
        user_id=current_user.id, request=payload,
        bypass_rate_limit=current_user.is_superuser,
    )
    return VerifyResponse(status=verified.status, violations=verified.violations, metrics=verified.metrics)
```

- **`SessionDep` を取らない** ── verify は永続化しないので DB セッション不要。solve との
  明確な違い。
- **Validation を走らせない** ── verify は「解けるか」でなく「この解が条件を満たすか」を見る。
  問題が Semantic に微妙(遠回りが必要等)でも、解の検証はできる(`Phase-0-7.md` §3.2)。
  Input Validation(Pydantic)は `VerifyRequest` を組む時点で当然かかる。
- 解が hard 違反 → `status="invalid"` を **200** で返す。エラーではない。

---

## 4. `verify_router` を集約に追加(既存ファイルへの追記)

`app/api/routes/__init__.py`(進行のルール #15 ── `test_verify_api.py` がルート登録に依存):

```python
# app/api/routes/__init__.py
from app.api.routes.verify import router as verify_router     # ← 追加
# ...
api_router.include_router(verify_router)                       # ← 追加
```

---

## 5. 既存への変更の当て方(写経手順)

1. `samples/app/schemas/optimization.py` で既存を上書き(`VerifyRequest` / `VerifyResponse` が
   増えるだけ。`Phase-1-6/1-7` の内容は不変)。
2. `samples/app/services/verify.py`、`samples/app/api/routes/verify.py` を新規写経。
3. `app/core/config.py` に `VERIFY_RATE_LIMIT_PER_HOUR` を 1 行、`app/api/routes/__init__.py` に
   `verify_router` を 2 行足す(samples には含めない)。
4. `samples/tests/api/test_verify_api.py` を新規写経。
5. `uv run pytest tests/api/test_verify_api.py` → 緑。

---

## 6. テスト観点(`samples/tests/api/test_verify_api.py`)

> **テスト対象 / ドライバ / スタブ**(進行のルール #14):
> - **対象**: `POST /api/v1/verify` の契約(ルート + `VerifyService` + `SolutionVerificationService`)
> - **ドライバ**: `httpx.AsyncClient`(`api` フィクスチャの認証付きクライアント)+
>   `create_access_token`(認証なしケース)
> - **スタブ / テストダブル**: FastAPI 依存差し替え ── `get_redis` → `FakeRedis`
>   (RateLimiter の Redis の代役)。`get_db` も差し替わるが verify は使わない。
>   **`SolutionVerificationService` は本物**(純粋)。

| ケース | 期待 |
| --- | --- |
| route 有効解 | 200 / `status="valid"` / `violations == []` |
| 禁止エッジを使う route 解を e_bd 禁止の問題で検証 | 200 / `status="invalid"` / `violations` に `forbidden` |
| shift 有効解 | 200 / `status="valid"` / `metrics["labor_cost"] == 21500` |
| shift 人数不足解 | 200 / `status="invalid"` |
| 認証ヘッダなし | 401 |

`uv run pytest tests/api/test_verify_api.py` /
`uvx pyright app/services/verify.py app/api/routes/verify.py`。

---

## 7. まとめ

- `POST /verify` = 問題 + 解 → `SolutionVerificationService.verify` → status / violations /
  metrics。DB を触らず、Validation も走らせない。
- `VerifyService` は検証器をレート制限で包むだけ。ルートは薄い。
- hard 違反解も 200(`status="invalid"`)。エラーにしない。
- `verify_router` はこの章で集約に足す(進行のルール #15)。

次章([Phase-2-6](./Phase-2-6.md))では、作業単位 2-6 ── `status="invalid"` の解が solve / verify /
取得系を通して「エラーでなく結果」として一貫して扱われることを確認する。
