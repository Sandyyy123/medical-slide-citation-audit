from pathlib import Path
import pytest
from fixture import make_deck
from slide_audit import CourseIndex, Enrollment, extract_pptx, Slide
from main import run

def test_presentation_order_and_citation(tmp_path):
    p=tmp_path/'ordered.pptx'; make_deck(p, ['FIRST', 'SECOND'], [2,1])
    slides=extract_pptx(p,'course','2026')
    assert [s.text for s in slides] == ['SECOND','FIRST']
    assert [s.number for s in slides] == [1,2]
    assert len(slides[0].deck_sha256)==64
    assert slides[0].citation()['deck']=='ordered.pptx'

@pytest.mark.parametrize('enrollment', [Enrollment('wrong',True,200), Enrollment('c',False,200), Enrollment('c',True,100)])
def test_denies_before_index_access(enrollment):
    with pytest.raises(PermissionError): CourseIndex().retrieve('c','ALPHA',enrollment,100)

def test_course_scope_prevents_cross_course_evidence():
    idx=CourseIndex()
    for course,text in [('c','ALPHA public teaching'),('other','ALPHA restricted teaching')]:
        idx.activate(course,'2026',[Slide(course,'2026','a'*64,'d.pptx',1,text)])
    result=idx.retrieve('c','ALPHA',Enrollment('c',True,200),100)
    assert [h['quote'] for h in result['evidence']]==['ALPHA public teaching']

def test_unsupported_query_abstains():
    assert run()['unsupported_query']['status']=='abstain'
    assert run()['unsupported_query']['evidence']==[]

def test_annual_update_invalidates_old_edition():
    r=run(); old=r['before_update']['evidence'][0]; new=r['after_update']['evidence'][0]
    assert 'AMBER' in old['quote'] and 'CYAN' in new['quote']
    assert old['citation']['deck_sha256'] != new['citation']['deck_sha256']
    assert new['citation']['edition']=='2027'
    assert all(h['citation']['edition']=='2027' for h in r['after_update']['evidence'])

def test_rejects_mixed_release():
    with pytest.raises(ValueError): CourseIndex().activate('c','2027',[Slide('c','2026','a'*64,'d.pptx',1,'ALPHA')])

def test_no_lexical_terms_abstains():
    idx=CourseIndex(); idx.activate('c','2026',[Slide('c','2026','a'*64,'d.pptx',1,'ALPHA')])
    assert idx.retrieve('c','what is the',Enrollment('c',True,200),100)['status']=='abstain'
