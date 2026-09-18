# DeciTima samples │ 作業単位 15-7
# セキュリティ監査(Phase 15-7)

README §15「Security」の6項目(Authentication / Authorization / Input Validation /
Rate Limit / CORS / Secret Management)を、既存実装のどのファイルが担っているかで
1項目ずつ確認した結果。**多くはテンプレートが既に足場を提供しており、作り直していない**
(README §15設計のポイント)。

## 1. Authentication(認証)

| 項目 | 実装 | 状態 |
| --- | --- | --- |
| パスワードハッシュ | `app/core/security.py::hash_password`(Argon2、`pwdlib`) | 健全 |
| トークン | JWT(access 短命 + refresh 長命)、`jti`(一意ID)を含めて Redis での失効管理に対応 | 健全 |
| 失効管理 | `jti` を Redis に記録しログアウト時に無効化(`app/services/auth.py`) | 健全 |

対応不要(テンプレート資産をそのまま再利用)。

## 2. Authorization(認可)

全ての読み取り・書き込みが **所有者スコープ**(`user_id` による絞り込み)を通る ──
`OptimizationReadService.get_problem`/`get_solution`(Phase 1)が模範例で、Phase 6〜15の
全新規エンドポイント(`/explain`・`/recommend`・`/compare`・`/jobs/{id}`)もこのパターンを
踏襲している(他ユーザーのリソースは 404、403 ではない ── 存在の有無も漏らさない設計)。
Phase 15-6 のキャッシュ層でも「所有者チェックはキャッシュ参照より先」を徹底した
(`Phase-15-6.md` §2)。

対応不要。**ただし今後新しいエンドポイントを追加する際は、この所有者スコープパターンから
外れないことを都度確認する**(監査で見つかった穴ではなく、今後のための運用ルール)。

## 3. Input Validation(入力検証)

全リクエストボディは Pydantic スキーマ(`app/schemas/**`)で型・値域を検証する。
判別可能ユニオン(`problem_type` で分岐)・`Field(ge=0)` 等の値域制約・
`model_validator` によるクロスフィールド検証(例: `RouteData.allow_negative` と
負辺の整合性)が Phase 0〜9 で既に整備されている。SQL は SQLAlchemy の ORM/パラメータ化
クエリのみで生文字列結合が無いことを `grep -rn "f\"SELECT\|execute(f\""` で確認した
(該当なし)。

対応不要。

## 4. Rate Limit(レート制限)

`app/services/rate_limit.py::RateLimiter`(Redis `INCR`+`EXPIRE`)が汎用実装。
`resource` 名ごとに時間/日の2ウィンドウで上限を設定でき、Phase 6〜14 の新エンドポイント
(solve/verify/benchmark/job_submit/simulate/recommend/explain/compare)全てに
個別の上限が設定済み(`app/core/config.py`)。

対応不要。

## 5. CORS

`app/main.py` で `CORSMiddleware(allow_origins=settings.CORS_ORIGINS)`。既定値は
`["http://localhost:3000"]`(開発用)、本番は `.env` で上書きする設計。値そのものは
env 経由で外から差し込む形になっており、コードの変更は不要(デプロイ時に
`CORS_ORIGINS` を実際のフロントエンドのドメインに設定するだけ)── 手順は
`Phase-15-11.md` のデプロイ Runbook に明記する。

対応不要(デプロイ手順の明記のみ、15-11 で対応)。

## 6. Secret Management(秘密情報管理)

`.env`/`.env.*` はルートの `.gitignore` で除外済み、`.env.example`(実際の値を含まない
プレースホルダ)のみコミットされている。`GOOGLE_API_KEY` 等の秘密情報は環境変数経由。

**監査で見つかった小さな穴**: `backend/.env.example` に `TAVILY_API_KEY=` が残っている ──
Phase 11-7 で Web検索QA機能(Tavily)を全面廃止した際、コードは削除したが
`.env.example` のプレースホルダ行を消し忘れていた。実害は無い(空プレースホルダなので
秘密情報の漏洩ではない)が、存在しない設定項目が残っているのはドキュメントとして
不正確 ── この行を削除する(該当ファイルは decitima-api リポジトリ直下、samples の
対象外なので本 Phase では変更手順のみ記録し、ユーザーが直接削除する)。

---

## 本番チェックリスト(デプロイ前に確認)

- [ ] `.env` の `JWT_SECRET_KEY` をランダムな64文字以上の値に変更する(`.env.example` の
      プレースホルダのまま本番投入しない)
- [ ] `CORS_ORIGINS` を実際のフロントエンドのドメインに設定する
- [ ] `ENVIRONMENT=production` を設定する(`app/main.py` が Swagger/OpenAPI docs を
      自動的に無効化する ── `_docs_enabled = settings.ENVIRONMENT != "production"`)
- [ ] `DEBUG=false` を設定する(SQLAlchemy のクエリログ等が無効化される)
- [ ] `backend/.env.example` から `TAVILY_API_KEY=` を削除する(上記6項目参照)
- [ ] `DATABASE_URL`/`REDIS_URL` を本番用の接続先に設定する
