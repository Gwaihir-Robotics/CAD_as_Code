"""Read-only FreeCAD adapter. World-space mesh/BREP fingerprints; never save CAD.
Run with FreeCAD's bundled Python. No process requirements inferred here.
"""
import sys, json, hashlib, argparse
from pathlib import Path
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mesh_record(shape,deflection):
    verts,triangles=shape.tessellate(deflection);b=shape.BoundBox
    return {'points':[list(v) for v in verts],'triangles':triangles,
            'sha256':hashlib.sha256(shape.exportBrepToString().encode()).hexdigest(),
            'bounds':[b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax],
            'volume_mm3':shape.Volume,'solid_count':len(shape.Solids)}

def extract(config, root, out):
    c=json.loads(Path(config).read_text()); src=root/c['cad_source']; before=sha(src)
    doc=App.openDocument(str(src)); result={}
    try:
        for i in c['instances']:
            if 'cad_object' not in i: continue
            o=doc.getObject(i['cad_object'])
            if o is None or not o.Shape.Solids: raise ValueError('Missing solid '+i['id'])
            result[i['id']]=mesh_record(o.Shape.copy(),0.7)
        detail_geometry={};detail_specs={};instances={i['id']:i for i in c['instances']}
        for op in c['operations']:
            for detail in op.get('details',[]):
                if 'crop_box_mm' not in detail['view']: continue
                bounds=detail['view']['crop_box_mm']
                if any(bounds[k]>=bounds[k+3] for k in range(3)): raise ValueError('Invalid crop box')
                box=Part.makeBox(*(bounds[k+3]-bounds[k] for k in range(3)),App.Vector(*bounds[:3]))
                meshes={}
                for iid in detail['uses']:
                    # Clip copies for illustration only; never change or save the document.
                    shape=doc.getObject(instances[iid]['cad_object']).Shape.copy().common(box)
                    if not shape.Solids or not shape.isValid(): raise ValueError('Empty/invalid detail crop '+iid)
                    meshes[iid]=mesh_record(shape,0.05)
                detail_geometry[detail['id']]=meshes
                detail_specs[detail['id']]={'uses':detail['uses'],'crop_box_mm':bounds}
        sections={}
        for op in c['operations']:
            for detail in op.get('details',[]):
                if 'section' not in detail['view']: continue
                plane=detail['view']['section']; paths={}
                for iid in detail['uses']:
                    instance=next(i for i in c['instances'] if i['id']==iid)
                    shape=doc.getObject(instance['cad_object']).Shape
                    paths[iid]=[[list(p) for p in w.discretize(Deflection=0.3)] for w in shape.slice(App.Vector(*plane['normal']),plane['offset_mm'])]
                sections[detail['id']]=paths
        audits=[]
        for i in c['instances']:
            if 'placement' not in i: continue
            p=i['placement']; target=doc.getObject(p['target_object']).Shape
            # Semantic cylinder-axis match; face indices are deliberately not retained.
            matches=[f for f in target.Faces if f.Surface.TypeId=='Part::GeomCylinder'
                     and abs(f.Surface.Axis.x)>.999
                     and abs(f.Surface.Radius-p['target_radius_mm'])<1e-4
                     and abs(f.Surface.Center.y-p['seat_mm'][1])<1e-4
                     and abs(f.Surface.Center.z-p['seat_mm'][2])<1e-4]
            ok=bool(matches)
            if p['verification']=='cad_axis_verified' and not ok: raise ValueError('Hardware axis mismatch '+i['id'])
            audits.append({'instance':i['id'],'axis_matches':len(matches),'verification':p['verification']})
        joints=[]
        tubes=[i for i in c['instances'] if i.get('member')]
        for n,a in enumerate(tubes):
            for b in tubes[n+1:]:
                sa=doc.getObject(a['cad_object']).Shape; sb=doc.getObject(b['cad_object']).Shape
                dist,points,_=sa.distToShape(sb)
                if dist<0.3:
                    p=(points[0][0]+points[0][1])*0.5
                    joints.append({'id':'joint.'+a['id']+'--'+b['id'],'members':[a['id'],b['id']],
                                   'point_mm':list(p),'gap_mm':dist,'requirement':'weld-procedure'})
    finally: App.closeDocument(doc.Name)
    assert before==sha(src),'CAD modified during extraction'
    Path(out).write_text(json.dumps({'schema_version':1,'cad_sha256':before,'freecad_version':App.Version(),
        'mapping_sha256':hashlib.sha256(json.dumps(c['instances'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),'detail_specs':detail_specs,'detail_geometry':detail_geometry,'section_specs':{d['id']:d['view']['section'] for op in c['operations'] for d in op.get('details',[]) if 'section' in d['view']},'sections':sections,'instances':result,'placement_audits':audits,'joints':joints},sort_keys=True))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('config');p.add_argument('root',type=Path);p.add_argument('out');a=p.parse_args()
    extract(a.config,a.root,a.out)
