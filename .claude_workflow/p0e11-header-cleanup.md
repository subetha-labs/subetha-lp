# P0-E.11 — LP header cleanup (workflow evidence)

Immutable record for the header cleanup task. Branch: `feat/lp-header-cleanup`.
Base commit at start: `37073af feat(lp): add technical Docs links (#6)`.

## 1. Requirements

Problem: the LP header packs wordmark + 10 nav links (Visibility, Problem, How it
works, Demo, Status, Use cases, FAQ, Articles, Roadmap, Documentation) + language
toggle + GitHub pill into one flex row. Below 960px it wraps into a second
horizontal-scroll row; the composition is dense on desktop and awkward/overflowing
on narrow viewports.

Must preserve (hard constraints):
- Both language trees `#page-en` / `#page-ja`; all existing anchor IDs and every
  existing anchor destination reachable from the header (9 section anchors per
  language + official Docs link `https://docs.subethalabs.com/`).
- Language toggle semantics: `data-lang` buttons, `aria-pressed`, `localStorage`
  key `subetha-lp-lang`, `<html lang>` + title update. EN static default.
- GitHub link `https://github.com/peaceandwhisky/SubEtha`.
- `focus-visible` styles, `prefers-reduced-motion` behavior, CI markers
  (`<!doctype html>` first, `<html lang="en">`, `data-lang="en"`, `data-lang="ja"`,
  `aria-pressed`, `prefers-reduced-motion`, `mailto:contact@subethalabs.com`).
- No content-claim changes; no changes to Hero or unrelated sections.
- No new dependencies; no generic hamburger without a complete accessible
  implementation.

Goals:
- Desktop: wordmark + a small set of primary section links; secondary navigation
  (e.g. Articles/Roadmap) reachable without crowding; Documentation and GitHub
  discoverable.
- Mobile: controls fit on the row; full navigation via an accessible compact
  disclosure with keyboard/focus support. No broken overflowing header.

## 2. Design

Composition (identical structure in EN and JA trees):

- Desktop (>960px):
  `wordmark · [Problem, How it works, Demo, Status, FAQ, More ▾] ··· Documentation ↗ · [EN|日本語] · GitHub ↗`
  - "More ▾" is a `<details class="nav-more">` disclosure containing Visibility,
    Use cases, Articles, Roadmap as a small dropdown card. JA labels: 課題 / 仕組み /
    デモ / 現在地 / FAQ primary; その他 ▾ → 見える範囲 / ユースケース / 記事 / ロードマップ.
- Mobile (≤960px): `.nav-links` and standalone Docs link hidden; a
  `<details class="nav-menu">` "Menu / メニュー" button appears. Its panel is a
  full-width sheet anchored under the sticky header listing all 9 section anchors
  plus a separated group with Documentation ↗ and GitHub ↗.
- ≤600px: header GitHub pill hidden (GitHub stays in the menu panel, hero CTA and
  footer); wordmark slightly smaller; tighter gaps. `flex-wrap` kept only as a
  graceful fallback for ultra-narrow (<330px) viewports.

Accessibility rationale: native `<details>/<summary>` is the disclosure pattern
already used by the FAQ — summary is focusable, activatable with Enter/Space, and
exposes expanded state natively. JS progressive enhancement adds: Esc closes and
returns focus to the summary, outside click closes, choosing a link closes, only
one nav disclosure open at a time, and language switch closes any open menus.
Without JS the disclosures still open/close natively. Caret rotation uses the
existing summary-span transition and inherits the existing
`prefers-reduced-motion` override; an explicit `.nav-caret` no-transition rule is
added to the reduced-motion block.

CSS strategy: new rules live in the existing `<style>` block using classes
(`.nav-more`, `.nav-menu`, `.nav-panel`, `.hdr-docs`, `.hdr-github`), following
the file's existing pattern of `!important` media-query overrides against inline
styles. Obsolete rules removed: `.hdr-in { flex-wrap: wrap }` +
`.nav-links { order:3; overflow-x:auto; … }` at 960px, and the meaningless
`.nav-links { grid-template-columns: 1fr }` at 600px.

Explicitly out of scope: Hero, all content sections, footer, copy claims,
scroll-progress/reveal behavior, contact links.

## 3. Taskization

1. Rewrite header CSS: dropdown/panel/menu rules; update 960px and 600px media
   queries; extend reduced-motion block.
2. Rewrite EN header DOM (`#page-en > header`): primary nav + More disclosure +
   Docs link + unchanged lang toggle + GitHub pill + mobile Menu disclosure.
3. Mirror for JA header (`#page-ja > header`) with `-ja` anchors and JA labels.
4. Extend the existing IIFE script: nav-disclosure close behavior (Esc/outside/
   link-click/single-open) and close-on-language-switch.
5. Verification (below), then commit `index.html` only.

## 4. Verification plan

1. **Exact CI validation locally**: run the same Python assertions and credential
   grep as `.github/workflows/validate.yml` against the working tree.
2. **Local HTTP smoke test**: `python3 -m http.server 4173`, `curl` the page,
   confirm HTTP 200 and full byte length.
3. **Browser checks** (headless browser):
   - Desktop (~1440px): header renders on one row, no overflow; More opens/closes;
     anchor links land; lang toggle EN↔JA updates `aria-pressed`, `<html lang>`,
     title, localStorage; focus ring visible on summary.
   - Narrow (~375px): no horizontal overflow of the header; Menu opens the sheet;
     all 9 anchors + Docs + GitHub present; Esc closes and restores focus;
     outside click closes; link click closes and navigates.
   - Console free of errors.
4. **Independent Codex review**: request review of the actual diff via Codex CLI
   with GPT-5.6; if that model is unavailable, report the limitation and record
   the model actually used. Preserve review output below.

## 5. Verification results

- Exact static HTML parse and CI assertions: PASS (`HTML_PARSE_OK`, 107045 bytes, 6 Docs URL occurrences, 2 nav menus).
- Credential scan: PASS (`CREDENTIAL_SCAN_OK`).
- Local HTTP smoke test: PASS (HTTP 200).
- Desktop browser: primary nav, More disclosure, Docs, language toggle, and GitHub render without header overflow; More opens and exposes Visibility / Use cases / Articles / Roadmap.
- Narrow browser evidence from the local verification run: 375px and 320px widths had no horizontal overflow; mobile Menu exposed all section links plus Docs/GitHub; Escape restored focus to summary; link click closed the menu; EN/JA switch updated the page state and aria-pressed values.
- Reduced-motion CSS and focus-visible styles remain present.
- No `.gstack/` browser-session artifacts are included in the change set; generated browser evidence was removed because it contained local tool session metadata.

## 6. Review record

Codex read-only review initially identified only the generated `.gstack/` session artifact and the missing evidence record. The artifact was removed and this verification section was appended; review is rerun before commit.
