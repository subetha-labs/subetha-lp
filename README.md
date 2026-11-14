# SubEtha LP

SubEtha の静的ランディングページ（subethalabs.com）。SubEtha v2 を、依存なしの HTML として x402 Provider 向けに説明します:
顧客は無改造の公式 x402 クライアントで zUSDC（wrap した USDC）を払い、注文ごとに異なる受取アドレスを使う。payer・金額・token・時刻は公開のまま。
テストネット、設計パートナー向け。

## Files

- `index.html` — 現行 LP（EN/JA、レスポンシブ、FAQ、言語切替、コピー CTA）
- `router/index.html`, `router/llms.txt` — SubEtha Router のページ（別製品）
- （V1 時代の LP 保存版 `index-v3-previous.html` は 2026-11-14 に削除。旧 URL は `_redirects` で引き続き `/` へ 302）
- `assets/` — ブランド、モバイル CSS/JS
- `_redirects` — Cloudflare Pages の配信境界: 旧 archive URL と、`scripts/` `tests/` `.github/` `.claude_workflow/` `README.md` `DESIGN_NOTES.md` を `/` へ 302
- `scripts/` — オフラインの検証スクリプト（下記）
- `tests/claims/`, `tests/output/` — ガードの fixture。fail 系は `*.b64`（base64）で格納し、public repo に禁止表現や D3 形状の平文を置かない。読むときは `base64 -d`、直すときは平文を編集して再エンコードする（合成値のみ。実際のホスト名・パス・アドレス・価格は使わない）
- `DESIGN_NOTES.md`, `.claude_workflow/` — 設計・検証ノート

## Start locally

```bash
python3 -m http.server 4173
```

Open `http://127.0.0.1:4173/`.

## Page structure

1. Hero — 見出し、必須 subline（全修飾語）、hosted testnet の公開台帳の読み方
2. Problem (`#problem`) — 買い手側の利用の露出 / Provider 側の売上の露出（仮説と明記）
3. How it works (`#how-it-works`) — 標準 x402 `exact` の 5 ステップ（hosted testnet 構成と明記）、配信のあと、構成図
4. Who sees what (`#visibility`) — 公開チェーン / 買い手 / Provider / 運用者（hosted と self-run は別行）/ 直接結び付かないもの / 公開 withdraw、相関、信頼境界
5. For Providers (`#providers`) — 変わらないもの・変わるもの、hosted の配信リスク開示、必要なもの、登録の概要、ソースとライセンス、Docs `/v2/providers/`
6. Status (`#status`) — 日付つきの repository の記録、検証の限界、計画、hosted が約束しないもの、パッケージとライセンス、Docs `/v2/status/`
7. FAQ (`#faq`) — 匿名か、既存 x402 との両立、顧客側の要件、Router との違い、本番利用、ソース公開、「配信済み」の意味
8. Contact (`#contact`) — コピー CTA、X、テストネット登録の相談

JA ブロックの id は `-ja` 付き。

## Verification

CI（`.github/workflows/validate.yml`）と同じ手順:

```bash
python3 -B scripts/check-private-source-links.py            # 配信インベントリ、_redirects、v2 ページ契約、D3 形状、D4 リンク
python3 -B scripts/check-private-source-links.py --fixtures # 出力ガードの fixture
python3 -B scripts/check-private-source-links.py --repo     # public repo 全体に D3/D4
python3 -B scripts/check-claims.py --fixtures               # claims ガードの fixture
python3 -B scripts/check-claims.py                          # 配信インベントリの主張レベル検査
python3 scripts/check-router.py
python3 scripts/check-mobile-layout.py
python3 -B scripts/check-mobile-scope.py
python3 -B scripts/check-private-source-links.py --list     # URL・コマンド・金額・NAME=・トークン様値の棚卸し（目視レビュー用）
```

モバイル作業の境界ゲート（`python3 -B scripts/check-router.py --scope mobile --base <base>`）は、head ブランチ名が `mobile/` で始まる PR にだけ CI が適用します（2026-11-14 以降）。それ以外のブランチでモバイル系ファイル（`assets/mobile.css`、`assets/mobile-nav.js`、`scripts/check-mobile-layout.py`、`scripts/check-mobile-scope.py`）を変更した場合は通常の変更として扱い、CI は差分の stat を記録するだけです。モバイル契約（`check-mobile-layout.py`）とスコープ fixture（`check-mobile-scope.py`）は全 PR と `main` への push で実行されます。

HTML マーカー（CI）: `exact`, `EIP-3009`, `mined receipt`, `zUSDC`, `testnet`, `public`, `independently quantified`, `correlation`。
構造: doctype、`lang="en"`、`data-lang` EN/JA、`aria-pressed`、`prefers-reduced-motion`、`mailto:` なし、コピー CTA。

claims ガードの例外は 1 文・1 出現ごとに `<!-- claims-ok rule=<rule> text="<文全体>" reason=denial|limitation|plan|technical -->` で付けます。
行・段落・ページ単位の免除はありません。

ブラウザで EN/JA 切替、FAQ、コピー CTA、390px / 1280px、console error、reduced-motion を確認してください。

## Publication gates

- 文言の根拠は内部の主張マトリクスに固定（主張 ID で参照。マトリクス自体は repo に置かない）
- 非公開のホスト名・パス・テンプレート・アドレス・価格・資格情報・private repo リンクを公開物に載せない
- hosted testnet と self-run facilitator の構成を 1 文・1 行・1 図に混ぜない
- merge は公開（Cloudflare Pages）。オーナー承認が必要
