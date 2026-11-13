# SubEtha LP v2 rewrite — verification note (2026-11-13)

Branch `feat/v2-lp-20261113` (base `main` @ `fae6e5e`). Companion to `v2-lp-design-20261113.md`. Raw logs, the
full diff and Codex transcripts are local-only (git-excluded `.local-review/`), not committed. This note contains
no internal endpoint, address, path template, price, credential or private repository link.

## 1. CI-equivalent checks run locally (all green)

| step | command | result |
|---|---|---|
| HTML parse + structural and v2 claim markers | the `validate.yml` Python block | `HTML_PARSE_OK` |
| served inventory, redirects, v2 page contract, D3, D4 | `python3 -B scripts/check-private-source-links.py` | `PRIVATE_SOURCE_LINKS_OK` (17 files), `ARCHIVE_REDIRECT_CONFIG_OK`, `ROOT_CONTRACT_OK` |
| output-guard fixtures | `… check-private-source-links.py --fixtures` | `OUTPUT_FIXTURES_OK` 36 negative (18 categories), 3 positive; `BINARY_CLASSIFICATION_OK` |
| repository-wide D3/D4 | `… check-private-source-links.py --repo` | `REPO_OUTPUT_OK` over every tracked text file (new files staged before the run) |
| claims-guard fixtures | `python3 -B scripts/check-claims.py --fixtures` | `CLAIMS_FIXTURES_OK` 78 fixtures, every rule in EN and JA |
| claims guard on the inventory | `python3 -B scripts/check-claims.py` | `CLAIMS_OK` 9 rules, 22 trigger occurrences, all bound to eligible exceptions |
| Router page | `python3 scripts/check-router.py` | `ROUTER_STRUCTURE_OK` (unchanged script) |
| mobile contract | `python3 scripts/check-mobile-layout.py` | `MOBILE_CONTRACT_OK` (unchanged script) |
| mobile scope fixtures | `python3 -B scripts/check-mobile-scope.py` | `MOBILE_SCOPE_FIXTURES_OK` (unchanged script) |
| credential grep | the `validate.yml` grep | `CREDENTIAL_SCAN_OK` |

The bounded-mobile PR step does not apply (no mobile asset or mobile checker changed).

## 2. Browser pass (local `python3 -m http.server 4173`, Chrome)

Measured through a same-origin harness holding the page in a 390 px and a 1280 px frame (the Chrome window could
not be resized below the display width in this session), EN and JA, FAQ closed and open:

| frame | lang | document scrollWidth vs width | clipped elements | h1 size | header height | mobile menu |
|---|---|---|---|---|---|---|
| 390 | EN | 375 ≤ 390 | none | 38.0 px | 65 px | shown |
| 390 | JA | 375 ≤ 390 | none | 38.0 px | 65 px | shown |
| 1280 | EN | 1265 ≤ 1280 | none | 58.9 px | 73 px | hidden |
| 1280 | JA | 1265 ≤ 1280 | none | 58.9 px | 73 px | hidden |

Also verified in the browser: all eight required ids exist in EN and with `-ja` in JA; every `href="#…"` resolves;
external href set is exactly `/router/`, `https://docs.subethalabs.com/v2/`, `/v2/providers/`, `/v2/status/`,
`/v2/#subetha-and-the-router` and `https://x.com/subethalabs`; the language switch hides the other block, updates
`<html lang>` and the title, and the topbar link follows to `#status-ja`; every grid is single-column at 390 px; no
console errors. The hero headline type was scaled from the V1 clamp to `clamp(42px, 4.6vw, 60px)` because the
mandated v2 headline is longer; desktop stays above the 40 px mobile guard and the 390 px size is unchanged
(mobile.css governs it).

## 3. Residue checks on `index.html`

`Poseidon`, `permit`, `payment-history`, `participant-scoped`, hosted or facilitator hostname fragments and 40-hex
addresses: 0 occurrences each. `accepted` / `finalized`: 0 occurrences (the unused V1 `.accepted` CSS rule was
removed). `anonym*` / `匿名`: 7 EN and 5 JA occurrences, all either the allowed "anonymity set" / 「匿名性セット」
phrase or the FAQ question "Is it anonymous?" / 「匿名ですか？」 answered "No." / 「いいえ。」 with a `claims-ok`
denial marker. The other markers on the page: two `hidden-amount` limitations (the P4 sentence, EN and JA), one
`hidden-amount` denial (JA FAQ answer), one `production-ready` denial (JA FAQ question). Every marker text equals
its complete sentence.

## 4. Public artifact inventory and review

Served inventory (derived from `_redirects` by the checker): `index.html`, `router/index.html`, `router/llms.txt`,
`index-v3-previous.html` (302 → `/`, mandatory), `_redirects`, `assets/mobile.css`, `assets/mobile-nav.js`,
`assets/web-demo.png` (unreferenced, kept), nine `assets/brand/*` files. Repository-only after the redirects:
`README.md`, `DESIGN_NOTES.md`, `.github/workflows/validate.yml`, `scripts/*.py` (5), `tests/claims/*`, `tests/output/*`
(counts as in §1), `.claude_workflow/*` (4 incl. this note).

Explicit review of `check-private-source-links.py --list` over every tracked text file (served and repository-only),
each item read in context:

- URLs: company hosts are exactly the LP, Docs v2 routes, the Router endpoint and the Router demo providers already
  public on `/router/`; third-party: Google Fonts, the SVG namespace, X, npm (`@subetha/payer`, Router page), the
  x402.org demo endpoint (Router page), three test-network faucets (Router `llms.txt`, count-fixed exceptions).
  Private V1 repository links: 8 in the archive page, 1 in the header-cleanup note, 1 in `check-mobile-scope.py`,
  all pre-existing, unedited by parent decision, count-fixed, listed in the PR as known and open. Local dev URL in
  README. No hosted-testnet or facilitator host, no path template, no recovery or resource path.
- Commands: CI commands, the local dev server, Router registration commands already on `/router/`, code lines in
  the checkers. None carries connection details or credentials.
- Amounts: CSS percentages and durations; Router page prices and limits (Router product, pre-existing); "about 9 s
  per order" (allowed, labelled not a guarantee). No v2 price or probe amount.
- `NAME=` tokens: a regex description and a Router page JS constant. No credential names.
- Token-like, authorization or secret-assignment values: none. Long opaque values: the checker's SHA-256 digest
  denylist and the base64 fixtures (synthetic).

## 5. Publication boundary

`_redirects` now holds the two archive rules plus six splat/exact rules (`/scripts/*`, `/tests/*`, `/.github/*`,
`/.claude_workflow/*`, `/README.md`, `/DESIGN_NOTES.md`) to `/` with 302; the checker proves statically that every
tracked file is either a site file or redirected and fails otherwise.

Verified on the Pages preview deployment of PR #32 (commit `084a6bb`, 2026-11-13, read-only requests): `/`,
`/router/`, `/router/llms.txt`, `assets/mobile.css` and a brand SVG answer 200; `README.md`, `DESIGN_NOTES.md`,
`scripts/check-router.py`, `scripts/check-claims.py`, `.github/workflows/validate.yml`, both `.claude_workflow/`
notes probed, a `tests/claims/` and a `tests/output/` fixture, and the archive page and its alias all answer 302 to
`/`. The served page carries the v2 headline. The same probe is to be repeated on `https://subethalabs.com/`
after merge (PR body). CI on the PR (Validate LP) passed.

## 6. Independent review

Design note: Codex `gpt-6-astra` rounds 1–4 CHANGES REQUIRED (15 items in total, all applied), round 5 LGTM.
Final diff review: see §7.

## 7. Final Codex review of the diff

Round 1 (CHANGES REQUIRED, 9 major + 1 minor) and what changed:

1. The design note's pattern examples tripped the amount checker once tracked → examples reworded.
2. Claims exceptions accepted an unrelated negation or a technical noun → negation must apply to the property
   (three words before, a negated verb six words after, or a same-clause JA negative ending); `technical` requires
   the quoted term; `limitation` needs a property-bound negation or a scope cue within 60 characters; fixtures added
   (EN/JA unrelated negation, unquoted technical affirmation, generic limitation cue).
3. D3 scans ignored comments, script/style bodies and attribute values → the D3 pass now runs on everything
   retrievable as text; fixtures for a comment path, a script path and an attribute host.
4. D4 missed percent-encoded and entity-encoded links → links are parsed from attributes and decoded before
   matching; fixtures for both encodings.
5. Files outside a suffix allowlist were skipped → every tracked non-binary file is checked; a file that is neither
   UTF-8 text nor a known binary type fails the run.
6. A bare number next to the asset name was not an amount → amounts are any number with an asset or atomic-unit word in either order (Router product prices on
   `/router/` as count-fixed per-file exceptions); fixture added.
7. The 2026-11-09 status row abbreviated the hosted custody wording → full operator-visibility and POS-key wording
   in EN and JA.
8. Meta and OG descriptions lacked the SDK-design attribution → added.
9. The JA settle step omitted "to the order's address" and both languages omitted "by block time" → added.
10. The verification note did not exist at review time → this note.

Round 2 (CHANGES REQUIRED, 6 major + 1 minor) and what changed:

1. This note carried a literal asset amount as an example → reworded.
2. Exceptions still accepted a negation in a relative clause, a JA negation after a topic shift, a quoted but
   affirmative "technical" term, a nearby scope cue and a plan that merely mentions the property → negation must
   govern the property (no relative pronoun, at most two words, JA topic marker only immediately after the trigger);
   a verb that bestows the property (provides, guarantees, 提供 …) rejects every reason unless negated or in a
   question answered No; `limitation` needs the property as subject of an unverified/unquantified predicate; `plan`
   needs "plan to …" / "… is planned" / 「…を計画」; `technical` needs the quoted term discussed as a term; nine
   fixtures added for these bypasses, EN and JA.
3. Faucet URLs and credential shapes were not checked on decoded content → every D3 shape runs on the raw source,
   the entity-decoded text and the percent-decoded text; fixtures for an encoded faucet URL and an entity-encoded
   bearer value.
4. D4 occurrence counting used offsets across decoded views → one entity-decoded view, each original occurrence
   counted once after percent-decoding; fixtures for exact, fewer and more occurrences with a preceding entity and
   an encoded link.
5. The asset word before the number was not an amount → both orders of number and asset word; fixture added.
6. Suffix-based binary skipping → classification by content: UTF-8 text is checked whatever its name; a genuine
   binary needs a known suffix and NUL bytes; anything else fails closed (both checkers).
7. Stale fixture counts in this note → refreshed.

Round 3 (CHANGES REQUIRED, 6 major) and what changed:

1. The claims fixture suite failed on a positive fixture after the stricter negation rule → fixtures aligned with
   the rule (the page sentence was already in the compliant form); the complete suite rerun is recorded in §1.
2. "Anonymity is verified" (limitation), "do not require registration" (denial, EN/JA) and "plan to improve"
   (plan) still passed → `limitation` accepts only negative predicates; a negated verb after the trigger must be a
   copula or a property verb (EN) or a property verb / copular negation (JA); `plan` accepts only verbs that
   introduce the property; seven fixtures added.
3. A source newline inside a trigger escaped detection → HTML newlines are spaces before splitting, and every
   trigger matches across whitespace; two fixtures added.
4. A percent-encoded GitHub hostname escaped D4 → the repository check runs on the fully decoded source.
5. Faucet counts ignored encoded duplicates → counted on the fully decoded source; fixtures for exact, fewer and
   more occurrences with mixed encodings.
6. A NUL byte plus an invalid UTF-8 byte classified a file as binary → binaries are accepted only with a known
   suffix and that type's signature (shared helper, self-tested); anything else fails closed.

Round 4 (CHANGES REQUIRED, 5 major) and what changed:

1. "Anonymous payments are not delayed", "No registration for anonymous payments" and 「匿名決済は遅延を保証しません」
   still passed as denials → the negation must sit on the property word, on a coordination that includes it, or on
   a property verb whose object or subject it is (EN and JA); three fixtures added.
2. Inline tags split or decorated triggers ("fully <code>private</code>", "anon<span>ymous</span>",
   「完全に<strong>プライベート</strong>」) → inline tags are removed without inserting a space; the `technical`
   gate reads `<code>` from the source instead; three fixtures added.
3. A dot-segment path reached a private repository → dot segments are resolved before identification; fixture.
4. A PNG signature followed by text counted as binary → binaries must be well-formed (PNG chunk walk, ICO directory,
   trailers and length fields); the repository's own images are checked in the self-test; malformed samples fail.
5. A protocol-relative faucet link escaped → `//host` links are spelled out as https before every scan; fixtures
   for a faucet and a company-domain host.

Round 5 (CHANGES REQUIRED, 4 major) and what changed:

1. "Anonymous payments do not imply delays" and "… are not guaranteed to be fast" passed → after-negation is accepted
   only when the property is the subject head (optionally one short prepositional phrase), never when it merely
   modifies the subject; two fixtures.
2. A comment or `<wbr>` inside a word hid a trigger → comments and `<wbr>` are removed without a space; two fixtures.
3. A link with an explicit port reached a private repository → ports and userinfo are parsed; two fixtures.
4. A JPEG signature around text, and a PNG of empty chunks with bad CRCs, counted as binaries → PNG (chunk walk,
   CRCs, IHDR/IDAT/IEND), ICO (directory to PNG/DIB images) and JPEG (marker walk) are validated structurally; no
   other binary format is accepted; the self-test covers the repository's own images and nine malformed samples.

Round 6 (CHANGES REQUIRED, 4 major) and what changed:

1. Double negations ("not without anonymity", "anything but anonymity", 「…ないわけではありません」) passed as
   denials → rejected as reversing frames; three fixtures.
2. An inline element outside the allowlist (`samp`) split a word → every non-block tag is removed without a space;
   fixture.
3. Forged binaries (zero IHDR with text IDAT, a bare SOS JPEG, a fake DIB with trailing text) → by the parent's
   decision the question is closed at the root: every file, binaries included, is scanned as UTF-8 text with
   replacement for all exact-match categories and for claims triggers; classification (now validating PNG header
   fields and IDAT size, JPEG tables/frame/scan, ICO directory and DIB geometry) is reporting only and exempts
   nothing; only tokenisation heuristics meaningless on byte noise are skipped for non-UTF-8 content; two
   embedded-binary fixtures (a claim and a denylisted token inside a well-formed PNG).
4. A trailing-dot authority reached a private repository → trailing dots are stripped before matching; fixture.

Threat model and review scope for round 7 onwards (parent decision 2026-11-13, also in the design note §8): the
guards prevent inadvertent drift by cooperating authors, not adversarial authors; review covers (i) public content
against the spec and (ii) guard coverage of the spec's required categories; deliberate bypass constructions outside
the required categories are listed as residual hardening items and do not affect the verdict.

Round 7 (scoped per the threat model): **VERDICT: LGTM**. One minor in-scope item, applied: the plan sentence
"the mainnet gates are open" / 「メインネットのゲートは開いたままです」 read as if access were enabled; now "the
prerequisites for mainnet remain open" / 「メインネット移行の前提条件は未解決です」 (V5). No residual
hardening items were listed in round 7; every item from rounds 1–6 was applied, so the residual count is 0.
All checks in §1 were rerun after the wording change.
