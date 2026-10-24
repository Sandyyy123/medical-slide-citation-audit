"""Small deterministic provenance demonstration, not a clinical AI system."""
from dataclasses import dataclass, asdict
from hashlib import sha256
from pathlib import Path
import posixpath
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'

@dataclass(frozen=True)
class Slide:
    course: str
    edition: str
    deck_sha256: str
    deck: str
    number: int
    text: str

    def citation(self):
        return {'course': self.course, 'edition': self.edition,
                'deck': self.deck, 'slide': self.number,
                'deck_sha256': self.deck_sha256}

def extract_pptx(path, course, edition):
    """Read visible text in presentation order; no images/OCR/notes ingestion."""
    path = Path(path)
    digest = sha256(path.read_bytes()).hexdigest()
    with ZipFile(path) as archive:
        rels = ET.fromstring(archive.read('ppt/_rels/presentation.xml.rels'))
        lookup = {r.attrib['Id']: r.attrib for r in rels}
        presentation = ET.fromstring(archive.read('ppt/presentation.xml'))
        slides = []
        for number, sid in enumerate(presentation.findall(f'.//{{{P}}}sldId'), 1):
            rel = lookup[sid.attrib[f'{{{R}}}id']]
            if rel.get('TargetMode') == 'External':
                raise ValueError('External slide references are unsupported')
            target = rel['Target']
            part = target.lstrip('/') if target.startswith('/') else posixpath.normpath('ppt/' + target)
            if not part.startswith('ppt/slides/') or '..' in part.split('/'):
                raise ValueError('Slide reference outside expected package directory')
            root = ET.fromstring(archive.read(part))
            paragraphs = []
            for paragraph in root.findall(f'.//{{{A}}}p'):
                paragraphs.append(''.join(t.text or '' for t in paragraph.findall(f'.//{{{A}}}t')))
            slides.append(Slide(course, edition, digest, path.name, number, '\n'.join(paragraphs).strip()))
    return slides

@dataclass(frozen=True)
class Enrollment:
    """Trusted server-side entitlement fixture; never accept this from a browser."""
    course: str
    paid: bool
    expires_at: int

class CourseIndex:
    def __init__(self):
        self._courses = {}

    def activate(self, course, edition, slides):
        slides = tuple(slides)
        if not slides or any(s.course != course or s.edition != edition for s in slides):
            raise ValueError('Mixed course/edition or empty release')
        self._courses[course] = (edition, slides)

    def retrieve(self, course, query, enrollment, now):
        # Deny before consulting the index. Real integration verifies identity
        # and payment claims on a trusted server, not via this illustrative object.
        if enrollment.course != course or not enrollment.paid or enrollment.expires_at <= now:
            raise PermissionError('Active paid enrollment required')
        if course not in self._courses:
            raise LookupError('Course not available')
        terms = set(re.findall(r'[a-z0-9]+', query.lower())) - {'the', 'a', 'an', 'is', 'what', 'which', 'in', 'of', 'and', 'to', 'for', 'how'}
        edition, slides = self._courses[course]
        scored = []
        for slide in slides:
            tokens = set(re.findall(r'[a-z0-9]+', slide.text.lower()))
            score = len(terms & tokens)
            if score:
                scored.append((score, slide.number, slide))
        scored.sort(key=lambda x: (-x[0], x[1]))
        hits = [{'quote': s.text, 'citation': s.citation(), 'matched_terms': n}
                for n, _, s in scored[:3]]
        return {'status': 'evidence_found' if hits else 'abstain', 'edition': edition,
                'mode': 'deterministic lexical retrieval; no generated medical answer', 'evidence': hits}
