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
- デザイン原本からの意図的な内容変更: ロードマップ先頭に現在地行（NOW — 動くフロー / ローカルPoC・非本番・未監査）を追加。subetha リポジトリの戦略ドキュメント（PRODUCT-STRATEGY.md / LAUNCH-AND-MOAT.md の主張規律）との整合をオーナーと確認して決定。クロスチェーン拡張（同 §9）は「MVP直後の機能ではない」ため意図的に非掲載。
- ロードマップ更新: 実装済みの facilitator / provider / Python / MCP / CLI / agent policy をPhase 1〜2へ反映し、NOWからデザインパートナー探索を並走させた。商用化の本体を「SDK」ではなくmanaged private payment layerと明記し、permit/self-transfer、実験的batch、accepted/finalized、商用許諾の境界をLP上でも条件付きで表現。
- 対外表示の整理: Mordred、journal recovery、具体的なKYB実装、zERC20 grantの詳細はロードマップ本文から外し、agent-runtime integrations、trusted provider network、licensing and operational readinessという外部向けの抽象度に統一。詳細はdocs・協業資料・内部ロードマップで扱う。
- Phase 2の表現を「Enterprise controls」から「Agent controls & operations / エージェント統制と運用」へ変更。企業向け管理画面ではなく、AIエージェントの支出を予算・Provider・人間承認・決済状態・レポートで制御するControl Planeであることを外部向けに明示。
- 採用戦略を追加: 企業への販売だけでなく、API Provider側の受け入れとAI Agent/Agent Builder側のpayer・runtime採用を別々の導入面として扱う。ロードマップにADOPTION行を追加し、Provider向けのdrop-in x402 adapter / testnet sandbox / onboarding / fee transparencyと、Agent向けのSDK / MCP・Python・CLI / framework integration / safe defaults / reference appsを明記。両面の導入を通じて、ProviderはAPIを変えずに受け入れ、Agentはprivate settlementを自前実装せずに利用できる状態を目標とする。
- CONTACT文言を自然な対象者表現へ更新。「エージェント開発者・APIプロバイダ・投資家」という限定的で硬い呼称を避け、AIエージェントを開発・運用する人、エージェント向けサービス提供者、この領域に関心のある人へ呼びかける表現に統一。英語も同じ意味に調整。
- フッターの作品名由来（『銀河ヒッチハイク・ガイド』のSub-Etha）に関するコピーを削除。著作権・出典上の不要な論点を避け、フッターは公式リンクのみの簡潔な構成とした。
- 技術記事の導線をEN/JA双方に追加。Zenn記事（`https://zenn.dev/peaceandwhisky/articles/6f0b8b672a6f78`）とMedium記事（`https://takuyafujita.medium.com/your-ai-agents-payment-log-is-its-strategy-log-subetha-hides-who-paid-whom-8a5fde719093`）をリンク化した。
- JAヒーローの訴求を「APIの支払いは、公開のまま。／支払者と提供者のつながりは、直接は見えない。」へ変更。Fable相当の独立レビューで、抽象的な「リンクは消える」や匿名決済を想起させる表現を避け、支払い自体は公開される一方、payerとproviderの対応関係が直接は見えないというclaim boundaryを先に伝える案を採用した。
- スクロール体験を強化。固定の進捗バー、IntersectionObserverによるセクション／カード／ロードマップ行の段階的なreveal、EN/JA切替後の表示状態再計算を追加。JavaScript非対応時の表示フォールバックと`prefers-reduced-motion`対応を維持し、演出が情報理解を邪魔しない範囲に限定した。
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

## Content direction update (2026-07-27, Fable レビュー反映)

承認済みのFableレコメンデーションを反映し、「見えなくする」訴求から「何が公開で、何が結びつかず、何が当事者に見えるか」を明示する claim-bounded な訴求へ調整した。

- EN H1 を「AI agents pay APIs. The payment is public. The link is not.」へ変更（JA H1 は既存の claim boundary 型のまま維持）。EN/JA ヒーローの実装表記を「オープンソースのローカルリファレンス実装（公式 zERC20 ツールチェーン上・新トークンなし・フォークなし・未監査・非本番）」に統一。
- 新セクション `#visibility` / `#visibility-ja`（ヒーロー直後）: 公開の場で見えるもの（両端は今日見える／payer↔provider の直接対応はオンチェーンに無い＝Live today）と、当事者に見えるもの（各自の記録による突き合わせ＝Live today、標準化された view key・期限付き監査人開示＝Phase 3 Roadmap・未提供）をチップ付きカードで分離。
- 新セクション `#status` / `#status-ja`（デモ後・ユースケース前）: Today（開発者・実験者向けローカルOSSリファレンス実装、未監査・非本番）/ Next（x402互換レイヤー、providerアダプタ、payer SDK、外部検証、デザインパートナー募集中）/ Future（fleet spend controls、顧客保有 view key、期限付き開示、監査人エクスポート＝ロードマップ・未提供）の3カード + 詳細ロードマップへのリンク。
- 過剰主張の修正: 「対応関係は決して現れない」→ 直接の対応関係はオンチェーンに書かれない、「追跡可能な入金はゼロ」→ 支払者まで遡れる入金は現れない、「売上を読めなくする」→ 支払者単位の追跡可能性・顧客単位の入金を読めなくする、「Design partners — running now / 現在並走」→ now recruiting / 現在募集中。バッチのタイミング・金額相関の注意書きは維持。
- CTA/Contact: ヒーロー第2CTAを「Work with us early → / 初期段階から関わる →」（既存の contact アンカー）へ。Contact は AIエージェント開発者・x402実験者・有料APIプロバイダ・プライバシー/決済インフラエンジニアに PoC 実行とギャップ報告を呼びかけ、組織からのロードマップ要件共有も歓迎する文面へ更新（メール・コピー・GitHub・X の連絡手段は維持）。
- ナビに Visibility / 見える範囲、Status / 現在地 を追加（既存の横スクロールモバイルナビと互換）。
