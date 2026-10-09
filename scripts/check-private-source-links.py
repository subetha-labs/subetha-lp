#!/usr/bin/env python3
"""Offline link/copy and archive redirect configuration guard."""
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = 'https://docs.subethalabs.com/'
HISTORY = DOCS + 'reference/payment-history/'
PRIVATE_REPOS = {
    ('peaceandwhisky', 'subetha'),
    ('peaceandwhisky', 'subetha-router'),
    ('subetha-labs', 'subetha-router'),
}


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


def check_links(page):
    for node in page.nodes:
        href = node['attrs'].get('href', '')
        if href.startswith('#'):
            assert unquote(href[1:]) in page.ids, f'Broken anchor: {href}'
        url = urlsplit(href)
        if url.hostname and url.hostname.lower() in {
                'github.com', 'www.github.com', 'raw.githubusercontent.com'}:
            parts = unquote(url.path).lower().strip('/').split('/')
            if len(parts) >= 2:
                repo = (parts[0], parts[1].removesuffix('.git'))
                assert repo not in PRIVATE_REPOS, f'Private product repo href: {href}'


def check_root(page):
    for lang, suffix in [('en', ''), ('ja', '-ja')]:
        nodes = [n for n in page.nodes if n['lang'] == lang]
        links = [n for n in nodes if n['tag'] == 'a']
        for href in (DOCS, HISTORY, '#contact' + suffix):
            assert any(n['attrs'].get('href') == href and n['text'].strip()
                       for n in links), f'Missing {lang} link: {href}'
        assert any(n['attrs'].get('data-copy') == 'contact@subethalabs.com'
                   for n in nodes), f'Missing {lang} contact copy button'
        faq = page.ids['faq' + suffix]['text']
        for marker in (['product repository is currently private', 'Public documentation',
                        'Published SDK packages', 'Contact us to discuss an integration']
                       if lang == 'en' else
                       ['製品リポジトリは現在非公開', '公開ドキュメント',
                        '公開済みのSDKパッケージ', '連携についてご相談']):
            assert marker in faq, f'Missing {lang} FAQ: {marker}'

        # Check decoded rendered text, including headings and text split by tags.
        text = page.ids[lang]['text']
        forbidden = [r'git\s+clone', r'\bclone\b', r'read\s+(?:the\s+)?code',
                     r'run\s+(?:the\s+)?(?:local\s+demo|PoC|reference\s+flow)',
                     r'コードを見る', r'クローン', r'(?:PoC|ローカルデモ)を(?:動か|実行)']
        for pattern in forbidden:
            assert not re.search(pattern, text, re.I), f'Stale {lang} CTA: {pattern}'
    assert any(n['tag'] == 'img' and n['attrs'].get('src') == 'assets/web-demo.png'
               and 'preview' in n['attrs'].get('alt', '') for n in page.nodes)
    assert 'Demo preview' in page.ids['en']['text']
    assert any(n['tag'] == 'a' and n['attrs'].get('href') == '#contact'
               and 'Discuss a demo' in n['text'] for n in page.nodes)


def check_redirects():
    # Preserve the historical HTML; redirect both public archive entry paths.
    # This checks configuration only, not Cloudflare's deployed HTTP behavior.
    routes = [tuple(line.split())
              for line in (ROOT / '_redirects').read_text(encoding='utf-8').splitlines()
              if line.strip() and not line.lstrip().startswith('#')]
    expected = {('/index-v3-previous.html', '/', '302'),
                ('/index-v3-previous', '/', '302')}
    assert len(routes) == len(expected) and set(routes) == expected, \
        f'Expected only the two exact archive redirects to / with 302: {routes}'


def main():
    check_redirects()
    for name in ('index.html', 'router/index.html'):
        page = Page((ROOT / name).read_text(encoding='utf-8'))
        check_links(page)
        if name == 'index.html':
            check_root(page)
    print('PRIVATE_SOURCE_LINKS_OK current root/router hrefs; root EN/JA docs, history, contact, FAQ, preview, anchors')
    print('ARCHIVE_REDIRECT_CONFIG_OK two exact routes to / with 302; deployed behavior not tested')


if __name__ == '__main__':
    main()
