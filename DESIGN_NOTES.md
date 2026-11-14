# SubEtha LP — Design Notes

Status: v2 content on the v4 visual design (2026-11-13). The V1-era archive page was removed on 2026-11-14 (its
old URLs still redirect to `/`). The visual system is unchanged; this revision replaces what the page says.

## Why the rewrite

The page described the first PoC (permit mode, proof-gated mint, a participant-scoped payment history). The product
that exists today is SubEtha v2: standard x402 v2 `exact` on the wire, zUSDC paid to a per-order address from the
zERC20 v2 point of sale, delivery on the re-validated mined receipt, recovery without a second payment, and a hosted
multi-Provider testnet configuration since 2026-11-09. Every section was rewritten against that evidence.

## Design direction (unchanged)

Editorial paper background, ink typography, rules and asymmetric layouts; cards only for real objects (the public
ledger reading, timeline rows); restrained motion with a reduced-motion path. No new dependencies, images or fonts.

## Content rules

- Headline and subline are fixed sentences; every qualifier in the subline must survive editing.
- Order: buyer value → Provider value (labelled hypothesis) → mechanism → who sees what → what you need →
  dated records → contact.
- Two facilitator configurations exist. Every flow, row and diagram names its configuration ("hosted testnet
  (since 2026-11-09)" or "self-run"); they never share a sentence.
- What is public stays public in the copy: payer, amount, token, per-order address, time. The claimed property is
  the direct public link between a per-order `payTo` and the merchant's shielded funds, always with "not
  independently quantified" and "correlation remains".
- Dates are part of the status: 2026-10-31 and 2026-11-01 (public Sepolia runs), 2026-11-09 (hosted switchover),
  2026-11-08 (serialized-order measurement). Mainnet is a plan, not a status.
- No hosted hostnames, paths, URL templates, asset addresses, prices, probe amounts, token or header values, or
  runbook commands with connection details. Registration is described by role. Source is "provided to design
  partners on request"; there is no v2 npm package.
- The Router is a separate product: one FAQ entry with the distinction and links, nothing more.

## Guards

- `scripts/check-claims.py`: assertion-level claims guard (EN/JA). Trigger patterns for anonymity, untraceability,
  unqualified unlinkability, hidden amounts, "fully private", trustlessness, production readiness, current mainnet
  support and npm availability of the v2 extension. Each occurrence needs one exception naming the rule, the
  complete sentence and an eligible reason; exceptions are rejected when the sentence affirms the property, contains
  a reversing frame, or is split from the rest of its sentence by a formatting boundary. Fixtures in `tests/claims/`.
- `scripts/check-private-source-links.py`: served inventory derived from `_redirects` (fail-closed), exact expected
  redirect rules, the v2 page contract (ids, headline, subline qualifiers, configuration captions, Docs v2 links, no
  V1 wording), D3 shape rules plus a digest denylist, D4 private-repository links (since 2026-11-14 no tracked file
  carries a real private repository link; the mobile-scope fixture uses the synthetic `fixture-org/private-fixture`
  entry, count-fixed at one occurrence, and the `--repo` pass rejects any exception naming a real repository), and a
  `--repo` pass over the whole repository. Fixtures in `tests/output/`.
- `scripts/check-router.py`, `scripts/check-mobile-layout.py`: unchanged. `scripts/check-mobile-scope.py`: the
  private-link rejection fixture uses the synthetic entry (2026-11-14); the stale protected-file name of the deleted
  V1 archive was replaced by `DESIGN_NOTES.md`.
- Bounded mobile task scope (`check-router.py --scope mobile --base`): CI applies it only to pull requests whose head
  branch starts with `mobile/` (owner decision 2026-11-14). Before that, any change to `assets/mobile.css`,
  `assets/mobile-nav.js`, `scripts/check-mobile-layout.py` or `scripts/check-mobile-scope.py` routed the PR into the
  gate, which rejects every non-mobile change, so a fixture or checker edit in an ordinary PR could not pass CI.
  On other branches CI reports whether mobile files changed and reviews them as ordinary changes; the mobile layout
  contract and the scope fixtures still run on every PR and on pushes to `main`.

## Language parity

EN and JA carry the same sections, rows, dates and links. The EN tree is the static default. The language switch
updates `<html lang>`, the title, `aria-pressed` and the persisted preference.

## Verification gates

- Static HTML parse and v2 marker checks; all guards above
- Real browser desktop/mobile render (390 px and 1280 px), EN/JA toggle, anchor integrity, FAQ, copy CTA
- Console output, asset paths, horizontal overflow, reduced-motion path
- Post-merge: redirected paths (`README.md`, `scripts/`, `.github/`, `.claude_workflow/`, `tests/`) answer 302 to `/`

Publication, push to `main`, deploy and external claims remain human-review gates.
