"""Export a smaller sharing PDF with raster figures and selectable instruction text.

The pinned work package is read-only. The output and its derivative manifest must
live outside it. Requires the compiler dependencies and Playwright Chromium.
"""
import argparse
import collections
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from unittest.mock import patch

from PIL import Image
from playwright.sync_api import sync_playwright
from reportlab.graphics.shapes import Drawing, Image as DrawingImage
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg
from work_instructions import read, write, indexed, make_pdf


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def export(package, output, scale=1.5, quality=86):
    package=package.resolve();output=output.resolve()
    if output.is_relative_to(package):
        raise ValueError('Keep the sharing copy outside the immutable package')
    if output.exists():
        raise ValueError('Sharing copy exists; choose a new output filename')
    c=read(package/'process.json');manifest=read(package/'manifest.json')
    parts=indexed(c['parts']);instances=indexed(c['instances']);requirements=indexed(c['requirements'])
    source_sha=sha(package/'work-instructions.pdf')
    if source_sha!=manifest['outputs_sha256']['work-instructions.pdf']:
        raise ValueError('Source PDF does not match the package manifest')
    ops=[]
    for n,op in enumerate(c['operations'],1):
        counts=collections.Counter(instances[i]['part'] for i in op['install'])
        materials=', '.join(f'{v} x {parts[k]["title"]}' for k,v in counts.items()) or 'No additional installed parts'
        details=[(str(n)+letter,f'figures/{n:02}-{letter}.svg',detail['view']['caption'])
                 for letter,detail in zip('ABCDEFGHIJKLMNOPQRSTUVWXYZ',op.get('details',[]))]
        ops.append((n,op,f'figures/{n:02}-{op["id"]}.svg',materials,
                    [requirements[r]['text'] for r in op['holds']],details))
    with tempfile.TemporaryDirectory(prefix='instruction-sharing-') as tmp:
        temp=Path(tmp);images={}
        with sync_playwright() as pw:
            browser=pw.chromium.launch()
            context=browser.new_context(viewport={'width':1040,'height':600},device_scale_factor=scale,offline=True)
            page=context.new_page()
            for svg in sorted((package/'figures').glob('*.svg')):
                expected=manifest['outputs_sha256'][str(svg.relative_to(package))]
                if sha(svg)!=expected:raise ValueError('Figure hash mismatch '+svg.name)
                page.goto(svg.as_uri())
                png=temp/(svg.stem+'.png');page.locator('svg').screenshot(path=str(png))
                jpg=png.with_suffix('.jpg')
                with Image.open(png) as image:
                    image.convert('RGB').save(jpg,quality=quality,optimize=True)
                images[svg.name]=jpg
            browser.close()

        def raster_drawing(path):
            drawing=Drawing(1040,600)
            drawing.add(DrawingImage(0,0,1040,600,str(images[Path(path).name])))
            # Retain figure labels as a transparent searchable layer as well as
            # their rendered pixels; preserve the original SVG text positions.
            svg=ET.parse(package/'figures'/Path(path).name).getroot()
            for child in list(svg):
                if child.tag!='{http://www.w3.org/2000/svg}text':svg.remove(child)
                else:child.set('fill-opacity','0')
            labels=svg2rlg(io.BytesIO(ET.tostring(svg)))
            labels.scale(1040/labels.width,600/labels.height)
            drawing.add(labels)
            return drawing

        original_draw_string=renderPDF._PDFRenderer.drawString
        def invisible_labels(renderer,string):
            canvas=renderer._canvas;draw=canvas.drawString
            def invisible(*args,**kwargs):
                kwargs['mode']=3  # PDF invisible text; selectable, no duplicate pixels.
                return draw(*args,**kwargs)
            with patch.object(canvas,'drawString',invisible):
                return original_draw_string(renderer,string)

        # Reuse the real compiler's layout; only its figure loader changes.
        with patch('svglib.svglib.svg2rlg',raster_drawing),patch.object(renderPDF._PDFRenderer,'drawString',invisible_labels):
            make_pdf(temp,c,ops,parts,instances,read(package/'geometry.json'),manifest['instruction_sha256'])
        candidate=temp/'work-instructions.pdf'
        original_text=subprocess.check_output(['pdftotext',str(package/'work-instructions.pdf'),'-'],text=True)
        compact_text=subprocess.check_output(['pdftotext',str(candidate),'-'],text=True)
        if original_text.split()!=compact_text.split():
            raise ValueError('Sharing export changed instruction text')
        if candidate.stat().st_size>= (package/'work-instructions.pdf').stat().st_size:
            raise ValueError('Sharing export did not reduce size')
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_bytes(candidate.read_bytes())
    assert source_sha==sha(package/'work-instructions.pdf'),'Pinned PDF changed'
    result={'schema_version':1,'type':'instruction-sharing-derivative',
            'instruction_sha256':manifest['instruction_sha256'],'source_pdf_sha256':source_sha,
            'output_pdf_sha256':sha(output),'output_bytes':output.stat().st_size,
            'source_bytes':(package/'work-instructions.pdf').stat().st_size,
            'figure_dpi':scale*1040/(510/72),'jpeg_quality':quality,
            'text_verified_unchanged':True,'graphics':'rasterized sharing copy; original vector package retained',
            'exporter_sha256':sha(__file__)}
    write(output.with_suffix('.manifest.json'),result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package',type=Path)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(export(args.package,args.out),indent=2))
