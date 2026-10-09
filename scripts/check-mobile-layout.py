#!/usr/bin/env python3
"""Offline mobile contract/content guards; optional installed Playwright visual checks.

python3 scripts/check-mobile-layout.py --base HEAD
python3 scripts/check-mobile-layout.py --browser chromium --screenshots /tmp/lp-shots
python3 scripts/check-mobile-layout.py --browser webkit --screenshots /tmp/lp-shots
No browser installation, external requests, probes, or payment actions.
"""
import argparse
from collections import Counter
import importlib.util
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('router_checks', ROOT / 'scripts/check-router.py')
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)
PAGES = ('index.html', 'router/index.html')


def offline(base):
    css = (ROOT / 'assets/mobile.css').read_text()
    js = (ROOT / 'assets/mobile-nav.js').read_text()
    assert '@media(max-width:560px)' in css
    assert not re.search(r'overflow(?:-x)?\s*:\s*(?:hidden|clip)', css)
    for marker in ('min-height:44px', 'flex-wrap:nowrap', 'text-wrap:balance',
                   'font-size:clamp(32px,9.75vw,40px)', 'grid-template-columns:minmax(0,1fr)',
                   'prefers-reduced-motion'):
        assert marker in css, marker
    for marker in ("event.key === 'Escape'", 'closeMenus()', '.focus(', 'matchMedia'):
        assert marker in js, marker
    for name in PAGES:
        source = (ROOT / name).read_text()
        page = checks.Page(source)
        assert 'assets/mobile.css' in source and 'assets/mobile-nav.js' in source
        headers = re.findall(r'<header>.*?</header>', source, re.S)
        assert len(headers) == 2
        for header in headers:
            menu = re.search(r'<details class="mobile-menu">(.*?)</details>', header, re.S)
            assert menu and '<summary>' in menu[1] and '<nav aria-label=' in menu[1]
            # Every original desktop navigation/action link must be in the menu.
            desktop = header[:menu.start()]
            destinations = re.findall(r'<a[^>]+href="([^"]+)"', desktop)[1:]
            assert set(destinations) <= set(re.findall(r'href="([^"]+)"', menu[1]))
            if name == 'index.html':
                assert 'https://docs.subethalabs.com/' in menu[1]
                assert 'href="#contact' in menu[1]
            buttons = [n['attrs'] for n in checks.Page(header).nodes if 'data-lang' in n['attrs']]
            assert len(buttons) == 2
            assert all(b.get('aria-label') and b.get('type') == 'button' for b in buttons)
        if base:
            before = subprocess.check_output(['git', 'show', f'{base}:{name}'], cwd=ROOT, text=True)
            # Exact main/footer text and original URLs/assets, including SDK guidance/caveats.
            prior = checks.Page(before)
            for tag in ('main', 'footer'):
                old = [n['text'] for n in prior.nodes if n['tag'] == tag]
                new = [n['text'] for n in page.nodes if n['tag'] == tag]
                assert old == new, f'{name}: changed {tag} copy'
            for tag, attr in (('a', 'href'), ('img', 'src')):
                old = Counter(n['attrs'].get(attr) for n in prior.nodes if n['tag'] == tag)
                new = Counter(n['attrs'].get(attr) for n in page.nodes if n['tag'] == tag)
                assert not old - new, f'{name}: removed {tag} destinations'
            # Desktop inline styles and product script stay byte-for-byte intact.
            for tag in ('style', 'script'):
                pattern = rf'<{tag}>(.*?)</{tag}>'
                assert re.findall(pattern, before, re.S) == re.findall(pattern, source, re.S), f'{name}: changed original {tag}'
    print('MOBILE_CONTRACT_OK bilingual native menus, complete navigation, touch/focus, bounded phone styles')
    if base:
        print(f'CONTENT_PRESERVED_OK base={base} main/footer copy, links, images, original styles and scripts')


# Executed in each browser: geometry and typography, not merely body overflow.
LAYOUT = r'''({lang, width}) => {
  const root = document.getElementById(lang);
  const box = el => el.getBoundingClientRect();
  const style = el => getComputedStyle(el);
  const header = root.querySelector('header');
  const menu = header.querySelector('.mobile-menu');
  const heading = root.querySelector('h1');
  const lede = root.querySelector('.hero-lede');
  const errors = [];
  const check = (ok, message) => { if (!ok) errors.push(message); };
  check(document.documentElement.scrollWidth <= width + 1, 'document overflow');
  if (width <= 560) {
    check(box(header).height <= 73, 'header/contact orphaned onto another row');
    const controls = [...header.querySelectorAll('.lang button, .mobile-menu summary')];
    const logo = header.querySelector('a');
    for (const el of [logo, ...controls]) {
      check(box(el).height >= 44 && box(el).width >= 44, 'small header touch target');
      check(Math.abs((box(el).top + box(el).height/2) - (box(logo).top + box(logo).height/2)) < 3, 'header controls not aligned');
      check(box(el).left >= 19 && box(el).right <= width - 19, 'header clipping');
    }
    check(parseFloat(style(heading).fontSize) <= 40, 'oversized mobile hero');
    if (width === 390) check(parseFloat(style(heading).fontSize) >= 34, 'hero too small');
    check(box(heading).height <= parseFloat(style(heading).lineHeight) * 6 + 2, 'unbalanced hero lines');
    check(box(heading).left === 20, 'missing 20px hero gutter');
    check(parseFloat(style(root.querySelector('.hero')).paddingTop) <= 36, 'excessive hero top space');
    check(parseFloat(style(lede).fontSize) >= 16 && parseFloat(style(lede).lineHeight) >= 25.6, 'unreadable hero body');
    for (const el of root.querySelectorAll('.split, .rails, .flow, .use-grid')) {
      check(style(el).gridTemplateColumns.split(' ').length === 1, 'cramped mobile card columns');
    }
    for (const el of root.querySelectorAll('.section, .contact')) {
      check(parseFloat(style(el).paddingTop) <= 52, 'oversized section spacing');
    }
  } else {
    check(style(menu).display === 'none', 'mobile menu changed desktop');
    check(style(header.querySelector('.lang-full')).display !== 'none', 'desktop language label changed');
    check(parseFloat(style(heading).fontSize) > 40, 'phone type leaked into desktop');
  }
  // Inspect all visible boxes; only naturally wide code/table descendants may scroll.
  for (const el of root.querySelectorAll('main *, footer *')) {
    if (!el.getClientRects().length || el.closest('details:not([open])') && !el.closest('summary')) continue;
    if (el.parentElement.closest('.codebox, .out, .rail-table-wrap')) continue;
    const r = box(el);
    check(r.left >= -1 && r.right <= width + 1, 'clipped ' + el.tagName + '.' + el.className);
  }
  return errors;
}'''


def browser_checks(args):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        engine = getattr(pw, args.browser)
        launch = {'headless': True}
        if args.executable:
            launch['executable_path'] = args.executable
        # Let launch failure report an explicit skip. Never install/escalate.
        try:
            browser = engine.launch(**launch)
        except Exception as exc:
            print(f'BROWSER_SKIPPED {args.browser}: {str(exc).splitlines()[0]}')
            return
        shots = Path(args.screenshots) if args.screenshots else None
        if shots:
            shots.mkdir(parents=True, exist_ok=True)
        for name in PAGES:
            for width in (320, 360, 390, 430, 768, 1440):
                context = browser.new_context(viewport={'width': width, 'height': 900}, reduced_motion='reduce')
                # All assets are local. Prevent fonts, probes and any other external traffic.
                context.route(re.compile(r'^https?://'), lambda route: route.abort())
                page = context.new_page()
                page.goto((ROOT / name).as_uri())
                for lang in ('en', 'ja'):
                    page.locator(f'#en [data-lang="{lang}"]').click()
                    errors = page.evaluate(LAYOUT, {'lang': lang, 'width': width})
                    assert not errors, f'{name} {lang} {width}: {errors}'
                    root = page.locator(f'#{lang}')
                    if shots:
                        page.screenshot(path=str(shots / f'{args.browser}-{name.replace("/", "-")}-{lang}-{width}.png'), full_page=True)
                    if width <= 560:
                        menu = root.locator('.mobile-menu')
                        summary = menu.locator('summary')
                        summary.focus()
                        page.keyboard.press('Enter')
                        assert menu.evaluate('(el) => el.open')
                        for link in menu.locator('a').all():
                            rect = link.bounding_box()
                            assert rect and rect['height'] >= 44 and rect['width'] >= 44
                        if shots and width == 390:
                            page.screenshot(path=str(shots / f'{args.browser}-{name.replace("/", "-")}-{lang}-menu.png'))
                        page.keyboard.press('Escape')
                        assert not menu.evaluate('(el) => el.open')
                        assert summary.evaluate('(el) => el === document.activeElement')
                        page.keyboard.press('Space')
                        assert menu.evaluate('(el) => el.open')
                        target = '#contact' if name == 'index.html' else '#use'
                        if lang == 'ja':
                            target += '-ja'
                        menu.locator(f'a[href="{target}"]').last.click()
                        assert not menu.evaluate('(el) => el.open')
                        assert page.locator(target).evaluate('(el) => el === document.activeElement')
                        page.evaluate('window.scrollTo(0, 0)')
                        summary.click()
                        other = 'ja' if lang == 'en' else 'en'
                        root.locator(f'[data-lang="{other}"]').click()
                        assert page.locator('.mobile-menu[open]').count() == 0
                        assert page.locator(f'#{other} [data-lang="{other}"]').evaluate('(el) => el === document.activeElement')
                        page.locator(f'#{other} [data-lang="{lang}"]').click()
                    # Expanded lower-page caveats/FAQ must also fit.
                    root.locator('main details').evaluate_all('(els) => els.forEach(el => el.open = true)')
                    errors = page.evaluate(LAYOUT, {'lang': lang, 'width': width})
                    assert not errors, f'expanded {name} {lang} {width}: {errors}'
                    page.evaluate('window.scrollTo(0, 0)')
                context.close()
        browser.close()
        print(f'MOBILE_BROWSER_OK {args.browser}: both pages/languages, 320/360/390/430/768/1440, menus/focus/expanded FAQ')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', help='Compare preserved copy/assets against a local Git revision')
    parser.add_argument('--browser', choices=('chromium', 'webkit'))
    parser.add_argument('--executable', help='Existing browser executable only; never downloaded')
    parser.add_argument('--screenshots', help='Directory for full-page and open-menu screenshots')
    args = parser.parse_args()
    offline(args.base)
    if args.browser:
        browser_checks(args)
