#!/usr/bin/env python3
"""Offline Router landing-page checks; optionally verify task scope against --base."""
import argparse
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shlex
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = 'https://router.subethalabs.com/mcp'


class Page(HTMLParser):
    """Collect text/attributes by ID, and reject mismatched or unclosed tags."""
    void = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
            'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.nodes = []
        self.ids = {}
        self.feed(source)
        self.close()
        assert not self.stack, f'Unclosed tags: {self.stack}'

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        node = {'tag': tag, 'attrs': attrs, 'text': ''}
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


def require(text, markers):
    for marker in markers:
        assert marker in text, f'Missing: {marker}'


def check_page(source):
    page = Page(source)
    assert source.startswith('<!doctype html>')
    assert '<html lang="en">' in source
    assert page.ids['ja']['attrs']['lang'] == 'ja'
    require(source, ['prefers-reduced-motion', "setAttribute('aria-pressed'", 'navigator.clipboard.writeText(target.textContent)'])
    switches = [n['attrs'] for n in page.nodes if 'data-lang' in n['attrs']]
    assert Counter(a['data-lang'] for a in switches) == {'en': 2, 'ja': 2}
    assert all(a['aria-pressed'] in ('true', 'false') for a in switches)

    for node in page.nodes:
        attrs = node['attrs']
        href = attrs.get('href', '')
        if href.startswith('#'):
            assert href[1:] in page.ids, f'Broken anchor: {href}'
        for attr in ('aria-controls', 'aria-describedby'):
            for target in attrs.get(attr, '').split():
                assert target in page.ids, f'Broken {attr}: {target}'
    copies = [n for n in page.nodes if 'data-copy-target' in n['attrs']]
    assert len(copies) == 8
    for node in copies:
        attrs = node['attrs']
        target = page.ids[attrs['data-copy-target']]
        assert target['tag'] == 'pre' and target['text'].strip()
        status = page.ids[attrs['aria-describedby']]['attrs']
        assert status['role'] == 'status' and status['aria-live'] == 'polite'

    shared = ['2026-10-09', '2026-10-08', 'Base Sepolia', 'Arc testnet',
              'Solana devnet', 'Tempo testnet', 'USDC', 'pathUSD', '0.01',
              '10000', 'decimals 6', '5 × 4 = 20', 'proof.onChainFinality',
              'not_checked', 'fundsMoveOnCredential', 'approval=quoteId',
              'paid_data_unavailable', 'unknown', 'awaiting_payment',
              'devnet SOL', '256 KiB', 'application/json', 'HTTPS',
              'Hyperliquid', 'Uniswap v3', 'result.structuredContent',
              'ok: true', 'routes', 'dynamic.profiles', 'data:']
    for lang, suffix in [('en', ''), ('ja', '-ja')]:
        body = page.ids[lang]['text']
        require(body, shared)
        for anchor in ('why', 'how', 'status', 'use', 'try', 'payments', 'faq'):
            assert anchor + suffix in page.ids
        prompt = page.ids['instruction' + suffix]['text']
        require(prompt, ['md-mpp-eth-snapshot', 'UUID', 'requestId', 'protocol',
                         'network', 'asset', 'decimals', 'fundsMoveOnCredential'])
        assert set(re.findall(r'subetha_router_\w+', prompt)) == {
            'subetha_router_list_routes', 'subetha_router_quote'}
        if lang == 'en':
            require(body, ['5 payment-rail combinations', '4 test networks',
                           '10 fixed routes', '20 dynamic profiles',
                           'Same-rail pairs are excluded', 'Not every attempt succeeded',
                           'not a fresh sweep', 'never initiate payment',
                           'Public local signing setup is being prepared', 'before any potentially spending signing step',
                           'Tempo MPP credential creation sends funds before purchase',
                           'Solana MPP locally signs first', 'does not prove human consent',
                           'Do not automatically retry', 'No refund is guaranteed',
                           'Providers are unverified', 'provider price plus the Router fee',
                           'HTTP 200 alone is not success', 'not API data or a Router quote'])
            require(prompt, ['still listed', 'exactly once', 'fresh UUID', 'amount', 'expiry',
                             'Then STOP', 'Do not sign, read keys, create a wallet, approve, or call purchase'])
        else:
            require(body, ['5つの決済レール', '4つのテストネット', '10の固定ルート',
                           '20の動的プロファイル', '同一レール同士は対象外',
                           'すべての試行が成功したわけではなく', '今回全組を再検証した結果でも',
                           '支払いを開始しません', '一般向けのローカル署名の導入手順は準備中',
                           '支出が起こり得る署名工程より前', 'Tempo MPP は credential 作成時に送金',
                           'Solana MPP はローカルで署名のみ', '人間の同意を証明しません',
                           '自動再試行しない', '返金の保証はありません', 'プロバイダは未検証',
                           'プロバイダの代金と Router 手数料', 'HTTP 200 だけでは成功とは判定できません',
                           'APIデータでも Router の見積でもありません'])
            require(prompt, ['まだ一覧にあれば', '1回だけ', '新しい UUID', '金額', '有効期限',
                             '必ず停止', '署名、鍵の読取、ウォレット作成、承認、purchase はしない'])
        scope = page.ids['verification-scope' + suffix]
        assert scope['tag'] == 'details' and 'open' not in scope['attrs']
        require(scope['text'], ['proof.onChainFinality', 'not_checked'] + (
            ['Verification scope', 'Not every attempt succeeded', 'paid attempt',
             'without usable data', 'not a fresh sweep or a production guarantee',
             'Independent finality checks'] if lang == 'en' else
            ['検証の範囲', 'すべての試行が成功したわけではなく',
             '支払ったのに利用可能なデータが得られなかった',
             '今回全組を再検証した結果でも、本番運用の保証でもありません',
             '独立した finality 照合']))
        assert page.ids['endpoint' + suffix]['text'] == ENDPOINT
        assert page.ids['register' + suffix]['text'] == f'claude mcp add --transport http subetha-router {ENDPOINT}'
        # Parse the rendered shell command, without executing it or making requests.
        argv = shlex.split(page.ids['curl' + suffix]['text'].replace('\\\n', ''))
        assert argv[:5] == ['curl', '-sS', '--max-time', '30', ENDPOINT]
        assert len(argv) == 13, f'Unexpected curl options: {argv}'
        assert argv[5:11:2] == ['-H'] * 3
        assert argv[6:11:2] == ['Content-Type: application/json',
                              'Accept: application/json, text/event-stream',
                              'MCP-Protocol-Version: 2025-03-26']
        assert argv[11] == '--data'
        assert json.loads(argv[12]) == {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
            'params': {'name': 'subetha_router_list_routes', 'arguments': {}}}

    tables = re.findall(r'<tbody>(.*?)</tbody>', source, re.S)
    assert len(tables) == 2 and tables[0] == tables[1]
    assert tables[0].count('<tr>') == 5
    assert Counter(n['attrs']['data-probe'] for n in page.nodes if 'data-probe' in n['attrs']) == {
        'x402': 1, 'mpp': 1, 'x402-ja': 1, 'mpp-ja': 1}
    scripts = re.findall(r'<script>(.*?)</script>', source, re.S)
    assert len(scripts) == 1
    script = scripts[0]
    assert script.count('fetch(') == 1
    require(script, ["fetch(ENDPOINTS[base],{method:'GET'", "'x402':'https://provider-x402.subethalabs.com/v1/eth/snapshot'",
                     "'mpp':'https://provider-mpp.subethalabs.com/v1/eth/snapshot'"])
    endpoint_block = re.search(r'const ENDPOINTS=\{(.*?)\};', script, re.S)[1]
    assert len(re.findall(r'https://', endpoint_block)) == 2
    assert ENDPOINT not in script, 'No browser Router requests'

    # Search rendered text as well as HTML, so tags cannot hide stale assertions.
    flat = source + '\n' + '\n'.join(page.ids[lang]['text'] for lang in ('en', 'ja'))
    forbidden = [r'subetha-router-egt', r'github\.com/subetha-labs/subetha-router',
                 r'git\s+clone', r'npm\s+(?:install|rebuild|run\s+(?:wallet|sign))',
                 r'@subetha/payer', r'\.env(?:\.local)?', r'ownerKey',
                 r'Only\s+purchase\s+costs', r'費用がかかるのは\s*purchase\s*だけ',
                 r'Retrying the call works', r'呼び直せば通ります',
                 r'fails closed and moves no money', r'資金を動かさずに失敗',
                 r'If you decline, nothing was spent', r'断れば、何も支払われていません',
                 r'2 rails / 1 request', r'Two routes, pick', r'routeは2本',
                 r'fully noncustodial', r'deliberately unlinked',
                 r'prompts/list', r'resources/list', r'five minutes', r'5分',
                 r'buy something,', r'from a fresh session', r'phase\s*[-0-9]']
    for pattern in forbidden:
        assert not re.search(pattern, flat, re.I), f'Obsolete/private claim: {pattern}'
    print('ROUTER_STRUCTURE_OK bilingual counts rails commands safety anchors copy-controls A/B-only')


def check_scope(base, source):
    allowed = {'router/index.html', 'scripts/check-router.py', '.github/workflows/validate.yml'}
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=ROOT, text=True)
    changed = set(git('diff', '--name-only', base, '--').splitlines())
    untracked = set(git('ls-files', '--others', '--exclude-standard').splitlines())
    assert changed | untracked <= allowed, f'Out-of-scope changes: {(changed | untracked) - allowed}'
    before = git('show', f'{base}:router/index.html')
    for pattern in (r'<nav\b.*?</nav>', r'<footer\b.*?</footer>',
                    r'<div class="topbar">.*?</div></div>', r'<img\b[^>]*>'):
        assert re.findall(pattern, before, re.S) == re.findall(pattern, source, re.S), f'Changed site chrome: {pattern}'
    # Track all other files, including unrelated pages and official SVGs, byte for byte.
    for name in git('ls-tree', '-r', '--name-only', base).splitlines():
        if name not in allowed:
            prior = subprocess.check_output(['git', 'show', f'{base}:{name}'], cwd=ROOT)
            assert (ROOT / name).read_bytes() == prior, f'Unrelated file changed: {name}'
    print(f'ROUTER_SCOPE_OK base={base} unrelated files, navigation, branding and footers unchanged')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', help='Local Git revision for bounded-change checks; no network access')
    args = parser.parse_args()
    source = (ROOT / 'router/index.html').read_text(encoding='utf-8')
    check_page(source)
    if args.base:
        check_scope(args.base, source)


if __name__ == '__main__':
    main()
