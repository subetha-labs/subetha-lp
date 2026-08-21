# SubEtha LP

SubEtha の静的ランディングページ。x402-compatible private machine payments と、現行実装に追加された facilitator / participant-scoped payment history / explicit lifecycle を、依存なしのHTMLとして説明します。

## Files

- `index.html` — 現行LP（EN/JA、レスポンシブ、FAQ、言語切替、コピーCTA）
- `index-v3-previous.html` — 改修前のLP保存版
- `assets/web-demo.png` — ガイド付きWebデモのスクリーンショット
- `DESIGN_NOTES.md` — 改修方針・実装内容・公開前ゲート

## Start locally

```bash
python3 -m http.server 4173
```

Open `http://127.0.0.1:4173/`.

## Page structure

1. Hero — payment/link boundary and public ledger visual
2. Problem — payer-side strategy leakage / provider-side revenue leakage
3. Protocol — request → 402 → authorize → accepted → finalized
4. Operational layer — participant-scoped history and explicit lifecycle
5. Current scope — facilitator, history, profile gates, roadmap
6. Use cases — research, providers, agents, trading/procurement, infrastructure
7. Demo — current guided browser demo
8. FAQ / Contact

## Verification

```bash
python3 - <<'PY'
from html.parser import HTMLParser
from pathlib import Path
p = Path('index.html')
s = p.read_text()
HTMLParser().feed(s)
for marker in ['accepted', 'finalized', 'participant-scoped', 'fail-closed', 'data-lang', 'prefers-reduced-motion']:
    assert marker in s, marker
assert 'mailto:' not in s
print('HTML parser: OK')
print('bytes:', len(s.encode()))
PY
```

ブラウザでEN/JA切替、FAQ、コピーCTA、desktop/mobile幅、console error、画像404、reduced-motionを確認してください。

## Publication gates

- zERC20 の名称・公式関係・ライセンス表現
- 実装済み / testnet-enabled / production-gated / roadmap の分類
- accepted / finalized、payment history、offline verificationのclaim boundary
- デモの実挙動と記載の整合
- 公開チャネルとデプロイ先
