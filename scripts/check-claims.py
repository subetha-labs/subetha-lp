#!/usr/bin/env python3
"""Assertion-level claims guard for the served LP output (EN and JA).

Prohibited affirmative claims (anonymity, untraceability, unqualified unlinkability, hidden amounts, "fully
private", trustlessness, production readiness, current mainnet support, npm availability of the SubEtha v2
Provider extension) are detected as trigger patterns. Every trigger occurrence must be consumed by exactly one
exception that names the rule, the complete assertion (one sentence) and an eligible reason (denial, limitation,
plan, technical). An exception never covers a line, paragraph, page or file.

    python3 -B scripts/check-claims.py              # served inventory + the mandatory archive page
    python3 -B scripts/check-claims.py --fixtures   # self-test against tests/claims/{pass,fail}-*
    python3 -B scripts/check-claims.py --report F   # list every trigger occurrence in file F with its sentence
"""
import argparse
import base64
import html
from html.parser import HTMLParser
import importlib.util
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]

RULES = {
    'anonymity': [r'anonym\w*', r'匿名'],
    'untraceability': [r'untraceab\w*', r'cannot be traced', r'hidden (?:service|provider|merchant)s?',
                       r'追跡(?:不可能|不能|できない|できません|されない|されません)', r'サービス(?:を|が)隠'],
    'unlinkable': [r'unlinkab\w*', r'no link exists', r'cannot be (?:linked|correlated)', r'correlation[- ]resistant',
                   r'(?:結び付け|紐付け|関連付け)(?:られない|不可能)', r'相関(?:耐性|できない|不可能)'],
    'hidden-amount': [r'(?:hidden|confidential|private|secret) amounts?',
                      r'amounts? (?:is|are|stays?|remains?) (?:hidden|confidential|private|secret)', r'amount privacy',
                      r'金額(?:は|が|も|の|を)?(?:秘匿|隠|非公開|見えな)'],
    'fully-private': [r'(?:fully|completely|totally|entirely) private', r'完全に(?:プライベート|秘匿|匿名)'],
    'trustless': [r'trustless\w*', r'トラストレス'],
    'production-ready': [r'production[- ](?:ready|grade)', r'ready for production', r'(?:in|for) production (?:use|today|now)',
                         r'本番(?:対応|利用可能|で使え|運用でき|投入)', r'プロダクション(?:対応|レディ)'],
    'mainnet-support': [r'mainnet[- ]?(?:ready|support\w*|available|live)', r'mainnet (?:is|are|now|already) (?:supported|available|live)',
                        r'(?:support\w*|available|live|runs?|running|works?) on [\w ]{0,20}mainnet',
                        r'メインネット(?:対応|で利用|で使え|サポート|稼働|に対応)'],
    'npm-v2': [r'(?:npm|pnpm|yarn) (?:i|install|add)(?: -g)? @subetha/provider', r'npx @subetha/provider',
               r'(?:v2|\./x402|x402 extension)[^.。]{0,60}(?:published on npm|available on npm|npm package)',
               r'npm package[^.。]{0,60}(?:v2|\./x402)', r'(?:v2|拡張)[^.。]{0,40}npm で(?:公開|入手|インストール)'],
}
# Allowed phrases are blanked (same length) before matching, so they never trigger and never hide a neighbour.
ALLOWED = [r'anonymity[- ]sets?', r'匿名性セット', r'匿名集合']
REASONS = ('denial', 'limitation', 'plan', 'technical')
WINDOW = 600          # a marker binds within this many characters of public text
# A Latin full stop ends a sentence only before whitespace or a closing quote/bracket, so "0.1.0" and "x402.org"
# do not split an assertion and cannot hide a frame. CJK terminators always end a sentence.
PUNCT_END = r'[.!?](?=["\')\]+·•]*(?:\s|$))|[。！？]'
SENTENCE_END = re.compile(PUNCT_END + r'|\n')      # assertion boundaries: punctuation and formatting breaks
CONTEXT_END = re.compile(PUNCT_END)                # context boundaries: punctuation only
MARKER = re.compile(r'<!--\s*claims-ok\s+rule=([\w-]+)\s+text="([^"]+)"\s+reason=(\w+)\s*-->')
COMMENT = re.compile(r'<!--.*?-->', re.S)
BLOCK_TAG = re.compile(r'</?(?:p|h[1-6]|li|ul|ol|dl|dt|dd|summary|details|td|th|tr|thead|tbody|tfoot|table|caption|div|section|article|aside|header|footer|main|nav|br|hr|title|pre|blockquote|figure|figcaption|form|fieldset|legend|address|option|textarea|script|style)\b[^>]*>', re.I)
TAG = re.compile(r'<[^>]+>')
CHECKED_ATTRS = ('alt', 'title', 'content', 'aria-label', 'placeholder')
TEXT_SUFFIXES = {'.html', '.htm', '.txt', '.md', '.svg', '.css', '.js'}   # fixture suffixes (plain); the inventory uses BINARY_SUFFIXES
LETTER = re.compile(r'[A-Za-z぀-ヿ一-鿿]')

# Eligibility gates, evaluated on the context (the punctuation-delimited sentence around the assertion).
AFFIRMATIVE = re.compile(
    r"\b(?:is|are|was|were|be|being|been|remains?|stays?|becomes?|get|gets|got)\s+(?:now\s+|already\s+|truly\s+|fully\s+|completely\s+|totally\s+|entirely\s+)?"
    r"(?:anonymous|untraceable|unlinkable|trustless|private|hidden|confidential|production[- ]ready|supported|available|live)\b"
    r"|(?:は|が|も)(?:今や|すでに|完全に)?(?:匿名|追跡不可能|追跡不能|トラストレス|秘匿|非公開|本番対応|メインネット対応)(?:だ|です|である|となる|になる|化)", re.I)
REVERSAL = re.compile(
    r"\b(?:false|untrue|not true|wrong|incorrect|a myth|no longer|not (?:just|only|merely|simply)|except|other than|anything but|nothing but|"
    r"not without|n't without|not un\w+|never without|hardly|barely|scarcely|far from un\w+)\b"
    r"|(?:誤り|間違い|とは限らない|だけでなく|のみならず|もはや|ただし|わけでは|わけでも|ないことは|なくはな|ないとは言え|以外|を除)", re.I)
# Eligibility binds the qualification to the prohibited property itself, not to the sentence at large.
# EN negation: a negating word at most three words before the trigger ("no anonymity", "does not guarantee
# unlinkability or anonymity", "without anonymity"), or the trigger as subject of a negated verb at most two words
# later with no relative pronoun in between ("amount privacy does not carry over"; not "payments that do not").
# JA negation: a negative ending in the same clause within 30 characters after the trigger, where a topic/subject
# particle may follow the trigger only immediately (「金額の秘匿性は…引き継がれません」 yes; 「匿名決済に待ち時間はありません」 no).
NEG_WORD = r"(?:no|not|never|nothing|neither|nor|cannot|can't|doesn't|don't|isn't|aren't|wasn't|weren't|won't|without|non)"
WORD = r"[\w'’-]+"
# Negation directly on the property word ("not anonymous", "no real anonymity"), on a coordination that includes it
# ("no anonymity or unlinkability", "not anonymous, untraceable or"), or on a property verb whose object it is
# ("does not guarantee unlinkability or anonymity"). "No registration for anonymous payments" matches none.
PROPERTY_OBJ_VERB = r"(?:guarantee|provide|offer|ensure|claim|mean|impl(?:y|ies)|make|deliver|give|promise|establish|achieve|bring|add|grant|confer|promote|advertise|sell|market)\w*"
NEG_BEFORE = re.compile(
    r"(?:\b" + NEG_WORD + r"[\s-]+(?:(?:fully|completely|totally|truly|really|any|real|true|the|a|an|its|their|your|our|such|even)\s+)?$"
    r"|\b" + NEG_WORD + r"\s+(?:" + WORD + r"[\s,]+(?:or|nor|and|,)\s+)+$"
    r"|\b(?:not|never|n't|cannot|can't|no)\s+(?:" + WORD + r"\s+)?" + PROPERTY_OBJ_VERB + r"\s+(?:" + WORD + r"[\s,]+){0,3}$)", re.I)
PROPERTY_VERB = r"(?:apply|hold|exist|carry\s+over|follow|mean|imply|make|guarantee|claim|establish|extend|result|survive)"
SUBJECT_TAIL = r"^(?:\s*(?:in|on|for|of|at|here|there|today|itself)\s+" + WORD + r")?\s*"   # "amount privacy", "unlinkability in practice"
NEG_AFTER = re.compile(SUBJECT_TAIL + r"(?:"
                       r"(?:is|are|was|were|remains?|stays?)(?:\s+not|n't|\s+never)\s+(?:claimed|guaranteed|promised|established|provided|assumed|offered|part|the\s+case|a\s+property|a\s+goal|available|included|meant|implied)\b"
                       r"|(?:does|do|did)(?:\s+not|n't|\s+never)\s+" + PROPERTY_VERB +
                       r"|(?:is|are|was|were)\s+(?:not|never)\s+(?:claimed|guaranteed|promised|established|provided|assumed|the\s+case)"
                       r"|(?:cannot|can't|could\s+not)\s+be\s+(?:established|guaranteed|claimed|assumed|verified|quantified))", re.I)
# JA: the negative must sit on a property verb (保証しません, 隠れません, 引き継がれません, 結び付けられない) or be a
# plain copular negation (ではない / ではありません) in the same clause, with a topic marker only right after the trigger.
JA_PROPERTY_NEG = r"(?:(?:保証|提供|実現|主張|確立|成立|引き継が|隠|隠さ|結び付け|結び付き|紐付け|関連付け|追跡|特定|到達)(?:し|され|でき|られ|れ|か|が)?(?:ない|ません|ず)|(?:では|じゃ)(?:ない|ありません)|になりません|にはなりません)"
# After the trigger: at most one particle, then at most 12 characters without another case particle, then the
# negated property verb (「匿名性を保証しません」「金額の秘匿性は引き継がれません」); an object of its own between
# them (「匿名決済は遅延を保証しません」) breaks the binding.
JA_NEG_AFTER = re.compile(r"^(?:(?:し|され|でき|られ|れ|か|が)?(?:ない|ません|ず)(?![\w])"     # the trigger itself ends in the verb stem (金額は隠 + れません)
                          r"|(?:性|化)?(?:は|が|を|も|など|だけ|のみ)?[^、。はをがにへ]{0,12}?" + JA_PROPERTY_NEG +
                          r"|(?:こと|の)?(?:や|も|など|と|、)[^、。]{0,15}?" + JA_PROPERTY_NEG + r")")   # coordinated with another property that the verb negates
JA_NEG_BEFORE = re.compile(r"(?:いいえ|ない|ません|なく)[^、。]{0,6}$")
# A verb that bestows the property on something makes the sentence an affirmation under every reason, unless the
# verb itself is negated ("does not guarantee anonymity" is a denial; "provides anonymous payments" is not).
BESTOW_BEFORE = re.compile(r"\b(?:provides?|providing|offers?|offering|delivers?|enables?|ensures?|guarantees?|achieves?|brings?|gives?|makes?|supports?|features?|includes?|adds?|unlocks?|enjoys?)(?:\s+" + WORD + r"){0,3}[\s`\"“「『]*$", re.I)
BESTOW_NEGATED = re.compile(r"\b" + NEG_WORD + r"(?:\s+" + WORD + r"){0,2}\s+(?:provide|offer|deliver|enable|ensure|guarantee|achieve|bring|give|make|support|feature|include|add)\w*(?:\s+" + WORD + r"){0,3}[\s`\"“「『]*$", re.I)
JA_BESTOW_AFTER = re.compile(r"^[^、。]{0,12}(?:を|が|も)?(?:提供|保証|実現|達成|確保)(?!しない|しません|されない|されません|できない|できません|せず)")
# Limitation: the trigger is the subject of an unverified/unquantified/out-of-scope predicate.
LIMIT_AFTER = re.compile(SUBJECT_TAIL + r"(?:is|are|was|were|remains?|has|have)\s+(?:"
                         r"(?:not|never)\s+(?:been\s+)?(?:verified|quantified|proven|established|observed|measured|shown)"
                         r"|(?:unverified|unquantified|unproven|unknown|unmeasured)"
                         r"|out\s+of\s+(?:the\s+)?(?:verification\s+)?scope|outside\s+the)\b", re.I)
JA_LIMIT_AFTER = re.compile(r"^(?:性|化)?(?:は|が|も)?[^、。はをがにへ]{0,12}?(?:未検証|未確認|定量評価されて(?:おらず|いない|いません)|検証されて(?:おらず|いない|いません)|範囲外)")
# Plan: the trigger is what is planned ("plan to add X", "X is planned"), not something a plan mentions.
PLAN_BEFORE = re.compile(r"\b(?:plan\w*|intend\w*|roadmap)(?:\s+is)?\s+to\s+(?:add|offer|provide|support|extend\s+to|introduce|build|deliver|enable|reach|become|ship|launch)(?:\s+" + WORD + r"){0,2}\s*$", re.I)
PLAN_AFTER = re.compile(SUBJECT_TAIL + r"(?:is|are|remains?)\s+(?:planned|intended|a plan|on the roadmap|not yet)\b", re.I)
JA_PLAN_AFTER = re.compile(r"^(?:性|化)?(?:(?:(?!向上|改善|強化|拡充)[^、。は]){0,3}(?:は|を|へ|に))?(?:(?!向上|改善|強化|拡充)[^、。は]){0,20}?(?:計画|予定)")
# Technical: the term is quoted and talked about as a term.
QUOTED = re.compile(r"[`\"“「『]([^`\"”」』]{1,80})[`\"”」』]")
META_TERM = re.compile(r"\b(?:the (?:word|term|literal|label|name)|is (?:used|spelled|written|called|named)|refers to)\b|(?:という(?:語|言葉|用語)|と呼ぶ|の表記)", re.I)
QUESTION_ANSWER_NO = re.compile(r"^[\s+·•\-–—]*(?:No\b|いいえ)")
NEAR = 60

# Per-occurrence exceptions for public files this task may not edit (rule, sentence fragment, reason, count).
# Each entry consumes exactly `count` occurrences of `rule` whose assertion contains `fragment` and passes the
# eligibility gates; fewer or more fail. No entry exempts another assertion in the same sentence or line.
EXTERNAL = {
    'router/index.html': [
        ('unlinkable', 'it does not guarantee unlinkability or anonymity', 'denial', 1),
        ('anonymity', 'it does not guarantee unlinkability or anonymity', 'denial', 1),
        ('anonymity', 'Does this make my payments anonymous?', 'denial', 1),
        ('unlinkable', 'Separate funding does not guarantee unlinkability or anonymity', 'denial', 1),
        ('anonymity', 'Separate funding does not guarantee unlinkability or anonymity', 'denial', 1),
        ('anonymity', '支払い同士を関連付けられないことや匿名性を保証しません', 'denial', 2),
        ('unlinkable', '支払い同士を関連付けられないことや匿名性を保証しません', 'denial', 2),
        ('anonymity', '支払いは匿名になりますか？', 'denial', 1),
        ('production-ready', '本番運用できますか？', 'denial', 1),
    ],
    'router/llms.txt': [
        ('anonymity', 'No anonymity or unlinkability is claimed', 'denial', 1),
        ('unlinkable', 'No anonymity or unlinkability is claimed', 'denial', 1),
    ],
    'index-v3-previous.html': [
        ('anonymity', 'Is this anonymous payment or a mixer?', 'denial', 1),
        ('anonymity', '匿名決済やミキサーですか？', 'denial', 1),
        ('production-ready', '本番運用できますか？', 'denial', 1),
    ],
}


class Attrs(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.values = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in CHECKED_ATTRS and value:
                self.values.append((tag, name, value))


# A literal space in a trigger matches any run of whitespace, so ordinary line wrapping cannot split a trigger.
PATTERNS = {rule: re.compile('|'.join(f'(?:{p})' for p in pats).replace(' ', r'\s+'), re.I) for rule, pats in RULES.items()}
ALLOWED_RE = re.compile('|'.join(ALLOWED), re.I)


def blank_allowed(text):
    return ALLOWED_RE.sub(lambda m: ' ' * len(m.group(0)), text)


def public_text(source, is_html=True):
    """Return (text, markers): comments removed, block tags → line breaks, other tags → spaces, entities decoded.

    Markers are read before removal and keep their position in the returned text.
    """
    markers = []

    def keep(match):
        rule, text, reason = match.group(1), match.group(2), match.group(3)
        markers.append({'rule': rule, 'text': ' '.join(html.unescape(text).split()), 'reason': reason})
        return f'\x01CLAIMSOK{len(markers) - 1}\x02'

    staged = MARKER.sub(keep, source.replace('\x01', ' ').replace('\x02', ' '))   # binary noise can never forge a sentinel
    if is_html:
        staged = staged.replace('\r', ' ').replace('\n', ' ')   # a source newline renders as a space in HTML
    # Comments, inline tags and <wbr> render nothing: remove them without inserting a space, so
    # "anon<!-- x -->ymous", "anon<wbr>ymous" and "anon<span>ymous</span>" stay one word.
    staged = COMMENT.sub('', staged)
    staged = BLOCK_TAG.sub('\n', staged)
    staged = TAG.sub('', staged)        # any remaining tag is inline (span, samp, kbd, img, …): it renders no space
    staged = html.unescape(staged)
    staged = re.sub(r'[ \t\r\f\v]+', ' ', staged)
    out, removed, last = [], 0, 0
    for match in re.finditer(r'\x01CLAIMSOK(\d+)\x02', staged):
        out.append(staged[last:match.start()])
        markers[int(match.group(1))]['pos'] = match.start() - removed
        removed += match.end() - match.start()
        last = match.end()
    out.append(staged[last:])
    return ''.join(out), markers


def spans_of(text, pattern):
    spans, start = [], 0
    for match in pattern.finditer(text):
        spans.append((start, match.end()))
        start = match.end()
    spans.append((start, len(text)))
    return spans


def normalise(fragment):
    return ' '.join(fragment.split()).strip(' +·•-–—')


def occurrences(text):
    blanked = blank_allowed(text)
    assertions = spans_of(blanked, SENTENCE_END)
    contexts = spans_of(blanked, CONTEXT_END)
    found = []
    for rule, pattern in PATTERNS.items():
        for match in pattern.finditer(blanked):
            index = next(i for i, s in enumerate(assertions) if s[0] <= match.start() < s[1])
            s0, s1 = assertions[index]
            c0, c1 = next(c for c in contexts if c[0] <= match.start() < c[1])
            following = ''
            for later in assertions[index + 1:]:
                candidate = text[later[0]:later[1]]
                if LETTER.search(candidate):
                    following = candidate
                    break
            # Words of the same punctuation-delimited sentence that a formatting break separated from the assertion.
            outside = text[c0:s0] + text[s1:c1]
            found.append({'rule': rule, 'start': match.start(), 'end': match.end(), 'match': text[match.start():match.end()],
                          'sentence_text': normalise(text[s0:s1]), 'context_text': normalise(text[c0:c1]),
                          'before': ' '.join(text[c0:match.start()].split()), 'after': ' '.join(text[match.end():c1].split()),
                          'split': bool(LETTER.search(outside)), 'following': following, 'consumed': None})
    found.sort(key=lambda o: o['start'])
    return found


def negated(before, after):
    """True when a negation applies to the trigger itself (see the regexes above)."""
    return bool(NEG_BEFORE.search(before + ' ') or NEG_AFTER.search(after) or JA_NEG_AFTER.search(after) or JA_NEG_BEFORE.search(before))


def bestowed(before, after):
    """True when a verb bestows the property on something and that verb is not negated."""
    if BESTOW_BEFORE.search(before + ' ') and not BESTOW_NEGATED.search(before + ' '):
        return True
    return bool(JA_BESTOW_AFTER.search(after))


def eligible(occ, reason):
    """Return None when the assertion, read in its context, is an eligible exception for `reason`, else the problem."""
    if occ['split']:
        return 'the assertion is split across formatting boundaries from other words of its sentence (ambiguous)'
    context, following = occ['context_text'], occ['following']
    if AFFIRMATIVE.search(context):
        return 'the sentence affirms a prohibited property'
    if REVERSAL.search(context):
        return 'the sentence contains a meaning-reversing frame and is ambiguous'
    before, after = occ['before'], occ['after']
    question = context.endswith(('?', '？')) and bool(QUESTION_ANSWER_NO.search(following or ''))
    if not question and bestowed(before, after):
        return 'a verb bestows the prohibited property (provides / guarantees / 提供 …) and is not negated'
    if reason == 'denial':
        if negated(before, after) or question:
            return None
        return 'a denial needs a negation applying to the property, or a question answered with No / いいえ'
    if reason == 'limitation':
        if negated(before, after) or LIMIT_AFTER.search(after) or JA_LIMIT_AFTER.search(after):
            return None
        return 'a limitation needs a negation or an unverified/unquantified/out-of-scope predicate applying to the property'
    if reason == 'plan':
        if PLAN_BEFORE.search(before) or PLAN_AFTER.search(after) or JA_PLAN_AFTER.search(after):
            return None
        return 'a plan must plan the property itself ("plan to …", "… is planned", 「…を計画」)'
    if reason == 'technical':
        quoted = any(PATTERNS[occ['rule']].search(blank_allowed(q)) for q in QUOTED.findall(context)) or occ.get('in_code')
        if quoted and META_TERM.search(context):
            return None
        return 'a technical explanation must quote the term and talk about it as a term (the word …, is used, refers to)'
    return f'reason must be one of {", ".join(REASONS)}'


def check_text(name, source, external=()):
    errors = []
    text, markers = public_text(source, name.endswith(('.html', '.htm', '.svg')))
    occs = occurrences(text)
    for occ in occs:   # a term written inside <code>…</code> in the source may be discussed as a term (technical)
        occ['in_code'] = bool(re.search(r'<code\b[^>]*>[^<]*' + re.escape(occ['match']) + r'[^<]*</code>', source, re.I))
    for i, marker in enumerate(markers):
        label = f'{name}: marker {i + 1} rule={marker["rule"]} text="{marker["text"]}"'
        if marker['rule'] not in RULES:
            errors.append(f'{label}: unknown rule')
            continue
        if marker['reason'] not in REASONS:
            errors.append(f'{label}: reason must be one of {", ".join(REASONS)}')
            continue
        inner = list(PATTERNS[marker['rule']].finditer(blank_allowed(marker['text'])))
        if len(inner) != 1:
            errors.append(f'{label}: exception text must contain exactly one {marker["rule"]} trigger, found {len(inner)}')
            continue
        if SENTENCE_END.search(marker['text'][:-1]):
            errors.append(f'{label}: exception text spans more than one sentence')
            continue
        bound = None
        for occ in occs:
            if occ['rule'] != marker['rule'] or occ['consumed'] or occ['start'] < marker['pos']:
                continue
            if occ['start'] - marker['pos'] > WINDOW:
                break
            if occ['sentence_text'] == normalise(marker['text']):
                bound = occ
                break
        if bound is None:
            errors.append(f'{label}: no {marker["rule"]} occurrence whose complete sentence equals this text within {WINDOW} characters after the marker')
            continue
        problem = eligible(bound, marker['reason'])
        if problem:
            errors.append(f'{label}: not eligible as {marker["reason"]}: {problem}')
            continue
        bound['consumed'] = f'marker {i + 1} ({marker["reason"]})'
    for rule, fragment, reason, count in external:
        hits = [o for o in occs if o['rule'] == rule and not o['consumed'] and fragment in o['sentence_text']]
        if len(hits) != count:
            errors.append(f'{name}: external exception rule={rule} "{fragment}" expects {count} occurrence(s), found {len(hits)}')
            continue
        for occ in hits:
            problem = eligible(occ, reason)
            if problem:
                errors.append(f'{name}: external exception rule={rule} "{fragment}" not eligible as {reason}: {problem}')
            else:
                occ['consumed'] = f'external ({reason})'
    for occ in occs:
        if not occ['consumed']:
            errors.append(f'{name}: unexempted {occ["rule"]} assertion "{occ["match"]}" in: {occ["sentence_text"][:160]}')
    if name.endswith(('.html', '.htm', '.svg')):
        for tag, attr, value in Attrs(source).values:
            blanked = blank_allowed(value)
            for rule, pattern in PATTERNS.items():
                if pattern.search(blanked):
                    errors.append(f'{name}: {rule} trigger inside <{tag} {attr}> cannot be exempted: {value[:120]}')
    return errors, occs


def links_module():
    spec = importlib.util.spec_from_file_location('links', ROOT / 'scripts/check-private-source-links.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LINKS = None


def scan_text(path):
    """Every inventory file is scanned, binaries included (UTF-8 with undecodable bytes replaced); the shared
    classification is kept only so that an unclassifiable artifact still fails closed."""
    data = path.read_bytes()
    LINKS.classify_bytes(path.name, data)
    return data.decode('utf-8', errors='replace')


def inventory():
    global LINKS
    LINKS = LINKS or links_module()
    return LINKS.public_inventory()


def check_inventory():
    errors, counted = [], 0
    names = inventory()
    for name in names:
        found, occs = check_text(name, scan_text(ROOT / name), EXTERNAL.get(name, ()))
        errors += found
        counted += len(occs)
    for name in EXTERNAL:
        assert name in names, f'External exceptions refer to a file outside the inventory: {name}'
    return errors, counted


def load_fixture(path):
    if path.suffix == '.b64':
        return path.with_suffix('').name, base64.b64decode(path.read_bytes()).decode('utf-8', errors='replace')
    return path.name, path.read_text(encoding='utf-8')


REQUIRED_FIXTURES = (
    'fail-en-denial-plus-affirmation.html', 'fail-ja-denial-plus-affirmation.html', 'fail-mixed-denial-plus-affirmation.html',
    'fail-en-two-clauses.html', 'fail-ja-two-clauses.html', 'fail-en-false-denial.html', 'fail-ja-false-denial.html',
    'fail-en-reversed-frame.html', 'fail-ja-reversed-frame.html', 'fail-en-substring-text.html',
    'fail-en-split-frame-br.html', 'fail-ja-split-frame-br.html', 'fail-en-split-frame-newline.txt', 'fail-ja-split-frame-newline.txt',
    'fail-en-text-spans-sentences.html', 'fail-en-text-two-triggers.html', 'fail-en-wrong-rule.html',
    'fail-en-marker-too-far.html', 'fail-en-attribute.html', 'fail-en-unrelated-negation.html', 'fail-ja-unrelated-negation.html',
    'fail-en-technical-affirmation.html', 'fail-en-limitation-unrelated-cue.html', 'fail-en-relative-clause-negation.html',
    'fail-ja-topic-shift-negation.html', 'fail-en-quoted-affirmation.html', 'fail-en-limitation-nearby-cue.html', 'fail-en-plan-mention.html',
    'fail-en-bestowing-verb.html', 'fail-ja-bestowing-verb.html', 'fail-en-limitation-positive-verified.html',
    'fail-en-denial-unrelated-predicate.html', 'fail-ja-denial-unrelated-predicate.html', 'fail-en-plan-improve.html',
    'fail-en-wrapped-line.html', 'fail-en-wrapped-mainnet.html', 'fail-ja-plan-improve.html', 'fail-en-not-delayed.html',
    'fail-en-no-registration-for.html', 'fail-ja-unrelated-guarantee.html', 'fail-en-inline-code-split.html',
    'fail-ja-inline-strong.html', 'fail-en-inline-span-split.html', 'fail-en-noun-modifier-imply.html',
    'fail-en-noun-modifier-guaranteed.html', 'fail-en-comment-split.html', 'fail-en-wbr-split.html',
    'fail-en-double-negation.html', 'fail-en-anything-but.html', 'fail-ja-double-negation.html', 'fail-en-samp-split.html',
    'fail-en-binary-embedded.png',
)


def check_fixtures():
    directory = ROOT / 'tests/claims'
    cases = sorted(p for p in directory.iterdir() if p.suffix in TEXT_SUFFIXES or p.suffix == '.b64')
    LINKS_LOCAL = links_module()
    assert cases, 'no claims fixtures'
    seen, failing_rules = [], set()
    for path in cases:
        name, source = load_fixture(path)
        seen.append(name)
        if name.endswith('.png'):
            assert LINKS_LOCAL.classify_bytes(name, base64.b64decode(path.read_bytes())) == 'binary', f'{name}: the embedded-claim sample must be a well-formed PNG'
        expect = re.search(r'<!--\s*expect:\s*(.+?)\s*-->', source)
        errors, occs = check_text(name, source)
        if name.startswith('pass-'):
            assert not errors, f'{name} should pass: {errors}'
        elif name.startswith('fail-'):
            assert path.suffix == '.b64', f'{name}: fail fixtures must be stored base64-encoded'
            assert expect, f'{name} needs an <!-- expect: … --> line'
            assert errors, f'{name} should fail'
            assert any(expect.group(1) in e for e in errors), f'{name}: expected "{expect.group(1)}", got {errors}'
            failing_rules |= {o['rule'] for o in occs if not o['consumed']}
        else:
            raise AssertionError(f'fixture name must start with pass- or fail-: {name}')
        print(f'FIXTURE_OK {name}')
    for required in REQUIRED_FIXTURES:
        assert required in seen, f'missing required fixture {required}'
    for rule in RULES:
        assert f'fail-en-{rule}.html' in seen and f'fail-ja-{rule}.html' in seen, f'missing bare affirmation fixtures for {rule}'
    assert failing_rules == set(RULES), f'fixtures must exercise every rule; missing {set(RULES) - failing_rules}'
    print(f'CLAIMS_FIXTURES_OK {len(cases)} fixtures, every rule exercised in EN and JA')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--fixtures', action='store_true', help='self-test against tests/claims')
    parser.add_argument('--report', metavar='FILE', help='list every trigger occurrence in FILE with its sentence')
    args = parser.parse_args()
    if args.report:
        source = Path(args.report).read_text(encoding='utf-8')
        found, occs = check_text(args.report, source, EXTERNAL.get(args.report, ()))
        for occ in occs:
            print(f'{occ["rule"]:18} {occ["consumed"] or "UNEXEMPTED":28} {occ["match"]!r}: {occ["sentence_text"][:140]}')
        for error in found:
            print('ERROR', error)
        return
    if args.fixtures:
        check_fixtures()
        return
    errors, counted = check_inventory()
    for error in errors:
        print(error)
    if errors:
        sys.exit(1)
    print(f'CLAIMS_OK {len(RULES)} rules, {counted} trigger occurrence(s), every one bound to an eligible assertion-level exception')


if __name__ == '__main__':
    main()
