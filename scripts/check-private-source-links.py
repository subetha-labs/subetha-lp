#!/usr/bin/env python3
"""Offline public-output guard: served inventory, redirect boundary, v2 page contract, D3 shapes, D4 links.

    python3 -B scripts/check-private-source-links.py            # served inventory + mandatory archive page
    python3 -B scripts/check-private-source-links.py --repo     # D3/D4 over every tracked text file
    python3 -B scripts/check-private-source-links.py --fixtures # self-test against tests/output/fail-*
    python3 -B scripts/check-private-source-links.py --list     # URLs, commands, amounts and NAME= tokens for review

Known hosted hostnames, paths, path templates, credential names and runbook script names are matched by SHA-256
digest only; this public file never spells them out. Shape rules (hosts under the company domain, facilitator-style
route segments, URL placeholders, faucet URLs, 40-hex addresses, authorization values, amounts) are literal.
"""
import argparse
import base64
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
DOCS_V2 = 'https://docs.subethalabs.com/v2/'
PROVIDERS_URL = DOCS_V2 + 'providers/'
STATUS_URL = DOCS_V2 + 'status/'
ROUTER_DOCS = DOCS_V2 + '#subetha-and-the-router'
ROUTER_PAGE = '/router/'
PRIVATE_REPOS = {
    ('peaceandwhisky', 'subetha'),
    ('peaceandwhisky', 'subetha-router'),
    ('subetha-labs', 'subetha-router'),
    ('subetha-labs', 'subetha-protocol'),
    ('fixture-org', 'private-fixture'),          # synthetic entry used only by fixtures (tests/output, check-mobile-scope.py)
}
# Count-fixed exceptions, identified by the PRIVATE_REPOS entry, never by writing a URL. Since 2026-11-14 no tracked
# file carries a real private repository link: the last one (a fixture string in scripts/check-mobile-scope.py) was
# replaced by the synthetic entry, which stays count-fixed. run_repo() rejects any exception naming a real repository.
PRIVATE_LINK_EXCEPTIONS = {
    'scripts/check-mobile-scope.py': (('fixture-org', 'private-fixture'), 1, 'synthetic fixture string for the private-link rejection case'),
    # fixture-only entries (synthetic repository) proving that fewer or more occurrences than declared fail
    'pass-privatelink-count.html': (('fixture-org', 'private-fixture'), 2, 'fixture'),
    'fail-privatelink-count-fewer.html': (('fixture-org', 'private-fixture'), 2, 'fixture'),
    'fail-privatelink-count-more.html': (('fixture-org', 'private-fixture'), 2, 'fixture'),
}
# Third-party test-network faucet links of the Router product (outside D3, spec rev 4), per file, URL and count.
FAUCET_EXCEPTIONS = {
    'router/llms.txt': {'https://faucet.circle.com': 4,
                        'https://docs.tempo.xyz/docs/quickstart/faucet': 1,
                        'https://faucet.solana.com': 1},
    'pass-faucet-count.txt': {'https://faucet.example.test/claim': 2},
    'fail-faucet-count-fewer.txt': {'https://faucet.example.test/claim': 2},
    'fail-faucet-count-more.txt': {'https://faucet.example.test/claim': 2},
    # This file names the same three public URLs once each (the table above); the repository-wide pass sees them.
    'scripts/check-private-source-links.py': {'https://faucet.circle.com': 2,
                                              'https://docs.tempo.xyz/docs/quickstart/faucet': 2,
                                              'https://faucet.solana.com': 2,
                                              'https://faucet.example.test/claim': 4},
}
PUBLIC_HOSTS = {'subethalabs.com', 'www.subethalabs.com', 'docs.subethalabs.com', 'router.subethalabs.com',
                'provider-x402.subethalabs.com', 'provider-mpp.subethalabs.com',
                'provider-x402-sol.subethalabs.com'}   # exact hostnames only; the three demo providers are already public on /router/
COMPANY_DOMAIN = 'subethalabs.com'
ROUTE_SEGMENTS = {'verify', 'settle', 'supported', 'orders'}
# SHA-256 digests of lower-cased prohibited tokens (hostnames and labels, paths and segments, templates,
# credential names, runbook script names, asset addresses) plus synthetic fixture-only tokens.
DENY_DIGESTS = set('''
00d84e88fcad934bd259eecb588b00aa51c01024cc1ad83e62a3b09c31c3d772 0d93e2e9eaa27527e259aa216a010e47b9ed42e1512d2c45616ea66797253ab6
0e5f297c29387580682645d1cd6b72944929a92b2ba3a6448c198803aff3f1c5 1f4166afa21cce3af79635c3df81d282117343e929c1c76cfdc084f3c2a56c18
20b568062e9c513c9ccd8aa69ddc4cd0fffd212f5aed42df8181911b48fca140 2875e41d887efa2da4275172d850190148311f3df5f32debfcb54ab85bd0c729
333c7ca227074541125bc71015d62387afdbf0aa9ab9e2b6a117f9df7dae5f25 35415c64bb38f5259a4b912e9657841d55eeb0cd32faa96071f2f9b6f7fe4f01
434d03bdfb184235e66abd4661c74a498558f77ae2fabc78d9efdc36ebbe294e 459e6425eed7c513d084c2c8ccb1b13f4439adb265fba94954ea619f3ae010ca
48ec97059444d2e369c6f13126d5bba0ddbc81bfc59fc9ae2ef70c3144e234da 4c04f2ae7f8058fa32e848ae096687702834207f9f06fb7a5a032af1272eab34
4f1bd724ec45e6eded653d7415447a707e7b5ef58f12a01e226342fbf1ee2b49 6a064a8759a25430eb3f46f6968dd68d207a5dd03faadc58e58bf0b4e8a044df
6a6890d6bbc7276c90cee42854445d9a0149098840ab418943fcfb882051ba1b 7b5d2c02d678a94ac8605395d05fae0c1d3f78f84fe928540a9e34de2da11d9c
877f04849e1971cb3f5da9a55437cb283f009a544fb54be97863a6497ccebf1b 8d8d9e33792b62e46e4e44422fe4b6d22234854c3c4b5ccbbb4f71e60680d170
9614c66078398adb542d42f10928e6270a92683e60452d6124767f0b4da25853 9a2c277fcef9606563e191a11ad3942cd3e5773af9a2aca1f140c06c9eaf7179
9bb1e6b395f4e6c99a5d70e4b01f9c48eed0b82bd9d7c91f449674be151f49ed a3b22246e9ecbb73006e5ec2c9a49830986b32e5fce2cd3e89dfa245e44159ce
a5f46460e907939b6bff6ba041f082ad9f58d94871cec09e912a7328de372ad3 aa82e5d92b833ac1072dfaa763f8123c8eec9ca28560a8004048539e6e76d59e
ade9fff73ccdfd0f9de8d7021e8f3461389925d284d71508fdfdb71fb568fc23 
b81b13675932352159d367f556e1817748416dfc8a67a7fe3b4c10bfa067c0c2 cfa085fc8de6eccbb94286cb7fec8bd1221ce074f07b4afe27a1a4cd7362e9a2
d5402a4758a81e49259c6c8f65b879bb0aa8985b3fff39e9a199d34bb86c0736 d951bc1be10714a7792e1ac99cb4fb08b8c5fd7aa6e641a4c76211ed1755a945
dae4f4d69fda149c639bb7d424c8eb88a23bbcd835d52720d95053f6b71a68bc dbdcbc19524065ea842235cfb00006f13f6319aba48d549436951d92c4a28e98
e0f2ef3367d341942d6369fe6ec8e85f4e6cf2305cbb63db8f27b07493442818 e81508453204821f897de8f19e8e57dcbcee27a1e1d50239c0891cf1446e1038
15e565e9cc2b3f317ed89495ae2b5435b9e19421f7d1e3efcf31163ee4da2c56 062e0914e679afa4736380510a678be0f96b336beaaecc3d028f66d9e08f9bd6 abf87c0d0b0e2148deab364b6e364cfca8c754ed2fe54c1be06d22f07c892c9c 0055b038262e562567b5a1bb6e580c489cecc0c5c9ce08ed817f873dc42d0356 ca32ad902f78bfee121f385616b828b4929ca291d2675f6917701a52de2d96d1
'''.split())
BINARY_SUFFIXES = {'.png', '.ico', '.jpg', '.jpeg', '.gif', '.webp', '.woff', '.woff2', '.ttf', '.otf', '.pdf'}
MANDATORY = ('index.html', 'router/index.html', 'router/llms.txt')   # the V1 archive page was removed on 2026-11-14; its URLs still 302 to /
EXPECTED_REDIRECTS = {
    ('/index-v3-previous.html', '/', '302'), ('/index-v3-previous', '/', '302'),
    ('/scripts/*', '/', '302'), ('/tests/*', '/', '302'), ('/.github/*', '/', '302'),
    ('/.claude_workflow/*', '/', '302'), ('/README.md', '/', '302'), ('/DESIGN_NOTES.md', '/', '302'),
}
URL = re.compile(r'https?://[^\s"\'<>()\[\]]+')
PATH_TOKEN = re.compile(r'(?<![\w/.:<])/(?:[\w<>{}:.-]+/)*[\w<>{}:.-]*')
WORD_TOKEN = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]*')
ADDRESS = re.compile(r'0x[0-9a-fA-F]{40}')
AUTH_VALUE = re.compile(r'\b(?:Bearer|Basic)\s+[A-Za-z0-9._~+/=-]{8,}')
SECRET_ASSIGN = re.compile(r'\b(?:token|secret|password|passphrase|api[-_ ]?key)\b\s*[:=]\s*["\']?[A-Za-z0-9._-]{12,}', re.I)
ASSET_WORD = r'(?:atomic|zUSDC|USDC|pathUSD|USDG|base units|ETH|SOL)'
AMOUNT = re.compile(r'\b\d[\d,]*(?:\.\d+)?\s*' + ASSET_WORD + r'\b|\b' + ASSET_WORD + r'\s*\d[\d,]*(?:\.\d+)?\b|atomic\s+zUSDC|zUSDC\s+per\s+purchase|[$¥€]\s*\d[\d,]*(?:\.\d{1,2})?(?=\s|$|[.,;:)])(?!,\S)', re.I)
# Pre-existing Router product prices and fees already public on /router/ (not v2 D3 items), per file and count.
AMOUNT_EXCEPTIONS = {
    'router/index.html': {'11000 base units': 2, '0.011 USDC': 2, '10000 base units': 4},
    'router/llms.txt': {'10000 base units': 2, '0.01 USDC': 1},
    # This file spells those Router amounts twice each (the table above and this entry); the repository-wide pass sees them.
    'scripts/check-private-source-links.py': {'11000 base units': 2, '0.011 USDC': 2, '10000 base units': 3, '0.01 USDC': 2},
}
FAUCET_URL = re.compile(r'https?://[^\s"\'<>()\[\]]*faucet[^\s"\'<>()\[\]]*', re.I)
PLACEHOLDER = re.compile(r'<[^>]+>|\{[^}]+\}|(?<=/):[A-Za-z]\w*')
ONE_LETTER_SEGMENT = re.compile(r'(?:^|/)[a-z]/[\w<{]')   # a one-letter segment followed by another segment
NAME_ASSIGN = re.compile(r'\b([A-Z][A-Z0-9_]{3,})=')
SCRIPT_TOKEN = re.compile(r'\b[\w.-]+\.(?:mjs|cjs|sh)\b')
SLASH_TOKEN = re.compile(r'\b[A-Za-z][\w.-]*(?:/[A-Za-z<{][\w.<>{}-]*)+')
TOKEN_VALUE = re.compile(r'\b(?:ghp|gho|ghu|ghs|github_pat|sk|pk|xox[baprs]|AKIA)_?[A-Za-z0-9]{10,}|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}|Authorization:\s*[A-Za-z0-9._~+/=-]{16,}')
LONG_OPAQUE = re.compile(r'\b(?:[A-Fa-f0-9]{32,}|[A-Za-z0-9+/]{40,}={0,2})\b')
COMMENT = re.compile(r'<!--.*?-->', re.S)
TAG = re.compile(r'<(/?)([A-Za-z][\w-]*)([^<>]*)>')
HTML_TAGS = set('''a abbr address area article aside audio b base bdi bdo blockquote body br button canvas caption cite code col colgroup data datalist dd del details dfn dialog div dl dt em embed fieldset figcaption figure footer form h1 h2 h3 h4 h5 h6 head header hgroup hr html i iframe img input ins kbd label legend li link main map mark menu meta meter nav noscript object ol optgroup option output p param picture pre progress q rp rt ruby s samp script section select slot small source span strong style sub summary sup svg table tbody td template textarea tfoot th thead time title tr track u ul var video wbr path g rect circle polygon polyline line text defs use clipPath linearGradient stop'''.split())


def strip_tags(source):
    """Remove real HTML/SVG tags and keep angle-bracket placeholders such as <id> that are not element names."""
    def keep_or_drop(match):
        closing, name, attrs = match.groups()
        if closing or attrs.strip() or name.lower() in HTML_TAGS:
            values = re.findall(r'=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s"\'>]+))', attrs)
            return ' ' + ' '.join(a or b or d for a, b, d in values) + ' '
        return match.group(0)
    return TAG.sub(keep_or_drop, source)
COMMAND_LINE = re.compile(r'(?m)^\s*(?:\$\s+)?(?:npm|pnpm|npx|node|curl|claude|codex|grok|python3|git|BUYER_KEY|RESOURCE_URL)\b.*$')


class Page(HTMLParser):
    void = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
            'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.stack, self.nodes, self.ids = [], [], {}
        self.feed(source)
        self.close()
        assert not self.stack, 'Unclosed HTML tags'

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        lang = attrs.get('lang', self.stack[-1]['lang'] if self.stack else '')
        node = {'tag': tag, 'attrs': attrs, 'lang': lang, 'text': ''}
        self.nodes.append(node)
        if 'id' in attrs:
            assert attrs['id'] not in self.ids, f'Duplicate ID: {attrs["id"]}'
            self.ids[attrs['id']] = node
        if tag not in self.void:
            self.stack.append(node)

    def handle_endtag(self, tag):
        assert self.stack and self.stack[-1]['tag'] == tag, f'Mismatched </{tag}>'
        self.stack.pop()

    def handle_data(self, text):
        for node in self.stack:
            node['text'] += text


def digest(token):
    return hashlib.sha256(token.lower().encode()).hexdigest()


def tracked_files():
    out = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode()
    return sorted(p for p in out.split('\0') if p)


def redirect_rules():
    rules = []
    for line in (ROOT / '_redirects').read_text(encoding='utf-8').splitlines():
        if line.strip() and not line.lstrip().startswith('#'):
            rules.append(tuple(line.split()))
    return rules


def redirected(path, rules):
    for source, target, status in rules:
        if target != '/':
            continue
        if source.endswith('/*') and path.startswith(source[:-1]):
            return True
        if path == source:
            return True
    return False


def is_site_file(path):
    return path == 'index.html' or path == '_redirects' or path.startswith('router/') or path.startswith('assets/')


def public_inventory():
    """Tracked files minus redirected paths, plus the four mandatory pages. Fails closed on any stray file."""
    rules = redirect_rules()
    served = [p for p in tracked_files() if not redirected('/' + p, rules)]
    stray = [p for p in served if not is_site_file(p)]
    assert not stray, f'Tracked files would be served outside the site boundary; add a redirect rule: {stray}'
    return sorted(set(served) | set(MANDATORY))


def check_redirects():
    routes = set(redirect_rules())
    assert routes == EXPECTED_REDIRECTS, f'_redirects must contain exactly the expected rule set; got {sorted(routes)}'


def private_repo(href):
    import posixpath
    url = urlsplit(href)
    host = (url.hostname or '').lower().rstrip('.')    # a trailing DNS dot names the same host
    if host in {'github.com', 'www.github.com', 'raw.githubusercontent.com'}:
        # dot segments resolve the way a browser resolves them: /fixture-org/other/../private-fixture
        path = posixpath.normpath('/' + unquote(url.path).lstrip('/')) if url.path else '/'
        parts = path.lower().strip('/').split('/')
        if len(parts) >= 2:
            return (parts[0], parts[1].removesuffix('.git'))
    return None


class LinkAttrs(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.values = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ('href', 'src', 'content', 'action', 'data-href') and value:
                self.values.append(value)


def check_private_links(name, source, errors):
    """Count links to private product repositories once per original occurrence, after decoding each value."""
    import html as _html
    exception = PRIVATE_LINK_EXCEPTIONS.get(name)
    counts = {}
    pattern = re.compile(r'(?:https?://)?(?:[\w.%-]+(?::[^@\s/]*)?@)?(?:www\.)?(?:github\.com|raw\.githubusercontent\.com)\.?(?::\d+)?/[^\s"\'<>()\[\]`]+', re.I)
    # Decoding never adds or removes a link, it only spells it out, so counting on the decoded view counts each
    # original occurrence exactly once (entities first, then percent escapes, so %67ithub.com is seen as github.com).
    decoded = scheme_relative(unquote(_html.unescape(source)))
    for match in pattern.finditer(decoded):
        value = match.group(0)
        href = value if value.lower().startswith('http') else 'https://' + value
        repo = private_repo(href)
        if repo in PRIVATE_REPOS:
            counts[repo] = counts.get(repo, 0) + 1
    for repo, count in counts.items():
        if exception and exception[0] == repo:
            continue
        errors.append(f'{name}: Private product repo href ({repo[0]}/{repo[1]}) x{count}')
    if exception:
        repo, expected, reason = exception
        actual = counts.get(repo, 0)
        if actual != expected:
            errors.append(f'{name}: pre-existing private link exception expects {expected} occurrence(s) of {repo[0]}/{repo[1]}, found {actual} ({reason})')


def plain(name, source):
    """Text with HTML comments, script/style bodies and tags removed and entities decoded (used by --list)."""
    import html as _html
    without_code = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', ' ', source, flags=re.S | re.I)
    return _html.unescape(strip_tags(COMMENT.sub(' ', without_code)))


SCHEME_RELATIVE = re.compile(r'(?<![\w:/])//(?=[\w.-]+\.[A-Za-z]{2,}(?:[/:?#]|$))')


def scheme_relative(text):
    """A protocol-relative link (//host/path) is an https link on the deployed page; spell the scheme out."""
    return SCHEME_RELATIVE.sub('https://', text)


def raw_text(source):
    """Everything retrievable as text: tags removed, but comments, script/style bodies and attribute values kept."""
    import html as _html
    return _html.unescape(strip_tags(source))


def check_d3(name, source, errors, binary=False):
    """Every file, binaries included, gets the exact-match categories (digest denylist, hosts under the company
    domain, faucet URLs, 40-hex addresses, credential values, asset amounts, private links). The tokenisation
    heuristics that only make sense for text (path templates, one-letter segments, route segments, currency
    symbols) are skipped for non-UTF-8 content, where every byte pair would read as a path."""
    text = raw_text(source)       # comments, script/style bodies and attribute values are public too
    views = [scheme_relative(v) for v in (source, text, unquote(text))]   # raw, entity-decoded, fully decoded
    faucet_allow = dict(FAUCET_EXCEPTIONS.get(name, {}))
    faucet_seen = {}
    for match in FAUCET_URL.finditer(views[2]):      # fully decoded view: each original occurrence counted once
        url = match.group(0).rstrip('.,;:')
        faucet_seen[url] = faucet_seen.get(url, 0) + 1
    for url, count in faucet_seen.items():
        if url not in faucet_allow:
            errors.append(f'{name}: faucet URL is not allowed: {url}')
    for url, expected in faucet_allow.items():
        if faucet_seen.get(url, 0) != expected:
            errors.append(f'{name}: faucet exception for {url} expects {expected}, found {faucet_seen.get(url, 0)}')
    seen_urls = set()
    for match in [m for view in views for m in URL.finditer(view)]:
        raw = match.group(0).rstrip('.,;:)')
        if raw in seen_urls:
            continue
        seen_urls.add(raw)
        url = urlsplit(raw)
        host = (url.hostname or '').lower()
        if host.endswith(COMPANY_DOMAIN) and host not in PUBLIC_HOSTS:
            errors.append(f'{name}: host under the company domain outside the public allowlist: {host}')
        if digest(host) in DENY_DIGESTS or any(digest(label) in DENY_DIGESTS for label in host.split('.')):
            errors.append(f'{name}: denylisted hostname in URL: {raw[:80]}')
        check_path(name, url.path, raw, errors)
    for match in re.finditer(r'\b[\w-]+\.' + re.escape(COMPANY_DOMAIN) + r'\b', text):
        host = match.group(0).lower()
        if host not in PUBLIC_HOSTS:
            errors.append(f'{name}: bare host under the company domain outside the public allowlist: {host}')
    for view in ([] if binary else views[1:]):
        for match in PATH_TOKEN.finditer(view):
            token = match.group(0)
            if len(token) > 1:
                check_path(name, token, token, errors)
    for label, pattern in (('40-hex address', ADDRESS), ('authorization header value', AUTH_VALUE),
                           ('credential-like assignment', SECRET_ASSIGN), ('token-like value', TOKEN_VALUE)):
        if any(pattern.search(view) for view in views):
            errors.append(f'{name}: {label}')
    for match in ([] if binary else SLASH_TOKEN.finditer(text)):
        token = match.group(0)
        if token.startswith(('http', 'assets/', 'router/')) or '://' in token:
            continue
        check_path(name, '/' + token, token, errors)
    amount_allow = dict(AMOUNT_EXCEPTIONS.get(name, {}))
    amount_seen = {}
    for match in AMOUNT.finditer(unquote(text)):
        value = ' '.join(match.group(0).split())
        if binary and value[0] in '$¥€':
            continue                                   # a currency symbol next to a digit is byte noise in a binary
        amount_seen[value] = amount_seen.get(value, 0) + 1
    for value, count in amount_seen.items():
        if value not in amount_allow:
            errors.append(f'{name}: price or probe amount: {value}')
    for value, expected in amount_allow.items():
        if amount_seen.get(value, 0) != expected:
            errors.append(f'{name}: amount exception for {value} expects {expected}, found {amount_seen.get(value, 0)}')
    for match in NAME_ASSIGN.finditer(text):
        if digest(match.group(1)) in DENY_DIGESTS:
            errors.append(f'{name}: denylisted variable name')
    for match in SCRIPT_TOKEN.finditer(text):
        if digest(match.group(0)) in DENY_DIGESTS:
            errors.append(f'{name}: denylisted runbook script name')
    for token in set(WORD_TOKEN.findall(text)):
        if digest(token) in DENY_DIGESTS or digest(token.rstrip('.')) in DENY_DIGESTS:
            errors.append(f'{name}: denylisted token')
            break


def check_path(name, path, shown, errors):
    path = unquote(path)
    if PLACEHOLDER.search(path) or ONE_LETTER_SEGMENT.search(path):
        errors.append(f'{name}: URL path template or tenant-style path: {shown[:80]}')
    segments = [s for s in path.split('/') if s]
    for segment in segments:
        if segment.lower() in ROUTE_SEGMENTS:
            errors.append(f'{name}: facilitator-style route segment in a path: {shown[:80]}')
            break
    prefixes = ['/' + '/'.join(segments[:i + 1]) for i in range(len(segments))]
    if any(digest(s) in DENY_DIGESTS for s in segments) or any(digest(p) in DENY_DIGESTS for p in prefixes) \
            or any(digest(p.lstrip('/')) in DENY_DIGESTS for p in prefixes):
        errors.append(f'{name}: denylisted path: {shown[:80]}')


def check_text_file(name, source, errors, binary=False):
    check_private_links(name, source, errors)
    check_d3(name, source, errors, binary)


def require_links(page, lang, suffix):
    nodes = [n for n in page.nodes if n['lang'] == lang]
    links = [n for n in nodes if n['tag'] == 'a']
    for href in (DOCS_V2, PROVIDERS_URL, STATUS_URL, ROUTER_DOCS, ROUTER_PAGE, '#contact' + suffix, '#how-it-works' + suffix):
        assert any(n['attrs'].get('href') == href and n['text'].strip() for n in links), f'Missing {lang} link: {href}'
    assert any(n['attrs'].get('data-copy') == 'contact@subethalabs.com' for n in nodes), f'Missing {lang} contact copy button'
    return nodes


def check_root(page, source):
    for required in ('top', 'problem', 'how-it-works', 'visibility', 'providers', 'status', 'faq', 'contact'):
        assert required in page.ids, f'Missing EN id: {required}'
        assert required + '-ja' in page.ids, f'Missing JA id: {required}-ja'
    for gone in ('history', 'history-ja', 'protocol', 'protocol-ja'):
        assert gone not in page.ids, f'V1 id must be removed: {gone}'
    en = require_links(page, 'en', '')
    ja = require_links(page, 'ja', '-ja')
    h1 = {lang: ' '.join(n['text'].split()) for lang, group in (('en', en), ('ja', ja)) for n in group if n['tag'] == 'h1'}
    assert h1['en'] == 'Your x402 customers keep paying the same way. The public chain stops showing a stream of payments into your address.', h1['en']
    assert h1['ja'] == '顧客の x402 の支払い方は変わらない。公開チェーンに、あなたのアドレスへの入金の列が残らなくなる。', h1['ja']
    lede = {lang: ' '.join(n['text'].split()) for lang, group in (('en', en), ('ja', ja)) for n in group if 'hero-lede' in n['attrs'].get('class', '')}
    for marker in ('unmodified official x402 client', 'zUSDC (wrapped USDC)', 'different receiving address instead of one fixed payTo',
                   'Payer, amount, token and transaction time stay public', 'not been independently quantified', 'correlation remains possible'):
        assert marker in lede['en'], f'EN subline qualifier missing: {marker}'
    for marker in ('無改造の公式 x402 クライアント', 'zUSDC（wrap した USDC）', '注文ごとに異なる受取アドレス',
                   'payer・金額・token・取引時刻は公開のまま', '独立に定量評価されておらず', '相関による推測は可能'):
        assert marker in lede['ja'], f'JA subline qualifier missing: {marker}'
    text = {'en': page.ids['en']['text'], 'ja': page.ids['ja']['text']}
    for marker in ('Configuration: hosted testnet (since 2026-11-09)', 'Hosted testnet (since 2026-11-09)', 'Facilitator operator, self-run',
                   'Is it anonymous?', 'Can I use it in production?', 'How is this different from the Router?', 'Is the source public?',
                   'What do my customers need?', 'design partners', 'delegated x402 facilitator', 'Testnet registration requests go to the same address'):
        assert marker in text['en'], f'Missing EN marker: {marker}'
    for marker in ('構成: hosted testnet（2026-11-09 以降）', 'Hosted testnet（2026-11-09 以降）', 'facilitator 運用者、self-run',
                   '匿名ですか？', '本番で使えますか？', 'Router と何が違いますか？', 'ソースは公開ですか？', '顧客側で何が必要ですか？',
                   '設計パートナー', '委任先の x402 facilitator', 'テストネット登録の相談も同じ宛先'):
        assert marker in text['ja'], f'Missing JA marker: {marker}'
    flat = source + '\n' + text['en'] + '\n' + text['ja']
    for pattern in (r'Poseidon', r'\bpermit\b', r'payment[- ]history', r'participant-scoped', r'proof-gated', r'\btreasury\b',
                    r'fail-closed', r'\baccepted\b', r'\bfinalized\b', r'web-demo', r'Demo preview', r'guided (?:browser|web) demo',
                    r'reference/payment-history', r'git\s+clone', r'\bclone\b', r'read\s+(?:the\s+)?code', r'コードを見る', r'クローン',
                    r'Agent Payment Intelligence Firewall', r'local reference implementation'):
        assert not re.search(pattern, flat, re.I), f'V1 wording must not remain: {pattern}'
    assert 'docs.subethalabs.com/"' not in source, 'Docs links must point at the v2 track'
    for node in page.nodes:
        if node['tag'] == 'img':
            assert node['attrs'].get('src', '').startswith('assets/brand/'), f'Unexpected image: {node["attrs"].get("src")}'


def check_pages(inventory):
    for name in inventory:
        if not name.endswith('.html'):
            continue
        page = Page((ROOT / name).read_text(encoding='utf-8'))
        for node in page.nodes:
            href = node['attrs'].get('href', '')
            if href.startswith('#'):
                assert unquote(href[1:]) in page.ids, f'{name}: broken anchor {href}'
        if name == 'index.html':
            check_root(page, (ROOT / name).read_text(encoding='utf-8'))


MAGIC = {'.png': (b'\x89PNG\r\n\x1a\n',), '.ico': (b'\x00\x00\x01\x00',), '.jpg': (b'\xff\xd8\xff',), '.jpeg': (b'\xff\xd8\xff',)}


def png_ok(data):
    """Signature; chunk walk with valid CRCs; a 13-byte IHDR with legal fields; IDAT payload that inflates to exactly
    the image's raw size; IEND last; no trailing bytes."""
    import struct, zlib
    if not data.startswith(MAGIC['.png'][0]):
        return False
    pos, kinds, idat, header = 8, [], b'', None
    while pos + 12 <= len(data):
        length = struct.unpack('>I', data[pos:pos + 4])[0]
        kind, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + length]
        if not re.fullmatch(rb'[A-Za-z]{4}', kind) or pos + 12 + length > len(data):
            return False
        if struct.unpack('>I', data[pos + 8 + length:pos + 12 + length])[0] != (zlib.crc32(kind + body) & 0xffffffff):
            return False
        if kind == b'IHDR':
            if kinds or length != 13:
                return False
            header = struct.unpack('>IIBBBBB', body)
        if kind == b'IDAT':
            idat += body
        if kind == b'IEND' and length != 0:
            return False
        kinds.append(kind)
        pos += 12 + length
    if not (pos == len(data) and header and kinds[-1] == b'IEND' and b'IDAT' in kinds):
        return False
    width, height, depth, colour, compression, filt, interlace = header
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(colour)
    if not (0 < width < 2 ** 24 and 0 < height < 2 ** 24 and channels and depth in (1, 2, 4, 8, 16)
            and compression == 0 and filt == 0 and interlace in (0, 1)):
        return False
    try:
        raw = zlib.decompress(idat)
    except zlib.error:
        return False
    rowbytes = (width * channels * depth + 7) // 8
    if interlace == 0:
        return len(raw) == height * (1 + rowbytes)
    total = 0
    for sx, sy, ox, oy in ((8, 8, 0, 0), (8, 8, 4, 0), (4, 8, 0, 4), (4, 4, 2, 0), (2, 4, 0, 2), (2, 2, 1, 0), (1, 2, 0, 1)):
        pw, ph = (width - ox + sx - 1) // sx, (height - oy + sy - 1) // sy
        if pw and ph:
            total += ph * (1 + (pw * channels * depth + 7) // 8)
    return len(raw) == total


def jpeg_ok(data):
    """Marker walk from SOI: quantisation and Huffman tables and a frame header with real dimensions before the scan,
    a scan header naming at least one component, entropy data, then EOI as the last bytes."""
    if not data.startswith(b'\xff\xd8\xff'):
        return False
    pos, seen = 2, set()
    while pos + 2 <= len(data):
        if data[pos] != 0xFF:
            return False
        marker = data[pos + 1]
        if marker == 0xFF:
            pos += 1
            continue
        if marker == 0xD9:
            return pos + 2 == len(data) and {'DQT', 'DHT', 'SOF', 'SOS'} <= seen
        if marker == 0xD8 or 0xD0 <= marker <= 0xD7 or marker == 0x01:
            pos += 2
            continue
        if pos + 4 > len(data):
            return False
        length = int.from_bytes(data[pos + 2:pos + 4], 'big')
        if length < 2 or pos + 2 + length > len(data):
            return False
        segment = data[pos + 4:pos + 2 + length]
        if marker == 0xDB:
            seen.add('DQT')
        elif marker == 0xC4:
            seen.add('DHT')
        elif marker in (0xC0, 0xC1, 0xC2):
            if length < 11:
                return False
            height, width, components = int.from_bytes(segment[1:3], 'big'), int.from_bytes(segment[3:5], 'big'), segment[5]
            if not (width > 0 and height > 0 and components in (1, 3, 4) and length == 8 + 3 * components):
                return False
            seen.add('SOF')
        elif marker == 0xDA:
            if 'SOF' not in seen or length < 8 or length != 6 + 2 * segment[0]:
                return False
            seen.add('SOS')
        pos += 2 + length
        if marker == 0xDA:
            start = pos
            while pos + 1 < len(data) and not (data[pos] == 0xFF and data[pos + 1] != 0x00 and not 0xD0 <= data[pos + 1] <= 0xD7):
                pos += 1
            if pos == start:
                return False
    return False


def ico_ok(data):
    """ICONDIR with entries that each point inside the file at a PNG or a BITMAPINFOHEADER DIB whose fields and
    pixel-data size agree with the entry; the file ends where the last image ends."""
    import struct
    if not data.startswith(MAGIC['.ico'][0]) or len(data) < 6:
        return False
    count = struct.unpack('<H', data[4:6])[0]
    if count < 1 or len(data) < 6 + 16 * count:
        return False
    end = 6 + 16 * count
    for i in range(count):
        entry = data[6 + 16 * i:6 + 16 * i + 16]
        w, h, colours, reserved, planes, bits, size, offset = struct.unpack('<BBBBHHII', entry)
        if size < 40 or offset < 6 + 16 * count or offset + size > len(data):
            return False
        image = data[offset:offset + size]
        if png_ok(image):
            pass
        elif image[:4] == b'\x28\x00\x00\x00':
            bw, bh, bplanes, bbits, bcomp = struct.unpack('<iiHHI', image[4:20])
            width, height = w or 256, h or 256
            if not (bw == width and bh == 2 * height and bplanes == 1 and bbits in (1, 4, 8, 24, 32) and bcomp == 0):
                return False
            palette = (4 << bbits) if bbits <= 8 else 0
            xor = ((width * bbits + 31) // 32) * 4 * height
            and_mask = ((width + 31) // 32) * 4 * height
            if size != 40 + palette + xor + and_mask:
                return False
        else:
            return False
        end = max(end, offset + size)
    return end == len(data)


VALIDATORS = {'.png': png_ok, '.ico': ico_ok, '.jpg': jpeg_ok, '.jpeg': jpeg_ok}


def well_formed_binary(suffix, data):
    """Only formats this repository can validate structurally are accepted as binaries; anything else fails closed."""
    validator = VALIDATORS.get(suffix)
    return bool(validator and validator(data))


def classify_bytes(name, data):
    """'text' for UTF-8 content whatever the suffix; 'binary' only when the suffix is a known binary type AND the
    bytes form a well-formed file of that type; anything else fails closed."""
    try:
        data.decode('utf-8')
        return 'text'
    except UnicodeDecodeError:
        pass
    suffix = Path(name).suffix.lower()
    if well_formed_binary(suffix, data):
        return 'binary'
    raise AssertionError(f'{name}: unclassified artifact (not UTF-8 text and not a well-formed {suffix or "binary"} file)')


def read_scan_text(path):
    """Every file is scanned: UTF-8 with undecodable bytes replaced, plus a flag saying whether the content is a
    well-formed binary (then only the tokenisation heuristics are skipped, see check_d3). classify_bytes() still
    fails closed on an unclassifiable file."""
    data = path.read_bytes()
    binary = classify_bytes(path.name, data) == 'binary'
    return data.decode('utf-8', errors='replace'), binary


def readable(name):
    return (ROOT / name).is_file()


def run_served():
    check_redirects()
    inventory = public_inventory()
    check_pages(inventory)
    errors = []
    for name in inventory:
        if readable(name):
            check_text_file(name, *read_scan_text(ROOT / name)[:1], errors, binary=read_scan_text(ROOT / name)[1])
    return inventory, errors


def run_repo():
    errors = []
    names = [n for n in tracked_files() if readable(n)]
    for name in names:
        check_text_file(name, *read_scan_text(ROOT / name)[:1], errors, binary=read_scan_text(ROOT / name)[1])
    for name in PRIVATE_LINK_EXCEPTIONS:
        if not name.startswith(('pass-', 'fail-')):
            assert name in names, f'exception refers to an untracked file: {name}'
    # Since 2026-11-14 the only tracked file allowed to carry a private-repository-shaped link is the mobile-scope
    # fixture, with the synthetic entry, one occurrence. Every other tracked file must count zero (checked above per
    # file), and no exception, fixture or not, may name a real repository. Adding an entry here fails on purpose.
    synthetic = ('fixture-org', 'private-fixture')
    allowed = {'scripts/check-mobile-scope.py': (synthetic, 1)}
    actual = {n: (e[0], e[1]) for n, e in PRIVATE_LINK_EXCEPTIONS.items() if not n.startswith(('pass-', 'fail-'))}
    assert actual == allowed, f'file-level private-link exceptions must be exactly {allowed}, got {actual}'
    real = sorted(n for n, e in PRIVATE_LINK_EXCEPTIONS.items() if e[0] != synthetic)
    assert not real, f'private-link exceptions may only name the synthetic fixture repository, got {real}'
    return names, errors


def run_fixtures():
    directory = ROOT / 'tests/output'
    cases = sorted(p for p in directory.iterdir() if p.name.startswith('fail-') and p.suffix == '.b64')
    assert cases, 'no output fixtures'
    categories = set()
    for path in cases:
        decoded = base64.b64decode(path.read_bytes()).decode('utf-8', errors='replace')   # binaries are scanned the same way
        expect = re.search(r'expect:\s*(.+)', decoded)
        assert expect, f'{path.name}: missing expect line'
        errors = []
        check_text_file(path.with_suffix('').name, decoded, errors, binary=path.name.endswith('.png.b64'))
        assert errors, f'{path.name} should fail'
        assert any(expect.group(1).strip() in e for e in errors), f'{path.name}: expected "{expect.group(1)}", got {errors}'
        categories.add(path.name.split('-')[1])
        print(f'FIXTURE_OK {path.name}')
    for required in ('host', 'hostdigest', 'route', 'template', 'tenant', 'faucet', 'address', 'auth', 'secret', 'amount',
                     'varname', 'script', 'token', 'pathdigest', 'privatelink', 'comment', 'attribute', 'binary'):
        assert required in categories, f'missing output fixture category: {required}'
    passes = sorted(p for p in directory.iterdir() if p.name.startswith('pass-') and p.suffix == '.b64')
    for path in passes:
        passing = base64.b64decode(path.read_bytes()).decode('utf-8')
        errors = []
        check_text_file(path.with_suffix('').name, passing, errors)
        assert not errors, f'{path.name} should pass: {errors}'
        print(f'FIXTURE_OK {path.name}')
    import struct, zlib
    def chunk(kind, body):
        return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body) & 0xffffffff)
    good_png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 0, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b'\x00\xff')) + chunk(b'IEND', b'')
    assert classify_bytes('x.txt', 'plain text'.encode()) == 'text'
    assert classify_bytes('x.png', good_png) == 'binary'
    for name in ('assets/brand/favicon.ico', 'assets/web-demo.png'):
        assert classify_bytes(name, (ROOT / name).read_bytes()) == 'binary', name
    bad_crc = good_png[:-4] + b'\x00\x00\x00\x00'
    empty_chunks = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', b'') + chunk(b'IEND', b'')
    fake_jpeg = b'\xff\xd8\xff<p>Payments are anonymous.</p>\xff\xd9'
    for bad_name, bad in (('x.png', b'\xff\x00<p>Payments are anonymous.</p>'), ('x.bin', b'\xff\x00\x01'), ('x.png', b'\xff\xd8\xff\x00'),
                          ('x.png', b'\x89PNG\r\n\x1a\n<p>Payments are anonymous.</p>'), ('x.png', good_png + b'\xff<p>trailing</p>'),
                          ('x.png', bad_crc), ('x.png', empty_chunks), ('x.jpg', fake_jpeg), ('x.gif', b'GIF89a\xff;'), ('x.pdf', b'%PDF-1.4\xff%%EOF'),
                          ('x.png', b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', b'\x00' * 13) + chunk(b'IDAT', b'<p>Payments are anonymous.</p>') + chunk(b'IEND', b'')),
                          ('x.jpg', b'\xff\xd8\xff\xda\x00\x02<p>Payments are anonymous.</p>\xff\xd9'),
                          ('x.ico', b'\x00\x00\x01\x00\x01\x00' + b'\x01\x01\x00\x00\x01\x00\x20\x00' + (40).to_bytes(4, 'little') + (22).to_bytes(4, 'little') + b'\xff' + b'\x00' * 39 + b'<p>Payments are anonymous.</p>'),
                          ('x.ico', b'\x00\x00\x01\x00\x01\x00' + b'\xff' * 10)):
        try:
            classify_bytes(bad_name, bad)
        except AssertionError:
            pass
        else:
            raise AssertionError(f'{bad_name} with a foreign or absent signature must fail closed')
    print('BINARY_CLASSIFICATION_OK text by content; PNG/ICO/JPEG by structure (chunks, CRCs, directory, marker walk); everything else fails closed')
    print(f'OUTPUT_FIXTURES_OK {len(cases)} negative fixtures, {len(categories)} categories, {len(passes)} positive fixtures')


def run_list():
    """Print every URL, command-like line, amount, NAME= token and credential-shaped value of every tracked text file."""
    served = set(public_inventory())
    amount = re.compile(r'(?:[$¥€]\s*\d[\d,.]*|\b\d[\d,.]*\s*(?:%|atomic|zUSDC|USDC|pathUSD|ETH|SOL|USDG|KiB|MiB|GB|s\b|ms\b|秒|円|base units|per (?:order|purchase|request)))', re.I)
    for name in tracked_files():
        if not readable(name):
            continue
        text, is_binary = read_scan_text(ROOT / name)
        kind = 'binary' if is_binary else 'text'
        print(f'## {name} ({"served" if name in served else "repository only"}, {kind})')
        for label, pattern in (('url', URL), ('command', COMMAND_LINE), ('amount', amount), ('name=', NAME_ASSIGN),
                               ('script', SCRIPT_TOKEN), ('token', TOKEN_VALUE), ('auth', AUTH_VALUE),
                               ('secret=', SECRET_ASSIGN), ('opaque', LONG_OPAQUE)):
            seen = {}
            for match in pattern.finditer(text):
                value = ' '.join(match.group(0).split())
                seen[value] = seen.get(value, 0) + 1
            for value, count in sorted(seen.items()):
                print(f'{label}\t{count}\t{value[:120]}')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--repo', action='store_true', help='D3/D4 over every tracked text file')
    parser.add_argument('--fixtures', action='store_true', help='self-test against tests/output')
    parser.add_argument('--list', action='store_true', help='print URLs, commands, amounts and NAME= tokens for review')
    args = parser.parse_args()
    if args.fixtures:
        run_fixtures()
        return
    if args.list:
        run_list()
        return
    if args.repo:
        names, errors = run_repo()
        for error in errors:
            print(error)
        if errors:
            sys.exit(1)
        print(f'REPO_OUTPUT_OK D3 shapes/digests and D4 private links over {len(names)} tracked text files; real private repository links in tracked files: 0 (one synthetic fixture occurrence, count-fixed)')
        return
    inventory, errors = run_served()
    for error in errors:
        print(error)
    if errors:
        sys.exit(1)
    print(f'PRIVATE_SOURCE_LINKS_OK served inventory of {len(inventory)} files: ' + ', '.join(inventory))
    print('ARCHIVE_REDIRECT_CONFIG_OK exact expected rule set; every tracked non-site file is redirected to / (302); deployed behaviour not tested')
    print('ROOT_CONTRACT_OK v2 ids, headline, subline qualifiers, configuration captions, Docs v2 links, no V1 wording')


if __name__ == '__main__':
    main()
