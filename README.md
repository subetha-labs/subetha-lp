# SubEtha LP — Vision-led review draft

公開前の静的LP。Heroと主要ストーリーの主語を「PoCの説明」から、SubEthaがagent-native internetに向けて実現しようとしている支払い基盤・境界設計・利用シナリオへ変更した、内部レビュー用アーティファクトです。

## Files

- `index-v2.html` — self-contained HTML/CSS/JS LP
- `DESIGN_NOTES.md` — vision-led copyの意図、claim boundary、未確定事項

## Start locally

```bash
python3 -m http.server 4173
```

Open `http://127.0.0.1:4173/index-v2.html`.

No build step or package install is required. Google Fonts are optional; local fallback stacks are included.

## Message architecture

1. Hero: SubEtha's project vision — payment rails for agents; intended participants; the boundary between paying, receiving value, and accountability.
2. Why now: agent/API-era payment needs a new boundary design, with concrete future scenarios.
3. Boundary: participant, observer, responsibility, and visibility map.
4. Validation: the vision is tested through a local / non-production PoC, without making the PoC the hero or CTA.
5. Current status / FAQ / footer: unaudited and non-production qualifiers remain explicit.
6. CTA: invite discussion of a use case, not a production signup or commercial offer.

English is the default (`<html lang="en">`). EN / JA switches preserve the same vision and claim boundaries. Both languages cover the Hero, why-now narrative, boundary map, current status, CTA, FAQ, and footer qualifiers.

## Implemented interactions

- Sticky navigation with mobile menu toggle.
- Anchor navigation to the narrative sections.
- FAQ disclosure buttons with `aria-expanded` state.
- EN / JA buttons with `aria-pressed`; switching updates document language and title.
- Keyboard focus-visible states and `prefers-reduced-motion` support.
- Responsive desktop/mobile layout.

The contact CTA intentionally remains a non-submitting `[ CONTACT URL TBD ]` placeholder until a human-approved destination exists.

## Verification record

Run from this directory:

```bash
python3 - <<'PY'
from pathlib import Path
from html.parser import HTMLParser

path = Path('index-v2.html')
text = path.read_text(encoding='utf-8')
assert text.startswith('<!doctype html>')
assert '</html>' in text
assert text.count('<script>') == 1
assert '<html lang="en">' in text
assert 'Build <em>payment rails</em>' in text
assert 'prefers-reduced-motion' in text
assert 'aria-expanded' in text and 'aria-pressed' in text
assert 'LOCAL / NON-PRODUCTION POC ONLY' in text
HTMLParser().feed(text)
print('HTML_PARSE_OK')
print(f'BYTES={path.stat().st_size}')
PY
```

Browser review remains required for desktop/mobile rendering, EN/JA transitions, keyboard FAQ/menu behavior, console errors, and horizontal overflow.

## Publication review gates

This is a static internal-review artifact, not a production service, commercial offer, audited security product, complete-anonymity claim, or official zERC20 partnership statement. Before publication, a human must confirm implementation evidence, real-process HTTP E2E behavior, dependency/version/artifact boundaries, naming and permission conditions, contact destination, and the final claim matrix. No publish, deploy, external share, or push was performed.
