# DeciTima samples │ 作業単位 15-11
# デプロイ Runbook(教材)

README §15「Deployment」── GitHub → GitHub Actions → Docker → VPS(API)、
Next.js → Vercel(UI)。**本 Runbook は手順書のみ。実際の VPS契約・ドメイン取得・
Vercelアカウント連携は行わない**(ユーザー確認による教材化のみの方針、
`Phase-15-introduction.md` 参照)。

## API(decitima-api)── GitHub Actions → Docker → VPS

前提: `docker-compose.prod.yml`(Phase 15-11 で `worker` サービスを追加済み)・
`nginx/nginx.prod.conf`・`backend/Dockerfile` は既に本番投入可能な状態。

1. **CI(`.github/workflows/backend-ci.yml`、Phase 15-10)** が `main` へのプッシュで
   lint/型チェック/テスト/Dockerビルドを検証する。
2. **VPS への配置**(手動、または CI からの SSH デプロイステップとして拡張可能):
   ```bash
   # VPS 上で(初回)
   git clone <decitima-api リポジトリ> && cd decitima-api
   cp .env.example .env   # 実際の値に書き換える(SECURITY.md の本番チェックリスト参照)
   mkdir -p nginx/certs && # certbot 等で発行した fullchain.pem/privkey.pem を配置
   docker compose -f docker-compose.prod.yml up -d --build

   # 更新時
   git pull && docker compose -f docker-compose.prod.yml up -d --build
   ```
3. **ヘルスチェック**: `curl https://<domain>/health` が 200 を返すことを確認。
4. **ロールバック**: `git checkout <前のコミット> && docker compose -f docker-compose.prod.yml up -d --build`
   (JSONB中心のスキーマのため、多くの変更は `alembic downgrade` 無しでも後方互換 ── ただし
   新テーブル追加を伴う Phase(Phase 9 の `jobs` 等)のロールバックは `alembic downgrade` も
   合わせて検討する)。

## UI(decitima-ui)── Next.js → Vercel

1. Vercel にリポジトリを接続(GitHub 連携、`main` ブランチへの自動デプロイ)。
2. 環境変数を1つ設定するだけでよい:
   - `NEXT_PUBLIC_API_URL` = デプロイした API の公開URL(例: `https://api.example.com`)
3. ビルドコマンド・出力設定は Next.js の既定のまま(`next.config.ts` に
   `output: "standalone"` 等の特別な設定は無い ── Vercel はネイティブに Next.js を
   ビルドするため、Docker化を意識した設定は不要)。
4. プレビューデプロイ(PRごとの自動プレビュー)は Vercel の既定機能をそのまま使う。

## セキュリティ・CORS との連携

- API 側の `CORS_ORIGINS`(`.env`)に、Vercel が発行するドメイン(本番 + プレビュー)を
  設定する(`SECURITY.md` §5)。
- `JWT_SECRET_KEY`・`GOOGLE_API_KEY` 等の秘密情報は API 側の `.env` にのみ置く
  (UI 側は `NEXT_PUBLIC_*` 以外の秘密情報を持たない設計 ── `NEXT_PUBLIC_` プレフィックスは
  ブラウザに露出するため、秘密情報をこの名前空間に置かないことを Vercel 側の環境変数
  設定時にも確認する)。

## 未実施(教材化のみ)

- 実際の VPS 契約・ドメイン取得・DNS設定
- 実際の Vercel プロジェクト作成・GitHub連携
- 実際の TLS証明書発行(certbot の実行)
- 本番相当の負荷でのリハーサル(README §15「Performance」の一部。Phase 15-1〜15-6で
  アルゴリズムレベルの大規模入力テストは実施済みだが、HTTPレベルの負荷テストは見送った
  ── `Phase-15-introduction.md` §7 非スコープ参照)
