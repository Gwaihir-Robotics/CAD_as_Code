"""Common-part bubbles must preserve individual installation identity."""
import copy
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from work_instructions import callout_groups,callout_labels,read,svg_view,validate,impact

FLY=Path(__file__).resolve().parents[2]/'stator-winder/fly'

class GroupedCalloutTests(unittest.TestCase):
    def setUp(self):
        self.c=read(FLY/'config/work-instructions/pilot-r006.json')
        self.op=next(o for o in self.c['operations'] if o['id']=='s1.P020')

    def test_identical_m6_screws_share_number_with_distinct_locations(self):
        groups=callout_groups(self.c,self.op)
        self.assertEqual([(g['number'],g['part'],g['quantity']) for g in groups],[(1,'pn.hrp85',1),(2,'pn.m6x20',4)])
        self.assertEqual([i['label'] for i in groups[1]['instances']],['2a','2b','2c','2d'])
        self.assertEqual(len({i['instance_id'] for i in groups[1]['instances']}),4)

    def test_different_part_numbers_are_not_merged_by_thread_size(self):
        new=copy.deepcopy(next(i for i in self.c['instances'] if i['id']=='s1.mount-bolt.1'));new.update(id='s1.different-length',part='pn.m6x30')
        self.c['instances'].append(new);self.op['uses'].append(new['id'])
        self.assertEqual([(g['part'],g['quantity']) for g in callout_groups(self.c,self.op)],[('pn.hrp85',1),('pn.m6x20',4),('pn.m6x30',1)])

    def test_detail_subset_keeps_parent_labels(self):
        op=next(o for o in self.c['operations'] if o['id']=='s1.P030');detail=op['details'][0]
        g=read(FLY/'output/work-instructions/cache/geometry-r006.json')
        svg=svg_view(self.c,g,dict(id=detail['id'],uses=detail['uses'],install=[],view=detail['view']),labels=callout_labels(self.c,op))
        labels=re.findall(r'font-size="11">([0-9]+[a-z]*)</text>',svg)
        self.assertEqual(labels,['1','3a','3b','3c','3d','4a','4b','4c','4d'])

    def test_second_station_reuses_labels_but_not_instance_ids(self):
        second=next(o for o in self.c['operations'] if o['id']=='s2.P020')
        a,b=callout_labels(self.c,self.op),callout_labels(self.c,second)
        self.assertEqual(list(a.values()),list(b.values()));self.assertFalse(set(a)&set(b))

    def test_labels_extend_beyond_26_locations(self):
        iid=self.op['uses'][1];part=next(i['part'] for i in self.c['instances'] if i['id']==iid)
        self.op['uses']=[]
        for n in range(28):
            item={'id':'extra.'+str(n),'part':part};self.c['instances'].append(item);self.op['uses'].append(item['id'])
        labels=list(callout_labels(self.c,self.op).values())
        self.assertEqual(labels[25:],['1z','1aa','1ab'])

    def test_style_change_requires_review_without_changing_bom(self):
        old=copy.deepcopy(self.c);old.pop('callout_style')
        self.assertEqual(len(impact(old,self.c,{'instances':{}},{'instances':{}})['needs_review']),len(self.c['operations']))
        self.assertEqual(old['bom'],self.c['bom'])

    def test_stale_crop_geometry_rejected(self):
        g=read(FLY/'output/work-instructions/cache/geometry-r006.json');self.c['operations'][1]['details'][1]['view']['crop_box_mm'][0]+=1
        with self.assertRaisesRegex(ValueError,'Stale cropped detail'):validate(self.c,g=g)

if __name__=='__main__':unittest.main()
