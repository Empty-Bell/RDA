"""Authority extraction contracts, not applicability or compliance rules."""
from html.parser import HTMLParser
import re
import xml.etree.ElementTree as ET

SECTIONS = ('305.2', '305.3', '305.9', '305.13', '305.14', '305.15', '305.16', '305.25', '305.27')


def title_version(data):
    titles = data.get('titles') if isinstance(data, dict) else None
    if not isinstance(titles, list): raise ValueError('eCFR titles unavailable')
    selected = [t for t in titles if t.get('number') == 16]
    if len(selected) != 1: raise ValueError('Title 16 missing/ambiguous')
    value = selected[0]
    for key in ('latest_issue_date', 'up_to_date_as_of'):
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(value.get(key, ''))):
            raise ValueError('eCFR date unavailable')
    return {k: value.get(k) for k in ('number', 'name', 'latest_issue_date', 'latest_amended_on', 'up_to_date_as_of')}


def cfr_sections(body):
    if b'<!DOCTYPE' in body.upper() or b'<!ENTITY' in body.upper():
        raise ValueError('XML DTD/entity declarations rejected')
    root = ET.fromstring(body)
    result = []
    for number in SECTIONS:
        matches = [e for e in root.iter() if e.get('TYPE') == 'SECTION' and e.get('N') == number]
        if len(matches) != 1: raise ValueError('eCFR section missing/ambiguous: ' + number)
        section = matches[0]; heading = section.find('HEAD')
        if heading is None or number not in ''.join(heading.itertext()):
            raise ValueError('eCFR heading drift')
        paragraphs = [' '.join(' '.join(e.itertext()).split()) for e in section.findall('P')]
        if not paragraphs or any(not text for text in paragraphs): raise ValueError('eCFR paragraphs unavailable')
        result.append({'section': number, 'heading': ''.join(heading.itertext()), 'paragraphs': paragraphs})
    return result


class MainText(HTMLParser):
    def __init__(self):
        super().__init__(); self.active = False; self.skip = 0; self.count = 0; self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == 'main': self.active = True; self.count += 1
        if tag in ('script', 'style'): self.skip += 1

    def handle_endtag(self, tag):
        if tag == 'main': self.active = False
        if tag in ('script', 'style'): self.skip -= 1

    def handle_data(self, value):
        if self.active and not self.skip: self.parts.append(value)


def criteria_text(html, title):
    parser = MainText(); parser.feed(html)
    text = ' '.join(' '.join(parser.parts).split())
    if parser.count != 1 or title not in text: raise ValueError('Criteria main/title missing or drifted')
    return {'title': title, 'selector': 'main; script/style excluded', 'text': text}
