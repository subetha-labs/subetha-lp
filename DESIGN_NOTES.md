# SubEtha LP — Design Notes

Status: Claude Design 移植版（v3）。旧 vision-led 版（`feat/vision-led-lp` 以前の `index.html`）は廃止。

## Provenance

- デザイン原本: Claude Design プロジェクト「Subetha LP制作」（projectId `1e3dd830-2a95-4f5d-ae27-7be428263747`）の `SubEtha LP.dc.html`。
- `assets/web-demo.png` は `subetha` リポジトリ `docs/images/web-demo.png` のオリジナル（デザインプロジェクト側の同名アセットと同一ソース）。

## Porting decisions (.dc.html → static index.html)

Claude Design のコンポーネント形式は独自ランタイム（`<x-dc>` / `<sc-if>` / `{{ props }}` / `style-hover` / DCLogic）に依存するため、次の変換で静的化した:

- `<sc-if isEn/isJa>` の2ツリーを `#page-en` / `#page-ja` として両方DOMに保持し、`hidden` 属性で切り替え。言語ボタンは `data-lang` + `aria-pressed`、選択は `localStorage`（キー `subetha-lp-lang`）に永続化。DCLogic の挙動と同等。
- props のデフォルト値を焼き込み: contact = `pioneerandf@gmail.com`、GitHub = `github.com/peaceandwhisky/SubEtha`、X = `x.com/peaceandwhisky`。
- `style-hover` 属性 → ホバー用CSSクラス（`.h-*`、インラインスタイルに勝つため `!important`）。
- JA ツリーのセクションIDに `-ja` サフィックスを付与し、ID重複とアンカー不整合を解消。
- デザインには無いレスポンシブ（960px / 600px でグリッド折り畳み・ナビ横スクロール）、focus-visible、`prefers-reduced-motion` を追加。CI の必須マーカーを維持。
- デザイン原本からの意図的なUX変更: Hero「Get in touch / 連絡する」とユースケースカード「Tell us about it → / 相談する →」の `mailto:` を Contact セクションへのページ内アンカーに変更（ラベルからメール起動が予測できず、メールクライアント未設定のデスクトップで離脱要因になるため）。Contact セクションにはアドレスのコピー用ボタンを追加（Clipboard API + `execCommand` フォールバック）。`mailto:` はアドレスがラベルに明示された Contact ボタンとフッターのみに残す。

再生成が必要な場合、変換スクリプトはセッションのスクラッチパッド（`build_lp.py`）にあり、原本はClaude Design側に残っている。手直しは `index.html` を直接編集してよい。

## Claim posture change from v2

- 連絡先は `[ CONTACT URL TBD ]` プレースホルダから実メールアドレスに変更（人間がデザイン内で決定済み）。CI の該当アサーションも実アドレス維持チェックに更新。
- Hero は「Private x402 payments · settled on zERC20」を正面に出す。「Built on the official zERC20 toolchain」は公式ツールチェーン**上に**構築という依存関係の記述であり、公式パートナーシップの主張ではない。
- FAQ で明示的に否定していること: ミキサー/匿名決済ではない、新トークンなし、フォークなし。treasury は mint 時に公開され、隠すのは支払者との対応関係のみ。view key による監査可能な開示はロードマップに明記。

## Open review gates (before publication)

1. zERC20 の名称・ロゴ・公式関係・商用利用の許諾表現の最終確認。
2. デモ記載（実 zERC20 スタック、permit モード、バッチ teleport）と実装の整合確認。
3. プロダクション readiness / 監査 / 法規制まわりのクレーム最終確認。
4. 公開チャネルとデプロイ先の決定。
