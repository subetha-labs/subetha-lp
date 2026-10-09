#!/usr/bin/env python3
"""Offline scope regression fixtures in a disposable Git index; no commits/browsers."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='mobile-scope-') as directory:
        fixture = Path(directory)

        def git(*args, cwd=fixture):
            return subprocess.check_output(['git', *args], cwd=cwd, text=True).strip()

        # Exercise real pages/checkers without touching the working tree or its index.
        names = git('ls-files', '--cached', '--others', '--exclude-standard', cwd=ROOT).splitlines()
        for name in names:
            source = ROOT / name
            if source.is_file():
                target = fixture / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
        git('init', '--quiet')
        git('add', '.')
        base = git('write-tree')
        script = fixture / 'scripts/check-router.py'

        def run(label, arguments, expected):
            result = subprocess.run([sys.executable, '-B', str(script), *arguments],
                                    cwd=fixture, text=True, capture_output=True)
            output = result.stdout + result.stderr
            if expected is None:
                assert result.returncode == 0, f'{label}: {output}'
            else:
                assert result.returncode != 0 and expected in output, f'{label}: {output}'
            print(f'FIXTURE_OK {label}')

        router = ['--base', base]
        mobile = [*router, '--scope', 'mobile']
        run('unchanged default Router scope', router, None)
        path = fixture / 'router/index.html'
        path.write_text(path.read_text() + '\n')
        run('default Router-only edit accepted', router, None)
        # Also works after merge, when the fixture baseline already contains mobile assets.
        for name in ('index.html', 'assets/mobile.css'):
            path = fixture / name
            path.write_text(path.read_text() + '\n')
        run('mobile exact files accepted with mandatory guards', mobile, None)
        run('default rejects mobile changes', router, 'Out-of-scope changes')
        run('explicit Router rejects mobile changes', [*router, '--scope', 'router'], 'Out-of-scope changes')
        run('mobile requires base', ['--scope', 'mobile'], '--scope mobile requires --base')
        run('missing base fails closed', ['--scope', 'mobile', '--base', 'refs/heads/missing-fixture-base'], 'fatal:')

        def reject(label, name, mutate, expected):
            path = fixture / name
            original = path.read_bytes() if path.exists() else None
            try:
                if mutate is None:
                    path.unlink()
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(mutate(original or b''))
                run(label, mobile, expected)
            finally:
                if original is None:
                    path.unlink()
                else:
                    path.write_bytes(original)

        for name in ('README.md', '_redirects', 'index-v3-previous.html',
                     'assets/brand/subetha-wordmark-color.svg', 'assets/web-demo.png',
                     'scripts/check-private-source-links.py', 'assets/unrelated-fixture.css',
                     'unrelated-fixture.txt'):
            reject(f'protected/unrelated {name}', name, lambda data: data + b'\nfixture',
                   'Out-of-scope changes')
        reject('protected deletion', '_redirects', None, 'Out-of-scope changes')
        for name in ('index.html', 'router/index.html'):
            reject(f'{name} main copy', name,
                   lambda data: data.replace(b'<main id="top">', b'<main id="top">fixture', 1),
                   'changed main copy')
            reject(f'{name} footer', name,
                   lambda data: data.replace(b'<footer>', b'<footer>fixture', 1), 'Changed site chrome')
            reject(f'{name} desktop navigation', name,
                   lambda data: data.replace(b'<nav class="nav">', b'<nav class="nav">fixture', 1),
                   'Changed site chrome')
            reject(f'{name} product script', name,
                   lambda data: data.replace(b'<script>', b'<script>/* fixture */', 1),
                   'changed product scripts')
            reject(f'{name} extra script', name,
                   lambda data: data.replace(b'</head>', b'<script src="/fixture.js"></script></head>', 1),
                   'changed product scripts')
            reject(f'{name} inline style', name,
                   lambda data: data.replace(b'<style>', b'<style>/* fixture */', 1), 'changed original style')
            reject(f'{name} private menu link', name,
                   lambda data: data.replace(b'<summary>',
                       b'<a href="https://github.com/peaceandwhisky/subetha">fixture</a><summary>', 1),
                   'Private product repo href')
        reject('mobile contract remains mandatory', 'assets/mobile.css',
               lambda data: data + b'\nhtml{overflow-x:hidden}', 'AssertionError')
    print('MOBILE_SCOPE_FIXTURES_OK default scope, explicit mobile scope, protected files/copy/scripts/links')


if __name__ == '__main__':
    main()
