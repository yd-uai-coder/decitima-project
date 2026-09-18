# Phase 15-7: セキュリティ監査 + ドキュメント化(作業単位 15-7)

## この章のゴール

README §15「Security」の6項目(Authentication / Authorization / Input Validation /
Rate Limit / CORS / Secret Management)を、既存実装のどのファイルが担っているかで
1項目ずつ監査する。README設計のポイント「テンプレートが既に足場を提供しており作り直さない」を実際に検証する章 ── 結論は「5項目は対応不要、1項目に小さな清掃漏れ」。

**この章で作成 / 更新するファイル**: `textbook/samples/SECURITY.md`(新規)。

---

## 1. 監査手順 ── 各項目を「どのファイルが担っているか」で辿る

一般論のチェックリストではなく、実装ファイルを具体的に読んで確認した:

- **Authentication**: `app/core/security.py`(Argon2ハッシュ、JWT access/refresh + `jti`)
- **Authorization**: `app/services/optimization_read.py::get_problem`/`get_solution`
  (所有者スコープの模範実装、Phase 1)── Phase 6〜15 の全新規エンドポイントがこのパターンを
  踏襲していることを `grep -rn "user_id=user_id" app/services/` で確認
- **Input Validation**: `app/schemas/**`(Pydantic)。SQL インジェクションの手がかりとして
  `grep -rn 'f"SELECT\|execute(f"' app/` → 該当なし(ORM経由のパラメータ化クエリのみ)
- **Rate Limit**: `app/services/rate_limit.py::RateLimiter` + `app/core/config.py` の
  10エンドポイント分の個別設定
- **CORS**: `app/main.py` の `CORSMiddleware(allow_origins=settings.CORS_ORIGINS)`
- **Secret Management**: `.gitignore`(`.env`/`.env.*` 除外)+ `.env.example`(プレースホルダ)

## 2. 発見 ── `.env.example` に Phase 11 で廃止した設定の消し忘れ

`backend/.env.example` に `TAVILY_API_KEY=` が残っていた。Phase 11-7 で Web検索QA機能
(Tavily)を全面廃止した際、`app/ai/tools/tavily.py`・`app/services/chat.py` 等の
**コードは削除**したが、`.env.example` のプレースホルダ行は消し忘れていた
(`Phase-11-introduction.md` の削除ファイル一覧に `.env.example` は含まれていない)。

実害は無い(空のプレースホルダなので秘密情報の漏洩ではない)が、存在しない設定項目が
ドキュメントに残っているのは開発者体験として不正確 ── `SECURITY.md` の本番チェック
リストに削除項目として記録した(`.env.example` は decitima-api リポジトリ直下の
ファイルで samples の対象外のため、本章はコード変更を伴わず削除手順の記録のみ)。

## 3. 他5項目は対応不要 ── 既存資産の再利用で足りている

README §15 設計のポイントの実演: Authentication/Authorization/Input Validation/
Rate Limit/CORS の5項目は、Phase 0〜14 が既に整備した資産(テンプレート由来 + DeciTima
固有の所有者スコープパターン)でそのまま満たされている。作り直しは一切発生しなかった。

---

## まとめ

- README §15 の6項目を実装ファイルベースで監査し、`SECURITY.md`(新規)にまとめた。
- 5項目(Authn/Authz/Validation/RateLimit/CORS)は既存資産で対応済み、コード変更なし。
- 1項目(Secret Management)で `.env.example` の消し忘れ(Phase 11 廃止機能の
  プレースホルダ)を発見、本番チェックリストに削除項目として記録した。

## テスト観点

本章はドキュメント監査のみでコード変更を伴わないため、専用テストは追加しない。
`grep` によるコードベース横断確認の結果は本章 §1/§2 に記録済み。

```bash
grep -rn 'f"SELECT\|execute(f"' app/          # SQL インジェクションの手がかり(該当なし)
grep -n "TAVILY_API_KEY" .env.example         # 消し忘れの確認
```

---

次章([Phase-15-8](./Phase-15-8.md))では Playwright を導入し、Route Planner の E2E を書く。
