import json
from pathlib import Path
import tempfile
import unittest
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from compact_instruction_pdf import export

class SharingExportTests(unittest.TestCase):
    def test_cannot_write_inside_pinned_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            package=Path(tmp)
            with self.assertRaisesRegex(ValueError,'immutable package'):export(package,package/'smaller.pdf')

    def test_cannot_replace_an_existing_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            package=Path(tmp)/'package';package.mkdir();output=Path(tmp)/'copy.pdf';output.write_bytes(b'keep')
            with self.assertRaisesRegex(ValueError,'exists'):export(package,output)
            self.assertEqual(output.read_bytes(),b'keep')

    def test_rejects_pdf_that_differs_from_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            package=Path(tmp)/'package';package.mkdir()
            (package/'process.json').write_text(json.dumps({'parts':[],'instances':[],'requirements':[]}))
            (package/'manifest.json').write_text(json.dumps({'outputs_sha256':{'work-instructions.pdf':'0'*64}}))
            (package/'work-instructions.pdf').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'manifest'):export(package,Path(tmp)/'copy.pdf')

if __name__=='__main__':unittest.main()
