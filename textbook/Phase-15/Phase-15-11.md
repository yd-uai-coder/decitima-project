# Phase 15-11: デプロイRunbook + プロジェクト完走(作業単位 15-11)

## この章のゴール

既存の Docker 資産(`Dockerfile`・`docker-compose.prod.yml`・`nginx/nginx.prod.conf`)を
監査し、VPS/Vercel デプロイの手順書を作る。README §15「Deployment」。**監査の過程で、
本番 compose に `worker` サービスが無いという実害のあるギャップを発見した** ──
この章もまた「実測(監査)してから直す」章になった。ユーザー確認により実インフラの
構築(VPS契約・ドメイン取得・Vercelアカウント連携)は行わない ── 設定ファイルと
手順書の整備に留める。

**この章で作成 / 更新するファイル**: `textbook/samples/docker-compose.prod.yml`(新規、
初出 Phase 15。既存ファイルへの追記だが samples 未収録だったため新規扱い)、
`textbook/samples/DEPLOYMENT.md`(新規)。

---

## 1. 発見 ── 本番 compose に `worker` サービスが無い

`decitima-api/docker-compose.prod.yml`(既存、Phase 15 まで samples 未収録)を
`decitima-api/docker-compose.yml`(開発用)と比較すると、開発用には Phase 9-8 で追加した
`worker`(arq)サービスがあるのに、**本番用には無い**:

```bash
grep -n "worker" docker-compose.prod.yml docker-compose.yml
# docker-compose.yml:58:  worker:
# (docker-compose.prod.yml に該当行なし)
```

これは実害のあるギャップ ── `POST /api/v1/jobs`・`POST /api/v1/simulate`(Phase 9-8/10-4)は
`JobRepository` への書き込みまでは成功する(リクエスト自体は 200 で返る)が、それを実際に
処理する arq ワーカーが本番環境に存在しないため、**ジョブが `queued` のまま永久に無応答に
なる**。ヘルスチェックも `/health`(backend の生存確認)しか無く、この種の「静かな機能
欠落」を検知できない。監査で発見できたのは、Phase 15-5 で `app/worker.py` を実際に触った
直後だったため「ワーカーはどこで起動されているか」を辿ったこと ── 単体では見つけにくい
種類のギャップだった。

## 2. 修正 ── 本番 compose に `worker` サービスを追加

開発用の `worker` サービス(Phase 9-8)と同じ image・同じコマンドで追加する
(`backend` サービスと同じ Dockerfile の `runtime` ステージを共有、コマンドだけ arq に
差し替え):

```yaml
# docker-compose.prod.yml(改訂)
  # (Phase 15-11)
  # 本番 compose に worker サービスが無かった ── POST /jobs / POST /simulate は受理される
  # (JobRepository への書き込みまでは成功する)が、それを実際に処理する arq ワーカーが
  # 存在せず、ジョブは queued のまま無応答になる実害のあるギャップだった(監査で発見)。
  worker:
    build:
      context: ./backend
      target: runtime
    image: fastapi-langchain-backend:latest
    restart: unless-stopped
    command: ["uv", "run", "arq", "app.worker.WorkerSettings"]
    env_file:
      - .env
    environment:
      DEBUG: "false"
      ENVIRONMENT: production
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - internal
```

## 3. Dockerfile / nginx.prod.conf の監査 ── 変更不要

- **`Dockerfile`**: `base → builder → runtime` の3段構成、`runtime` は非rootユーザー
  (`app`)・`--reload` 無し。既にマルチステージのベストプラクティスに沿っており変更不要。
- **`nginx/nginx.prod.conf`**: HTTP→HTTPS強制リダイレクト、certbot の ACME challenge
  経路、TLS終端、`/health` プロキシまで揃っている。変更不要(証明書の配置手順のみ
  Runbook に明記)。

---

## まとめ

- 本番 `docker-compose.prod.yml` に `worker` サービスが欠落していることを監査で発見し、
  追加した ── `Dockerfile`/`nginx.prod.conf` は既存資産のまま変更不要だった。
- README §15設計のポイント「テンプレートが既に足場を提供」は Dockerfile/nginx には
  当てはまったが、Phase 9 で追加した DeciTima 固有のワーカーは本番側への反映が漏れていた
  ── テンプレート資産の監査だけでなく、Phase 6〜14 で DeciTima が積み増した部分の
  本番反映漏れも確認する必要があると分かった。
- 実際の VPS/Vercel デプロイ手順は `DEPLOYMENT.md` にまとめ、実インフラは構築しない
  (ユーザー確認どおり教材化のみ)。

## テスト観点

本章はインフラ設定ファイルの監査・追記のみでアプリケーションコードの変更を伴わないため、
専用の pytest は追加しない。`docker-compose.prod.yml` の構文検証のみ行う。

```bash
docker compose -f docker-compose.prod.yml config --quiet   # 構文エラーが無いことを確認
```

---

Phase 15 のまとめは [Phase-15-introduction.md](./Phase-15-introduction.md) §10/§11 を参照。
プロジェクトの完走をもって Phase 0〜15 が一区切りする。
