# SubEtha LP v2 — Design Notes

Status: internal review / local, non-production PoC only
Artifact: `index-v2.html`

## Surface decision

Primary surface: **Decide / Learn**.

The page is intended to help a technical team decide whether a small, local experiment is worth discussing. The composition therefore moves from an immediately legible problem to a boundary map, validation phases, responsibility split, current scope, and a review-aware CTA. It is not a product dashboard and does not present a production service.

## Reference principles translated for SubEtha

- Stripe-like precision was translated into a restrained paper surface, strong typographic hierarchy, narrow rules, explicit status labels, and a small number of actions. No Stripe logo, copy, layout, or brand color was copied.
- Linear-like restraint was translated into a quiet neutral palette, hairline separators, one controlled teal accent, and no decorative gradient background. No Linear UI or branded visual identity was copied.
- Framer-like product adjacency was translated into an original participant / observer boundary map and a three-phase validation sequence. The mechanism is visible next to its explanation rather than hidden below marketing copy. No Framer layout or proprietary component was copied.

## SubEtha-specific information design

### 1. Hero as a decision frame

The first viewport contains four explicit facts:

- WHO: AI agent, API provider, and teams evaluating privacy requirements.
- WHY: payment history can become a clue about API use or relationships.
- NOW: local / non-production PoC; internal review status.
- TEST: payer, provider, facilitator, observer boundaries and metadata.

This avoids a generic centered headline + button hero that hides the current stage and the value hypothesis.

### 2. Original boundary map

The dark section is not an abstract AI illustration. It is a two-column information diagram:

- Participants: payer / agent, provider, facilitator.
- Observers: chain / RPC, operators, and the explicit “what we do not claim” boundary.

The map states the privacy claim narrowly: the PoC explores the difficulty of reading payer ↔ provider correspondence as a simple transfer. It does not imply that metadata disappears.

### 3. Validation phases

The three unequal columns represent the actual sequence rather than three equal feature cards:

1. Threat model — separate user, observer, protected subject, and acceptable metadata.
2. Accepted — verify the local payment flow and burn confirmation.
3. Finalized — keep proof-gated mint as asynchronous and separate from the request path.

The phase labels intentionally preserve `accepted` / `finalized` semantics and avoid presenting a mint as already complete.

### 4. Responsibility split

The role list separates SubEtha integration, external payment-rail dependencies, and operator responsibilities. The review box keeps permission, E2E, artifact/version, and contact checks visible before publication.

## Anti-AI-slop diagnostic

### Before (P0-C.5 `index.html`)

Score: **4 / 10**

- Tech gradient: present in background/CTA treatments.
- Generic tech hue: cyan is used as the default AI-tech accent without enough structural justification.
- Feature-tile grid: present in the first problem section as three equal cards.
- Unearned blur: present via sticky translucent header and decorative glow.
- Default type: Inter is the primary typeface.

Not counted: accent rail, monument stat, icon topper, center stack, wrong surface. The page was directionally useful, but its repeated rounded cards and glow made it read as a generic AI landing-page template.

### After (`index-v2.html`)

Score: **0 / 10**

- No tech gradient or decorative grid background.
- Teal is a deliberate restrained accent, not an indigo/violet default.
- No equal-weight three-card feature grid; each major claim uses a different layout.
- No glassmorphism or decorative glow.
- No oversized stats, icon toppers, or filler iconography.
- Typography uses IBM Plex Sans JP, DM Mono, and Shippori Mincho with distinct roles.
- Composition is appropriate to Decide / Learn: it teaches and qualifies the PoC rather than imitating a dashboard.

The only blur-like behavior is a limited sticky navigation backdrop for legibility; it is not used as a content surface or elevation system.

## Intentional unresolved decisions

- Contact URL remains `[ CONTACT URL TBD ]`; the CTA is non-submitting and does not invent an external endpoint.
- zERC20 is described as an external dependency / rail under the PoC, without an official partnership, endorsement, certification, or licensing claim.
- The exact production readiness, audit status, supported versions, and external service responsibility remain human review gates.
- Copy should be updated after implementation and real-process HTTP E2E evidence are available; this artifact does not upgrade any unverified claim.

## Accessibility and responsive posture

- English is the default reading language; Japanese remains available through the EN / JA switch, with English labels retained where they describe protocol state.
- Semantic headings, nav, lists, buttons, and an aria-labelled mobile menu are used.
- FAQ buttons expose `aria-expanded`.
- Focus-visible states are present for nav links, buttons, and FAQ controls.
- Mobile layout collapses the two-column diagrams and keeps 44px menu hit area.
- `prefers-reduced-motion: reduce` disables smooth scrolling and transitions.


## P0-C.8 language adaptation

The LP keeps the v2 Decide / Learn layout and boundary-first narrative while making English the default surface. A compact EN / JA control sits in the header; it uses native buttons, `aria-pressed`, and updates `<html lang>` so assistive technology receives the active language. The same sections and status qualifiers are available in both languages.

The switch is intentionally presentation-only: it does not change the meaning of the boundary map, accepted/finalized phases, responsibility split, or local / non-production PoC status. The CTA remains a non-submitting placeholder.

Verification scope: static HTML parsing plus browser checks for initial English rendering, both language transitions, keyboard activation, FAQ disclosure, mobile navigation, desktop/mobile layout, console errors, and horizontal overflow.
