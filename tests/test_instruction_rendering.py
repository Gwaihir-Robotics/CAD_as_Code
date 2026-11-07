"""Technical drawings must retain shape edges without exposing mesh diagonals."""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from work_instructions import technical_mesh


class TechnicalDrawingTests(unittest.TestCase):
    def test_coplanar_faces_weld_seam_without_drawing_diagonal(self):
        # Duplicate vertices model the tessellation seam between imported faces.
        points=[[0,0,0],[2,0,0],[2,2,0],[0,0,0],[2,2,0],[0,2,0]]
        shape={'points':points,'triangles':[[0,1,2],[3,4,5]],'solid_count':0}
        svg=''.join(s for _,s in technical_mesh(shape,points,lambda p:p[:2],'context'))
        self.assertEqual(len(re.findall(r'M [-0-9.]+ [-0-9.]+ L',svg)),4)
        self.assertNotIn('M 0.00 0.00 L 2.00 2.00',svg)
        self.assertNotIn('M 2.00 2.00 L 0.00 0.00',svg)

    def test_perpendicular_faces_keep_the_shared_feature_edge(self):
        points=[[0,0,0],[2,0,0],[2,2,0],[0,0,0],[2,0,0],[0,0,2]]
        shape={'points':points,'triangles':[[0,1,2],[3,4,5]],'solid_count':0}
        svg=''.join(s for _,s in technical_mesh(shape,points,lambda p:p[:2],'context'))
        self.assertEqual(len(re.findall(r'M [-0-9.]+ [-0-9.]+ L',svg)),5)
        self.assertEqual(svg.count('M 0.00 0.00 L 2.00 0.00'),1)


if __name__=='__main__':unittest.main()
