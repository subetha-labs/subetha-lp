# SubEtha LP — Design Notes

Status: v4 redesign in a dedicated worktree. The previous LP is preserved as `index-v3-previous.html`.

## Why the redesign

The prior page was careful about claims, but its visual language still read as a familiar AI / crypto landing page: centered oversized hero, dark green “chain sees” card, repeated rounded cards, many pills, and a long sequence of similarly weighted sections. The redesign changes composition before decoration.

## Design direction

Primary surface: **Decide / Learn**, not “AI product launch”.

- Editorial paper background, ink typography, rules, and asymmetric layouts replace glow, grids, and decorative gradients.
- Typography and horizontal rules carry hierarchy; cards are used only where they represent a real object (ledger, payment receipt, lifecycle).
- The hero is a claim-boundary artifact: a compact public-ledger reading, not abstract technology art.
- The protocol is a five-column operational sequence, with `accepted` and `finalized` visually separated.
- The operational layer is represented as a receipt-like participant-scoped history view rather than another feature-card grid.
- Scope is a timeline with explicit `Implemented`, `Enabled / gated`, and `Roadmap` states.
- Motion is restrained to reveal-on-scroll and button hover; reduced-motion removes transitions.

## Product content reconciliation

Source checked against `origin/develop` of `peaceandwhisky/SubEtha` (latest fetched during this work):

| Current implementation evidence | LP treatment |
|---|---|
| Facilitator daemon with challenge / verify / settle / supported / admin / health and finalize loop | Current scope: Facilitator daemon + provider/client SDKs |
| `accepted` is distinct from `finalized`; finality uses proof-gated mint | Protocol flow and FAQ explicitly separate both states |
| Participant-scoped Payment History, payer/provider/facilitator projections | Operational layer and current scope |
| Server-side `HistoryIdentityResolver`; spoofed caller headers are not auth evidence | Operational layer wording |
| Reorg states retain records instead of silently deleting them | Receipt / FAQ wording |
| Offline verification and encrypted backup/restore checks are fail-closed | Current scope is phrased as implementation surface, not production guarantee |
| Explicit local/testnet/production profile behavior; production gated | Scope timeline and hero caveat |
| Official zERC20 SDK/toolchain boundary; no new token or fork | Hero / FAQ |

The page deliberately does **not** claim production readiness, audit completion, commercial availability, anonymous payments, operator obliviousness, or shipped view-key/auditor disclosure.

## Language parity

EN and JA both cover the central claim, protocol stages, current implementation, profile gates, and contact CTA. The EN tree is the static default. The language switch updates `<html lang>`, title, `aria-pressed`, and persisted local preference.

## Verification gates

- Static HTML parse and marker checks
- Real browser desktop/mobile render
- EN/JA toggle and anchor integrity
- FAQ interaction, copy CTA, keyboard focus
- console output, asset paths, horizontal overflow
- reduced-motion path

Publication, push, deploy, and external claims remain human-review gates.
