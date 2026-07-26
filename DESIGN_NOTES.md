# SubEtha LP — Design Notes

Status: internal review / local, non-production PoC only
Artifact: `index-v2.html`

## Change intent: PoC-led → vision-led

P0-C.10 changes the page's primary subject. The Hero no longer presents SubEtha mainly as a local PoC or privacy experiment. It introduces SubEtha as a project building payment rails and explicit boundaries for an agent-native internet: autonomous software should be able to discover APIs, exchange value, and remain accountable.

The PoC remains visible, but moves to the appropriate evidence layer: Hero-side “NOW”, Current status, validation phases, FAQ, footer, and publication review gates. `local / non-production PoC` is deliberately not the Hero headline or primary CTA.

## Copy decisions

- Hero: project vision, intended builders/users, and the desired payment boundary.
- Why now: explains why agent/API-era value exchange needs more than a transfer primitive.
- Scenarios: agent discovers an API; provider returns value under clear terms; payment/result responsibility is separated; operations account for observability.
- Boundary map: makes participant, observer, dependency, and responsibility boundaries visible rather than promising invisibility.
- CTA: invites a use-case conversation, without inventing a contact endpoint or commercial availability.
- EN/JA: both translations retain the vision, local PoC qualifier, unaudited status, no-complete-anonymity boundary, and no official zERC20 relationship claim.

## Claim boundary

The page does not claim production readiness, audit completion, commercial availability, complete anonymity, complete untraceability, official zERC20 partnership, endorsement, certification, or licensing permission. zERC20/toolchain references remain dependency/context language and require formal confirmation before publication. `[ CONTACT URL TBD ]` remains a non-submitting placeholder.

The vision language is intentionally aspirational (“building”, “aims”, “we want to enable”) rather than a claim that the full agent economy or production payment rail already exists.

## Surface and visual principles

Primary surface: **Decide / Learn**. The existing paper/ink composition is retained: restrained teal accent, editorial typography, narrow rules, participant/observer diagram, unequal validation phases, responsibility split, and review-aware CTA. This keeps the page project-specific without copying Stripe, Linear, or Framer layouts or identity.

The visual hierarchy now follows: vision → why now → boundary design → validation → current scope → conversation. This prevents a status label from becoming the product story while keeping status available for an honest review.

## Accessibility and responsive posture

- English is the static default (`<html lang="en">`); JA is available through native buttons with `aria-pressed`.
- Language switching updates document language and title.
- Semantic headings, nav, lists, buttons, FAQ `aria-expanded`, focus-visible states, mobile menu state, and reduced-motion handling are retained.
- Mobile layout collapses diagrams and preserves usable controls.

## Open review gates

1. Human review of vision copy and whether the intended audience/scenarios are accurate.
2. Verify real-process HTTP E2E behavior and reconcile implementation/version/artifact boundaries.
3. Confirm zERC20 naming, logo, official-relationship, and commercial-use permissions.
4. Confirm production readiness, audit, operations, legal/regulatory, contact, and data-retention claims separately.
5. Decide final contact destination and publication channel.

No external sharing, deployment, publication, or push was performed for this draft.
