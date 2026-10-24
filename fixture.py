"""Generate a minimal synthetic OOXML text fixture; no clinical source material."""
from xml.sax.saxutils import escape
from zipfile import ZipFile, ZIP_DEFLATED
from slide_audit import P, A, R

def make_deck(path, texts, order=None):
    order = order or list(range(1, len(texts) + 1))
    with ZipFile(path, 'w', ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>')
        ids = ''.join(f'<p:sldId id="{255+i}" r:id="rId{i}"/>' for i in order)
        z.writestr('ppt/presentation.xml', f'<p:presentation xmlns:p="{P}" xmlns:r="{R}"><p:sldIdLst>{ids}</p:sldIdLst></p:presentation>')
        rels = ''.join(f'<Relationship Id="rId{i}" Target="slides/slide{i}.xml" Type="{R}/slide"/>' for i in range(1,len(texts)+1))
        z.writestr('ppt/_rels/presentation.xml.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+rels+'</Relationships>')
        for i,text in enumerate(texts,1):
            z.writestr(f'ppt/slides/slide{i}.xml', f'<p:sld xmlns:p="{P}" xmlns:a="{A}"><p:cSld><p:spTree><p:sp><p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>{escape(text)}</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sld>')
