"""Run: python main.py. All data are synthetic, non-clinical labels."""
import json
from tempfile import TemporaryDirectory
from pathlib import Path
from fixture import make_deck
from slide_audit import extract_pptx, CourseIndex, Enrollment

def run():
    with TemporaryDirectory() as folder:
        path = Path(folder) / 'synthetic_review.pptx'
        make_deck(path, ['Synthetic topic ALPHA: the teaching marker is AMBER.',
                         'Synthetic topic BETA: the teaching marker is VIOLET.'])
        index = CourseIndex()
        index.activate('exam-demo', '2026', extract_pptx(path, 'exam-demo', '2026'))
        user = Enrollment('exam-demo', True, 200)
        before = index.retrieve('exam-demo', 'ALPHA marker', user, now=100)
        unsupported = index.retrieve('exam-demo', 'ZEBRA', user, now=100)
        make_deck(path, ['Synthetic topic ALPHA: the teaching marker is CYAN.'])
        index.activate('exam-demo', '2027', extract_pptx(path, 'exam-demo', '2027'))
        after = index.retrieve('exam-demo', 'ALPHA', user, now=100)
        try:
            index.retrieve('exam-demo', 'ALPHA', Enrollment('other-course', True, 200), 100)
            denied = False
        except PermissionError:
            denied = True
        return {'synthetic_only': True, 'before_update': before, 'unsupported_query': unsupported,
                'after_update': after, 'cross_course_access_denied': denied}

if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
