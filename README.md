# SubEtha LP

Private repository for the SubEtha landing page. This repository contains a pre-publication static artifact for internal review only.

## Current status

- English-first presentation with an EN / JA display switch
- Local / non-production PoC positioning
- No production deployment
- No external contact destination configured
- No claim of commercial availability, audit, complete anonymity, or official zERC20 partnership

## Files

- `index.html` — self-contained static LP (HTML/CSS/JS)
- `DESIGN_NOTES.md` — information architecture, reference principles, anti-slop review, and publication gates

## Run locally

```bash
python3 -m http.server 4173
```

Open <http://127.0.0.1:4173/>.

No build step or package install is required. Google Fonts are optional; local fallback stacks are included.

## Implemented interactions

- Sticky navigation and mobile menu
- EN / JA language switch with `lang` and `aria-pressed` updates
- FAQ disclosure buttons with `aria-expanded`
- Keyboard focus-visible states
- Responsive desktop/mobile layouts
- `prefers-reduced-motion` support

## Verification

The checked-in artifact has passed HTML parsing and static marker checks. Before publication, perform a browser review at desktop and mobile sizes, including language switching, keyboard interaction, FAQ disclosure, console errors, and horizontal overflow.

## Publication gates

Do not publish or deploy this repository until a human confirms:

- implementation and real-process HTTP E2E evidence
- dependency, version, and artifact boundaries
- zERC20 naming, logo, relationship, and usage permissions
- contact destination and data-retention scope
- final claim matrix and public wording

This repository is private and its contents are not a production service or a commercial offer.
