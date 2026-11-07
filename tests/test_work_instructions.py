import copy,json,sys,tempfile,unittest,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from work_instructions import validate,impact,read,generate
from build_records import connect,ingest,export,acknowledge,summary
ROOT=Path(__file__).resolve().parents[1]; FLY=ROOT.parent/'stator-winder/fly'; CONFIG=FLY/'config/work-instructions/pilot-r001.json'
class ProcessTests(unittest.TestCase):
 def setUp(self): self.c=read(CONFIG)
 def bad(self,fn):
  c=copy.deepcopy(self.c);fn(c)
  with self.assertRaises(Exception):validate(c)
 def test_valid(self):validate(self.c,FLY)
 def test_duplicate_ids(self):self.bad(lambda c:c['instances'].append(c['instances'][0]))
 def test_missing_id(self):self.bad(lambda c:c['instances'][0].pop('id'))
 def test_unresolved(self):self.bad(lambda c:c['operations'][0]['uses'].append('missing'))
 def test_cycle(self):self.bad(lambda c:c['operations'][0]['prerequisites'].append('F040'))
 def test_bom_qty(self):self.bad(lambda c:c['bom'][0].update(quantity=999))
 def test_double_install(self):self.bad(lambda c:c['operations'][1]['install'].append(c['operations'][0]['install'][0]))
 def test_hardware_missing_placement(self):self.bad(lambda c:next(i for i in c['instances'] if 'placement' in i).pop('placement'))
 def test_missing_spec(self):self.bad(lambda c:next(i for i in c['parts'] if i['kind']=='hardware').pop('spec'))
 def test_hold_prevents_release(self):self.bad(lambda c:(c.update(status='released'),c['packages'][0].update(status='released',reviewed_by='test')))
 def test_stale_hash(self):
  c=copy.deepcopy(self.c);c['sources'][0]['sha256']='0'*64
  with self.assertRaises(ValueError):validate(c,FLY)
 def test_impact_downstream(self):
  c=copy.deepcopy(self.c);c['operations'][4]['instructions'].append('Revised fit check')
  r=impact(self.c,c,{'instances':{}},{'instances':{}})
  self.assertEqual(r['needs_review'],['s1.P010','s1.P020','s1.P030'])
 def test_geometry_change(self):
  r=impact(self.c,self.c,{'instances':{'s1.hrp85':{'sha256':'a'}}},{'instances':{'s1.hrp85':{'sha256':'b'}}})
  self.assertEqual(r['needs_review'],['s1.P010','s1.P020','s1.P030'])
 def test_datums_invalidate(self):
  c=copy.deepcopy(self.c);c['datums'][0]['description']+=' revised'
  self.assertEqual(len(impact(self.c,c,{'instances':{}},{'instances':{}})['needs_review']),len(c['operations']))
 def test_bom_hardware_spec_matches_source(self):
  c=copy.deepcopy(self.c);next(p for p in c['parts'] if p['id']=='pn.m6x20')['spec']['length_mm']=30
  with self.assertRaises(ValueError):validate(c,FLY)
 def test_instance_change_invalidates(self):
  c=copy.deepcopy(self.c);next(i for i in c['instances'] if i['id']=='s1.mount-bolt.1')['placement']['seat_mm'][1]+=1
  self.assertEqual(impact(self.c,c,{'instances':{}},{'instances':{}})['needs_review'],['s1.P020','s1.P030'])
class ExecutionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.definition=Path(self.tmp.name);c=read(CONFIG);(self.definition/'process.json').write_text(json.dumps(c));(self.definition/'manifest.json').write_text(json.dumps({'instruction_sha256':'a'*64}));self.db=connect(':memory:')
  self.e=dict(schema_version=1,event_id=str(uuid.uuid4()),event_type='assembly.operation_completed',occurred_at_utc='2026-11-06T12:00:00Z',product_id=c['product'],variant_id=c['variant'],instruction_revision=c['revision'],instruction_sha256='a'*64,build_id='demo-1',work_order_id='demo-wo',operation_instance_id='demo-1.s1.P020',operation_id='s1.P020',actor='simulated-assembler',payload={})
 def tearDown(self):self.db.close();self.tmp.cleanup()
 def test_dedup_retry_ack(self):
  ingest(self.db,[self.e,self.e],self.definition);self.assertEqual(self.db.execute('select count(*) from events').fetchone()[0],1)
  p=self.definition/'export.json';export(self.db,p);export(self.db,p);self.assertEqual(len(read(p)['events']),1);self.assertEqual(self.db.execute('select attempts from outbox').fetchone()[0],2)
  acknowledge(self.db,[self.e['event_id']]);export(self.db,p);self.assertEqual(read(p)['events'],[])
 def test_conflicting_id_rejected(self):
  ingest(self.db,[self.e],self.definition);e=copy.deepcopy(self.e);e['actor']='different'
  with self.assertRaises(ValueError):ingest(self.db,[e],self.definition)
 def test_completion_not_acceptance(self):
  ingest(self.db,[self.e],self.definition);self.assertNotIn('quality',summary(self.db)['demo-1']['operations']['s1.P020'])
 def test_reject_acceptance_on_completion(self):
  self.e['payload']['disposition']='accepted'
  with self.assertRaises(ValueError):ingest(self.db,[self.e],self.definition)
 def test_unapproved_inspection(self):
  self.e.update(event_type='assembly.inspection_recorded',payload={'inspection_requirement_id':'s1.P020.check.1','disposition':'accepted','evidence_id':'demo-evidence'})
  with self.assertRaises(ValueError):ingest(self.db,[self.e],self.definition)
 def test_wrong_revision(self):
  self.e['instruction_revision']='r002'
  with self.assertRaises(ValueError):ingest(self.db,[self.e],self.definition)
 def test_wrong_part(self):
  self.e['payload']['part_instance_id']='s2.hrp85'
  with self.assertRaises(ValueError):ingest(self.db,[self.e],self.definition)
 def test_append_correction_retains_evidence(self):
  self.e.update(event_type='assembly.inspection_recorded',payload={'inspection_requirement_id':'s1.P020.check.1','disposition':'rejected','evidence_id':'evidence-1'})
  ingest(self.db,[self.e],self.definition);e=copy.deepcopy(self.e);e['event_id']=str(uuid.uuid4());e['payload'].update(disposition='pending',supersedes_event_id=self.e['event_id'],evidence_id='evidence-2');ingest(self.db,[e],self.definition)
  self.assertEqual(self.db.execute('select count(*) from events').fetchone()[0],2)
if __name__=='__main__':unittest.main()

class ArtifactIntegrityTests(unittest.TestCase):
 @unittest.skipUnless((FLY/'output/work-instructions/two-station-8110/r001/manifest.json').exists(),'Generate pilot first')
 def test_refuses_changed_existing_revision(self):
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp);c=read(CONFIG);(out/'r001').mkdir();(out/'r001/manifest.json').write_text(json.dumps({'instruction_sha256':'0'*64}));geo=FLY/'output/work-instructions/cache/geometry-current.json'
   if not geo.exists():self.skipTest('Current cache not yet generated')
   with self.assertRaisesRegex(ValueError,'Immutable revision'):generate(CONFIG,FLY,geo,out)

class DetailCalloutTests(unittest.TestCase):
 def test_detail_keeps_parent_callout_numbers(self):
  import re
  from work_instructions import svg_view
  geometry=FLY/'output/work-instructions/cache/geometry-current.json'
  if not geometry.exists():self.skipTest('Generate geometry cache first')
  c=read(FLY/'config/work-instructions/pilot-r004.json');o=next(x for x in c['operations'] if x['id']=='s1.P030');d=o['details'][0]
  svg=svg_view(c,read(geometry),dict(id=d['id'],uses=d['uses'],install=[],view=d['view']))
  labels=[int(n) for n in re.findall(r'font-size="11">([0-9]+)</text>',svg)]
  self.assertEqual(labels,[o['uses'].index(i)+1 for i in d['uses']])
