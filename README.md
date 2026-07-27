# SubEtha LP

SubEtha（Private x402 payments, settled on zERC20）の静的ランディングページ。デザインは Claude Design プロジェクト「Subetha LP制作」（`SubEtha LP.dc.html`）で作成し、このリポジトリでは依存なしの静的HTMLとして保守します。

## Files

- `index.html` — self-contained HTML/CSS/JS LP（EN/JA 両言語を内包）
- `assets/web-demo.png` — ガイド付き Web デモのスクリーンショット
- `DESIGN_NOTES.md` — デザインの出自、移植時の変換方針、公開前レビューゲート

## Start locally

```bash
python3 -m http.server 4173
```

Open `http://127.0.0.1:4173/`.

ビルド不要・パッケージインストール不要。Google Fonts（Space Grotesk / IBM Plex）はネットワークがない場合サンセリフのフォールバックで表示されます。

## Page structure

1. Hero: x402 のHTTP決済フローを保ったまま、zERC20 burn / mint で決済し、支払者と受取プロバイダのオンチェーンリンクを残さないという提案。「What the chain sees」パネル付き。
2. Problem: 支払いログ＝戦略ログ（エージェント側の行動漏洩・プロバイダ側の売上漏洩）。
3. How it works: 5ステップフローと、burn と mint がリンクしない理由・導出式。
4. Demo: 実 zERC20 スタック上のガイド付きブラウザデモ紹介。
5. Use cases: 金融リサーチ / B2B調達 / トレーディングBot / AIインフラ / APIプロバイダ。
6. FAQ / Roadmap / Contact / Footer。

## Implemented interactions

- EN / JA 切り替え: `data-lang` ボタン + `aria-pressed`。切り替えで `<html lang>` とタイトルも更新、`localStorage` に永続化。英語が静的デフォルト（`<html lang="en">`）。
- 言語ごとに独立したDOMツリー（`#page-en` / `#page-ja`）。アンカーIDは JA 側に `-ja` サフィックスを付与して重複を回避。
- FAQ は `<details>/<summary>` によるネイティブ開閉。
- Hero とユースケースの CTA は Contact セクションへのページ内アンカー。`mailto:` はアドレスがラベルに見えている Contact ボタンとフッターのみ。Contact にはアドレスのコピー用ボタンあり。
- focus-visible スタイル、`prefers-reduced-motion` 対応、960px / 600px ブレークポイントのレスポンシブ。

## Verification

CI（`.github/workflows/validate.yml`）が PR / main push で以下を検証:

- `<!doctype html>` 先頭・`<html lang="en">`・EN/JA スイッチマーカー・`aria-pressed`・`prefers-reduced-motion`
- 連絡先が人間承認済みアドレス（`mailto:contact@subethalabs.com`）のままであること
- HTML パース・資格情報らしき文字列の混入なし

ブラウザでのデスクトップ/モバイル描画、EN/JA遷移、キーボード操作、コンソールエラーの確認は引き続き人間レビューの対象です。

## Publication review gates

公開前に人間が確認すること: zERC20 の名称・公式関係・利用許諾の表現、プロダクション/監査状況に関するクレーム、デモの実挙動と記載の整合、最終的な公開チャネル。
