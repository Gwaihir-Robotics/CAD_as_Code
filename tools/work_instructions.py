"""Offline instruction compiler; process JSON is authored in the consumer repo."""
import argparse, collections, hashlib, html, json, math, shutil, sys
from pathlib import Path
import jsonschema
VERSION='0.3.0'
HERE=Path(__file__).resolve().parents[1]
def digest(value): return hashlib.sha256(value).hexdigest()
def canonical(x): return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def read(p): return json.loads(Path(p).read_text())
def write(p,x): Path(p).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def indexed(xs):
    ids=[x['id'] for x in xs]
    if len(ids)!=len(set(ids)): raise ValueError('Duplicate IDs')
    return dict(zip(ids,xs))

def letter_suffix(index):
    """Zero-based location suffix: a..z, aa..az, ba..."""
    result=''
    while index>=0:
        index,remainder=divmod(index,26)
        result=chr(97+remainder)+result
        index-=1
    return result

def callout_groups(c,o):
    """One common part number per bubble; instance suffixes follow authored order."""
    instances=indexed(c['instances']);groups=[];by_part={}
    grouped=c.get('callout_style','per_instance')=='grouped_by_part'
    for position,iid in enumerate(o['uses'],1):
        part=instances[iid]['part']
        if grouped and part in by_part:
            group=by_part[part]
        else:
            number=len(groups)+1 if grouped else o['view'].get('callout_numbers',{}).get(iid,position)
            group={'number':number,'part':part,'instances':[]};groups.append(group);by_part[part]=group
        group['instances'].append({'instance_id':iid})
    for group in groups:
        group['quantity']=len(group['instances'])
        for n,instance in enumerate(group['instances']):
            suffix=letter_suffix(n) if grouped and group['quantity']>1 else ''
            instance['label']=str(group['number'])+suffix
    return groups

def callout_labels(c,o):
    return {i['instance_id']:i['label'] for group in callout_groups(c,o) for i in group['instances']}

def location_range(group):
    labels=[i['label'] for i in group['instances']]
    return labels[0] if len(labels)==1 else labels[0]+' - '+labels[-1]

def cropped_detail_specs(c):
    return {d['id']:{'uses':d['uses'],'crop_box_mm':d['view']['crop_box_mm']}
            for o in c['operations'] for d in o.get('details',[]) if 'crop_box_mm' in d['view']}

def html_callout_key(c,o):
    instances=indexed(c['instances']);parts=indexed(c['parts']);E=html.escape
    groups=callout_groups(c,o)
    rows=[];locations=[]
    for group in groups:
        part=group['part'];number=group['number']
        rows.append(f'<tr data-callout-group="{number}" data-part="{E(part)}" data-quantity="{group["quantity"]}"><td>{number}</td><td><a href="#bom-{E(part)}">{E(parts[part]["title"])}</a><br><code>{E(part)}</code></td><td>{group["quantity"]}</td><td>{E(location_range(group))}</td></tr>')
        for item in group['instances']:
            iid=item['instance_id'];placement=instances[iid].get('placement',{}).get('verification','CAD geometry')
            locations.append(f'<tr><td>{E(item["label"])}</td><td>{E(iid)}</td><td>{E(placement)}</td></tr>')
    return '<h3>Callout key</h3><table><tr><th>Bubble</th><th>Common part</th><th>Qty shown</th><th>Locations</th></tr>'+''.join(rows)+'</table><details><summary>Location IDs and placement checks</summary><table><tr><th>Location</th><th>Installed instance</th><th>Placement</th></tr>'+''.join(locations)+'</table></details>'
def validate(c,root=None,g=None):
    jsonschema.validate(c,read(HERE/'schemas/build-process-v1.json'))
    tables={k:indexed(c[k]) for k in ['sources','parts','instances','datums','packages','operations','requirements']}
    S,P,I,D,W,O,R=[tables[k] for k in tables]
    all_ids=[x for t in tables.values() for x in t]
    if len(all_ids)!=len(set(all_ids)): raise ValueError('IDs must be globally unique')
    def refs(values,table):
        for v in values:
            if v not in table: raise ValueError('Unresolved reference '+v)
    refs([c['cad_source']],{s['path']:s for s in S.values()})
    refs([i['part'] for i in I.values()],P)
    for i in I.values():
        if 'member' in i: refs([i['member']['datum']],D)
        if 'placement' in i:
            refs([i['placement']['datum']],D)
            if P[i['part']]['kind']!='hardware': raise ValueError('Placement on nonhardware')
    consumed=[];seen=set();check_ids=[];detail_ids=[]
    for o in O.values():
        refs(o['prerequisites'],O);refs(o['install']+o['uses'],I);refs(o['holds'],R);refs(o['sources'],S);refs([o['package']],W)
        if any(p not in seen for p in o['prerequisites']): raise ValueError('Cycle or non-topological operation order')
        seen.add(o['id']);consumed+=o['install'];check_ids += [x['id'] for x in o['checks']]
        if not any(o['view']['direction']): raise ValueError('Zero camera direction')
        refs(list(o['view']['offsets_mm']),{i:I[i] for i in o['uses']})
        if c.get('callout_style')=='grouped_by_part' and 'callout_numbers' in o['view']:
            raise ValueError('Grouped callouts cannot use legacy callout_numbers')
        for detail in o.get('details',[]):
            detail_ids.append(detail['id'])
            refs(detail['uses'],I)
            if len(detail['uses'])!=len(set(detail['uses'])): raise ValueError('Duplicate detail instance')
            refs(list(detail['view']['offsets_mm']),{i:I[i] for i in detail['uses']})
            if not any(detail['view']['direction']): raise ValueError('Zero detail camera direction')
            if c.get('callout_style')=='grouped_by_part':
                refs(detail['uses'],{i:I[i] for i in o['uses']})
                if 'callout_numbers' in detail['view']: raise ValueError('Grouped details use the parent callout key')
            if 'crop_box_mm' in detail['view']:
                bounds=detail['view']['crop_box_mm']
                if any(bounds[k]>=bounds[k+3] for k in range(3)): raise ValueError('Invalid detail crop bounds')
                if any('cad_object' not in I[i] for i in detail['uses']): raise ValueError('Cropped details require CAD solids')
            refs(list(detail['view'].get('callout_numbers',{})),{i:I[i] for i in detail['uses']})
            if len(set(detail['view'].get('callout_numbers',{}).values()))!=len(detail['view'].get('callout_numbers',{})): raise ValueError('Duplicate detail callout number')
            if 'section' in detail['view'] and not any(detail['view']['section']['normal']): raise ValueError('Zero section normal')
        if len(o['uses'])!=len(set(o['uses'])): raise ValueError('Duplicate callout instance')
    if len(check_ids)!=len(set(check_ids)): raise ValueError('Duplicate inspection IDs')
    if len(detail_ids)!=len(set(detail_ids)): raise ValueError('Duplicate detail IDs')
    if len(consumed)!=len(set(consumed)): raise ValueError('Double-counted installed instance')
    refs([r['source'] for r in R.values()],S)
    b={x['part']:x for x in c['bom']}
    if len(b)!=len(c['bom']) or set(b)!=set(P): raise ValueError('BOM part coverage')
    actual=collections.Counter(i['part'] for i in I.values())
    for p,row in b.items():
        if row['quantity']!=actual[p]: raise ValueError('BOM quantity '+p)
        for i in I.values():
            if i['part']==p and (i['id'] in consumed)==row['reference_only']: raise ValueError('Install coverage '+i['id'])
    for p in P.values():
        if p['kind']=='hardware' and ('spec' not in p or any('placement' not in i for i in I.values() if i['part']==p['id'])): raise ValueError('Hardware specification/placement missing')
    for pkg in W.values():
        if pkg['status']=='released':
            if c['status']!='released': raise ValueError('Package release disagrees with definition')
            for o in O.values():
                if o['package']==pkg['id'] and any(R[r]['mandatory'] and R[r]['status']!='resolved' for r in o['holds']): raise ValueError('Mandatory hold blocks release')
            used={i for o in O.values() if o['package']==pkg['id'] for i in o['uses']}
            if any(I[i].get('placement',{}).get('verification','cad_axis_verified')!='cad_axis_verified' for i in used): raise ValueError('Incomplete hardware blocks release')
            if not pkg.get('reviewed_by'): raise ValueError('Release requires reviewer')
    if root:
        for s in S.values():
            p=(root/s['path']).resolve()
            if not p.is_relative_to(root.resolve()): raise ValueError('Source escapes root')
            if digest(p.read_bytes())!=s['sha256']: raise ValueError('Stale source hash '+s['id'])
        hardware_source=next((s for s in S.values() if s['id']=='hardware'),None)
        if hardware_source:
            hardware=read(root/hardware_source['path'])
            for part in P.values():
                if part['kind']=='hardware' and not part['id'].endswith('washer'):
                    spec=part['spec']; row=next((r for r in hardware['screw_rows'] if r['id']==spec['role']),None)
                    if not row or row['size']!='M'+str(int(spec['diameter_mm'])) or row['length_mm']!=spec['length_mm'] or actual[part['id']]>row['quantity']: raise ValueError('Hardware BOM specification/quantity mismatch '+part['id'])
    if g:
        expected_details=cropped_detail_specs(c)
        if g.get('detail_specs',{})!=expected_details: raise ValueError('Stale cropped detail geometry')
        if set(g.get('detail_geometry',{}))!=set(expected_details): raise ValueError('Missing cropped detail geometry')
        for did,spec in expected_details.items():
            if set(g['detail_geometry'][did])!=set(spec['uses']): raise ValueError('Cropped detail instance coverage')
        expected_sections={d['id']:d['view']['section'] for o in c['operations'] for d in o.get('details',[]) if 'section' in d['view']}
        if g.get('section_specs')!=expected_sections: raise ValueError('Stale section plane cache')
        if g['cad_sha256']!=next(s['sha256'] for s in S.values() if s['path']==c['cad_source']): raise ValueError('Stale geometry')
        if set(g['instances'])!={i['id'] for i in I.values() if 'cad_object' in i}: raise ValueError('Geometry coverage')
        if g.get('mapping_sha256')!=digest(canonical(c['instances'])): raise ValueError('Stale geometry mapping/placements')
        audits={a['instance']:a for a in g['placement_audits']}
        for i in I.values():
            if 'placement' in i:
                if audits.get(i['id'],{}).get('verification')!=i['placement']['verification']: raise ValueError('Missing placement audit')
                if i['placement']['verification']=='cad_axis_verified' and not audits[i['id']]['axis_matches']: raise ValueError('Unverified fastener')
    return tables

def impact(old,new,oldg,newg):
    changed_sources={s['id'] for s in new['sources'] if s not in old['sources']}
    a=indexed(old['instances']); b=indexed(new['instances']);pa=indexed(old['parts']);pb=indexed(new['parts'])
    changed={i for i in a.keys()|b.keys() if a.get(i)!=b.get(i) or pa.get(a.get(i,{}).get('part'))!=pb.get(b.get(i,{}).get('part')) or oldg['instances'].get(i,{}).get('sha256')!=newg['instances'].get(i,{}).get('sha256')}
    oldops=indexed(old['operations']); affected=set()
    global_change=any(old.get(k)!=new.get(k) for k in ['datums','requirements','baseline','packages','callout_style'])
    # Non-CAD source changes conservatively affect all: no false precision about interfaces.
    broad=bool(changed_sources-{'cad','cad-manifest'})
    for o in new['operations']:
        if global_change or broad or oldops.get(o['id'])!=o or changed.intersection(o['uses']+o['install']) or changed_sources.intersection(o['sources']): affected.add(o['id'])
    while True:
        more={o['id'] for o in new['operations'] if affected.intersection(o['prerequisites'])}
        if more<=affected: break
        affected |= more
    return {'changed_instances':sorted(changed),'changed_sources':sorted(changed_sources),'needs_review':sorted(affected),'status':'needs_review' if affected else 'unchanged'}

def norm(v):
    length=math.sqrt(sum(x*x for x in v));return [x/(length or 1) for x in v]
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def dot(a,b):return sum(x*y for x,y in zip(a,b))

# Keep context visibly solid on white paper; use lighting and feature edges to
# show form instead of washing the whole model out. Colors are shared by SVG/PDF.
MATERIALS={
    'context': {'base':(153,168,184), 'edge':'#344657'},
    'current': {'base':(35,139,190), 'edge':'#123e59'},
    'hardware': {'base':(238,164,45), 'edge':'#724715'},
}
LIGHT=norm([-.4,-.6,1.])

def surface_color(material,normal):
    # Mesh winding can differ between imported solids. Orient the lighting
    # normal toward the viewer without changing geometry or face visibility.
    normal=[-v for v in normal] if normal[2]<0 else normal
    shade=.55+.45*max(0.,dot(normal,LIGHT))
    return '#'+''.join('%02x'%round(v*shade) for v in MATERIALS[material]['base'])

def technical_mesh(shape,points,xy,material):
    """Depth-sorted shaded triangles with boundary, crease and silhouette edges.

    Weld coincident tessellation vertices for adjacency so CAD face seams do not
    turn every triangle into a wireframe. Attach lines to their owning surface
    rather than drawing all hidden edges over the completed model. Closed CAD
    solids suppress unmatched tessellation seams; open meshes retain boundaries.
    """
    vertices=[tuple(round(v,6) for v in p) for p in shape['points']]
    faces=[];edges=collections.defaultdict(list)
    for t in shape['triangles']:
        vs=[points[k] for k in t]
        normal=norm(cross([vs[1][k]-vs[0][k] for k in range(3)],
                          [vs[2][k]-vs[0][k] for k in range(3)]))
        if not any(normal): continue
        n=len(faces);depth=sum(v[2] for v in vs)/3
        faces.append((t,normal,depth))
        for a,b in zip(t,(t[1],t[2],t[0])):
            if vertices[a]!=vertices[b]:
                edges[tuple(sorted((vertices[a],vertices[b])))].append((n,a,b))
    outlines=collections.defaultdict(list)
    crease_cos=math.cos(math.radians(25))
    for adjacent in edges.values():
        normals=[faces[n][1] for n,_,_ in adjacent]
        boundary=len(adjacent)==1 and not shape.get('solid_count',1)
        crease=any(abs(dot(normals[0],v))<crease_cos for v in normals[1:])
        silhouette=min(v[2] for v in normals)<0<max(v[2] for v in normals)
        if boundary or crease or silhouette:
            n,a,b=max(adjacent,key=lambda entry:faces[entry[0]][2])
            p,q=xy(points[a]),xy(points[b])
            outlines[n].append('M %.2f %.2f L %.2f %.2f'%(*p,*q))
    result=[]
    for n,(t,normal,depth) in enumerate(faces):
        polygon='<polygon points="'+' '.join('%.2f,%.2f'%tuple(xy(points[k])) for k in t)+'" fill="'+surface_color(material,normal)+'"/>'
        if outlines[n]:
            polygon+='<path class="model-edge" d="'+' '.join(outlines[n])+'" fill="none" stroke="'+MATERIALS[material]['edge']+'" stroke-width="0.85" stroke-linejoin="round"/>'
        result.append((depth,polygon))
    return result

def mesh_hardware(i,p):
    # Explicit shank, head and washer solids as polygonal technical envelopes.
    spec=p['spec']; seat=i['placement']['seat_mm']; d=spec['diameter_mm']; length=spec['length_mm']
    rings=[(0,d/2),(0,spec['head_diameter_mm']/2),(length,spec['head_diameter_mm']/2),(length,d/2),(0,d/2)] if p['id'].endswith('washer') else [(-spec['head_height_mm'],spec['head_diameter_mm']/2),(0,spec['head_diameter_mm']/2),(0,d/2),(length,d/2)]
    pts=[[seat[0]+x,seat[1]+r*math.cos(k*math.pi/8),seat[2]+r*math.sin(k*math.pi/8)] for x,r in rings for k in range(16)]
    ts=[]
    for n in range(len(rings)-1):
        for k in range(16):
            a=n*16+k;b=n*16+(k+1)%16;c=b+16;e=a+16;ts.extend([(a,b,c),(a,c,e)])
    for k in range(1,15):ts.extend([(0,k+1,k),((len(rings)-1)*16,(len(rings)-1)*16+k,(len(rings)-1)*16+k+1)])
    return {'points':pts,'triangles':ts,'bounds':[seat[0]-6,seat[1]-6,seat[2]-6,seat[0]+length,seat[1]+6,seat[2]+6]}

def svg_view(c,g,o,joints=False,labels=None):
    I=indexed(c['instances']);P=indexed(c['parts']);direction=norm(o['view']['direction']);right=norm(cross([0,0,1] if abs(direction[2])<.99 else [0,1,0],direction));up=cross(direction,right)
    labels=callout_labels(c,o) if labels is None else labels
    def project(p):return [dot(p,right),-dot(p,up),dot(p,direction)]
    items=[];cloud=[]
    for id in o['uses']:
        i=I[id];shape=(g['detail_geometry'][o['id']][id] if 'crop_box_mm' in o['view'] else g['instances'].get(id)) or mesh_hardware(i,P[i['part']]);off=o['view']['offsets_mm'].get(id,[0,0,0]);pts=[project([v[k]+off[k] for k in range(3)]) for v in shape['points']];cloud+=pts
        items.append((id,shape,pts,off))
    xmin=min(p[0] for p in cloud);xmax=max(p[0] for p in cloud);ymin=min(p[1] for p in cloud);ymax=max(p[1] for p in cloud)
    scale=min(700/max(xmax-xmin,1),440/max(ymax-ymin,1))
    def xy(p):return [180+(p[0]-xmin)*scale,65+(p[1]-ymin)*scale]
    triangles=[];calls=[];arrows=[]
    centers={id:xy(project([(shape['bounds'][k]+shape['bounds'][k+3])/2+off[k] for k in range(3)])) for id,shape,pts,off in items}
    slots={}
    for side in [0,1]:
        group=sorted([id for id in centers if (centers[id][0]>530)==bool(side)],key=lambda id:centers[id][1])
        for row,id in enumerate(group):slots[id]=(985 if side else 45,70+row*min(38,420/max(1,len(group)-1)))
    for n,(id,s,pts,off) in enumerate(items,1):
        number=labels[id];current=id in o['install'];hardware=P[I[id]['part']]['kind']=='hardware'
        material='hardware' if hardware else ('current' if current else 'context')
        triangles.extend(technical_mesh(s,pts,xy,material))
        b=s['bounds'];center=[(b[k]+b[k+3])/2+off[k] for k in range(3)];q=xy(project(center)); side=n%2;line=n//2
        lx,ly=slots[id]
        radius=max(11,4*len(number)+5)
        if not o.get('no_callouts'): calls.append(f'<path d="M {q[0]:.1f} {q[1]:.1f} L {lx} {ly}" fill="none" stroke="#45576a" stroke-width="1"/><circle cx="{lx}" cy="{ly}" r="{radius}" fill="white" stroke="#164563"/><text x="{lx}" y="{ly+4}" text-anchor="middle" font-size="11">{number}</text>')
        if any(off):
            dest=xy(project([(b[k]+b[k+3])/2 for k in range(3)])); unit=norm([dest[0]-q[0],dest[1]-q[1]]);head=[dest,[dest[0]-8*unit[0]+4*unit[1],dest[1]-8*unit[1]-4*unit[0]],[dest[0]-8*unit[0]-4*unit[1],dest[1]-8*unit[1]+4*unit[0]]];arrows.append('<polygon points="'+' '.join('%.2f,%.2f'%tuple(x) for x in head)+'" fill="#126d9b"/>');arrows.append(f'<path d="M {q[0]} {q[1]} L {dest[0]} {dest[1]}" stroke="#126d9b" stroke-width="2" stroke-dasharray="6 4" fill="none"/><circle cx="{dest[0]}" cy="{dest[1]}" r="3" fill="#126d9b"/>')
    if joints:
        marks=[(n,xy(project(j['point_mm']))) for n,j in enumerate(g['joints'],1)]
        for side in [0,1]:
            group=sorted([(n,q) for n,q in marks if (q[0]>530)==bool(side)],key=lambda nq:nq[1][1])
            for row,(n,q) in enumerate(group):
                lx=990 if side else 24;ly=60+row*min(25,450/max(1,len(group)-1))
                calls.append(f'<path d="M {q[0]} {q[1]} L {lx} {ly}" stroke="#a52020" stroke-width="0.8"/><circle cx="{q[0]}" cy="{q[1]}" r="4" fill="#bd352b"/><text x="{lx-5}" y="{ly-3}" font-size="12" fill="#a52020">J{n:02}</text>')
    sb=100 if scale<1 else 20
    triad=[]
    for label,v,color in [('X',[1,0,0],'#a33325'),('Y',[0,1,0],'#287a3c'),('Z',[0,0,1],'#235c9d')]:
        q=project(v);ex=920+q[0]*30;ey=545+q[1]*30;triad.append(f'<path d="M 920 545 L {ex} {ey}" stroke="{color}" stroke-width="2"/><text x="{ex+3}" y="{ey}" font-size="11">+{label}</text>')
    if 'section' in o['view']:
        triangles=[];arrows=[];calls=[]
        for id,lines in g['sections'][o['id']].items():
            for line in lines:
                pts=[xy(project(v)) for v in line]
                calls.append('<polyline points="'+' '.join('%.2f,%.2f'%tuple(p) for p in pts)+'" fill="none" stroke="#143d57" stroke-width="2"/>')
    return '<svg xmlns="http://www.w3.org/2000/svg" width="1040" height="600" viewBox="0 0 1040 600"><rect width="1040" height="600" fill="#fff"/>'+''.join(x[1] for x in sorted(triangles))+''.join(arrows)+''.join(calls)+''.join(triad)+f'<path d="M 70 550 h {sb*scale}" stroke="#183c52" stroke-width="3"/><text x="70" y="573" font-size="13">{sb} mm (view scale)</text><text x="400" y="570" font-size="13">Blue: current | grey: prior/context | amber: hardware</text></svg>'

def generate(config,root,geometry,out,previous=None):
    c=read(config);g=read(geometry);tables=validate(c,root,g);S,P,I,D,W,O,R=[tables[k] for k in tables]
    source_hashes={s['id']:s['sha256'] for s in c['sources']}
    generator_hashes={p.name:digest(p.read_bytes()) for p in [Path(__file__),HERE/'tools/instruction_geometry.py',HERE/'schemas/build-process-v1.json',HERE/'tools/build_records.py',HERE/'requirements-instructions.txt']}
    identity=digest(canonical({'process':c,'geometry':digest(Path(geometry).read_bytes()),'generators':generator_hashes}))
    final_target=out/c['revision']; target=final_target
    if target.exists():
        if read(target/'manifest.json')['instruction_sha256']==identity:return target
        raise ValueError('Immutable revision exists with different content; allocate a new revision')
    review=impact(read(previous/'process.json'),c,read(previous/'geometry.json'),g) if previous else {'status':'initial_draft','needs_review':list(O)}
    if previous:
        old_generators=read(previous/'manifest.json')['generator_sha256']
        changed_generators=sorted(k for k in generator_hashes if old_generators.get(k)!=generator_hashes[k])
        if changed_generators:
            review.update(changed_generators=changed_generators,needs_review=list(O),status='needs_review')
    if previous and review['needs_review'] and any(p['status']=='released' for p in c['packages']): raise ValueError('Changed instructions require review before release')
    target=out/('.'+c['revision']+'.staging')
    if target.exists(): shutil.rmtree(target)
    target.mkdir(parents=True);(target/'figures').mkdir();write(target/'process.json',c);shutil.copyfile(geometry,target/'geometry.json');write(target/'bom.json',c['bom']);write(target/'review-impact.json',review)
    (target/'generators').mkdir()
    for filename in generator_hashes:
        source=next(p for p in [Path(__file__),HERE/'tools/instruction_geometry.py',HERE/'schemas/build-process-v1.json',HERE/'tools/build_records.py',HERE/'requirements-instructions.txt'] if p.name==filename)
        shutil.copyfile(source,target/'generators'/filename)
    # Retain exact input content, including dirty worktree bytes.
    for s in c['sources']:
        p=target/'sources'/s['path'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/s['path'],p)
    write(target/'callouts.json',{'schema_version':1,'style':c.get('callout_style','per_instance'),
        'operations':{o['id']:{'groups':callout_groups(c,o),
            'details':{d['id']:{iid:callout_labels(c,o)[iid] for iid in d['uses']}
                       for d in o.get('details',[]) if c.get('callout_style')=='grouped_by_part'}} for o in O.values()}})
    E=html.escape
    style='''body{font:16px system-ui;color:#173347;margin:0;background:#eef2f4}nav{padding:18px;background:#14384d;color:white;position:sticky;top:0}a{color:#127099}nav a{color:white;margin-right:14px}main{max-width:1120px;margin:auto;padding:24px}section{background:white;padding:28px;margin:24px 0;border-radius:8px}img{width:100%;height:auto}.hold{background:#fff1d8;padding:12px;border-left:5px solid #b86100}table{border-collapse:collapse;width:100%;font-size:13px}td,th{padding:7px;border-bottom:1px solid #ddd;text-align:left}code{font-size:13px}h1{font-size:32px}h2{color:#164d69}@media print{nav{display:none}section{break-before:page;margin:0;padding:0}body{background:white}}'''
    body=f'<nav><b>FLY / {E(c["revision"])} / DRAFT</b> '+''.join(f'<a href="#{E(o["id"])}">{E(o["id"])}</a>' for o in O.values())+'<a href="#bom">BOM</a></nav><main>'
    body+=f'<section><h1>Two-station fly winder</h1><h2>Illustrated assembly and fabrication pilot</h2><p>{E(c["baseline"])}</p><p class="hold">DRAFT - Engineering review required. Mandatory holds prevent release. This is not an approved fabrication procedure.</p><p>Instruction digest: <code>{identity}</code></p><p>Leaf-instance BOM scope: {E(c["bom_scope"])}</p><p>Offline guide; no progress checkboxes or durable browser records. Use separate pinned build records and explicit event exports.</p></section>'
    pdf_ops=[]
    overview={'no_callouts':True,'uses':list(g['instances']),'install':[],'view':{'direction':[1,-1,.75],'offsets_mm':{}}}
    svg=svg_view(c,g,overview);(target/'figures/overview.svg').write_text(svg)
    body+='<section><h2>Figure 0 - Assembled orientation</h2><a href="figures/overview.svg"><img src="figures/overview.svg" alt="Assembled orientation"/></a><p>Unshown machine parts are outside this pilot. +Z up, +X transfer, +Y station direction. Shared front mount is context.</p></section>'
    for n,o in enumerate(O.values(),1):
        fig=f'figures/{n:02}-{o["id"]}.svg';(target/fig).write_text(svg_view(c,g,dict(o,no_callouts=o['id']=='F020'),o['id']=='F020'))
        req=[R[r]['text'] for r in o['holds']]; counts=collections.Counter(I[i]['part'] for i in o['install'])
        materials=', '.join(f'{v} x {P[k]["title"]}' for k,v in counts.items()) or 'No additional installed parts'
        body+=f'<section id="{E(o["id"])}"><h2>{E(o["id"])} - {E(o["title"])}</h2><p>Package {E(o["package"])} | {E(o["kind"])} | Prerequisites: {E(", ".join(o["prerequisites"]) or "none")}</p><p><b>Start:</b> {E(o["starting_condition"])}</p><p><b>Parts/hardware:</b> {E(materials)}</p><p><b>Tools:</b> {E(", ".join(o["tools"]))}</p><p><b>Consumables:</b> {E(" ".join(o["consumables"]))}</p><a href="{fig}"><img src="{fig}" alt="Figure {n}: {E(o["title"])}"/></a><p>Figure {n}. {E(o["view"]["caption"])} Dashed lines point from exploded position to installed alignment dot. Hardware uses nominal dimensional envelopes; threads and sockets omitted. M4 installation remains incomplete. Click image to enlarge.</p><ol>'+''.join('<li>'+E(t)+'</li>' for t in o['instructions'])+'</ol><h3>Completion / inspection</h3><ul>'+''.join(f'<li>{E(x["id"])}: {E(x["text"])} [{E(x["acceptance"])}]</li>' for x in o['checks'])+'</ul>'+''.join('<p class="hold">HOLD: '+E(t)+'</p>' for t in req)
        body+=html_callout_key(c,o)+'</section>'
        details=[]
        for letter,detail in zip('ABCDEFGHIJKLMNOPQRSTUVWXYZ',o.get('details',[])):
            dp=f'figures/{n:02}-{letter}.svg'
            labels=callout_labels(c,o) if c.get('callout_style')=='grouped_by_part' else None
            (target/dp).write_text(svg_view(c,g,dict(id=detail['id'],uses=detail['uses'],install=[],view=detail['view']),labels=labels))
            body+=f'<section><h3>Figure {n}{letter} - {E(detail["id"])}</h3><a href="{dp}"><img src="{dp}" alt="Detail {E(detail["id"])}"/></a><p>{E(detail["view"]["caption"])}</p></section>'
            details.append((str(n)+letter,dp,detail['view']['caption']))
        pdf_ops.append((n,o,fig,materials,req,details))
    body+='<section id="bom"><h2>Pilot leaf BOM and frame members</h2><table><tr><th>Part</th><th>Description</th><th>Qty</th><th>Scope</th></tr>'+''.join(f'<tr id="bom-{E(b["part"])}"><td>{E(b["part"])}</td><td>{E(P[b["part"]]["title"])}</td><td>{b["quantity"]}</td><td>{"reference only" if b["reference_only"] else "installed leaf"}</td></tr>' for b in c['bom'])+'</table><h3>Member identification</h3><table>'+''.join(f'<tr><td>{E(i["id"])}</td><td>{i["member"]["length_mm"]} mm</td><td>along {i["member"]["orientation"]}; {E(i["member"]["datum"])}</td></tr>' for i in I.values() if 'member' in i)+'</table><h3>Joint locations (not weld requirements)</h3><table>'+''.join(f'<tr><td>J{n:02}</td><td>{E(j["id"])}</td><td>{", ".join(f"{v:.2f}" for v in j["point_mm"])} mm</td></tr>' for n,j in enumerate(g['joints'],1))+'</table></section></main>'
    (target/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Fly winder work instructions</title><style>'+style+'</style>'+body+'</html>')
    make_pdf(target,c,pdf_ops,P,I,g,identity)
    write(target/'manifest.json',{'schema_version':1,'generator_version':VERSION,'generator_sha256':generator_hashes,'instruction_sha256':identity,'process_sha256':digest(canonical(c)),'source_sha256':source_hashes,'freecad_version':g['freecad_version'],'review':review,'status':c['status'],'outputs_sha256':{str(p.relative_to(target)):digest(p.read_bytes()) for p in target.rglob('*') if p.is_file()}})
    target.rename(final_target)
    return final_target

def make_pdf(target,c,ops,P,I,g,identity):
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle,KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from svglib.svglib import svg2rlg
    styles=getSampleStyleSheet();styles['BodyText'].fontSize=9;styles['BodyText'].leading=12
    story=[]
    def p(s,style='BodyText',bold=False):
        text=html.escape(s);story.append(Paragraph('<b>'+text+'</b>' if bold else text,styles[style]));story.append(Spacer(1,6))
    def fig(path):
        d=svg2rlg(str(target/path));d.scale(510/d.width,510/d.width);d.width=510;d.height=294;story.append(d)
    p('Fly winder / illustrated work instructions','Title');p(c['revision']+' - DRAFT / NOT RELEASED','Heading1');p(c['baseline']);p('Mandatory holds prevent fabrication release. Geometry validity is not process approval.');p('Instruction digest: '+identity);fig('figures/overview.svg');p('Figure 0 - assembled orientation; +Z up, +X transfer, +Y across stations.');p(c['bom_scope']);p('No browser progress records. Build execution and inspection acceptance remain separate.');story.append(PageBreak())
    for n,o,path,materials,req,details in ops:
        p(o['id']+' - '+o['title'],'Heading1');p('Package: '+o['package']+' | Prerequisites: '+(', '.join(o['prerequisites']) or 'none'));p('Start: '+o['starting_condition']);p('Parts: '+materials);p('Tools: '+', '.join(o['tools'])+' | Consumables: '+' '.join(o['consumables']));fig(path);p('Figure '+str(n)+' - '+o['view']['caption'])
        for t in o['instructions']:p(t)
        for x in o['checks']:p(x['id']+': '+x['text']+' ['+x['acceptance']+']')
        for t in req:p('HOLD: '+t)
        story.append(PageBreak());p(o['id']+' / Figure '+str(n)+' callout key','Heading2')
        for group in callout_groups(c,o):
            p(str(group['number'])+' | '+str(group['quantity'])+' x '+P[group['part']]['title']+' | locations '+location_range(group),bold=True)
            for item in group['instances']:
                iid=item['instance_id'];p(item['label']+' | '+iid+' | '+I[iid].get('placement',{}).get('verification','CAD geometry'))
        story.append(PageBreak())
        for number,path,caption in details:
            p('Figure '+number+' - Detail','Heading2');fig(path);p(caption);story.append(PageBreak())
    p('Pilot BOM','Heading1')
    for b in c['bom']:p(str(b['quantity'])+' x '+b['part']+' - '+P[b['part']]['title']+(' (reference only)' if b['reference_only'] else ''))
    story.append(PageBreak());p('Frame members / datum cell.origin','Heading1')
    for i in I.values():
        if 'member' in i:p(i['id']+': '+str(i['member']['length_mm'])+' mm; along '+i['member']['orientation'])
    story.append(PageBreak());p('Joint-location key / Figure 2','Heading1')
    for n,j in enumerate(g['joints'],1):p('J%02d'%n+' | '+' / '.join(j['members'])+' | XYZ '+', '.join('%.2f'%v for v in j['point_mm'])+' mm')
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.drawString(40,24,c['revision']+' / DRAFT - engineering holds apply');canvas.drawRightString(570,24,str(doc.page))
    while story and isinstance(story[-1],(Spacer,PageBreak)): story.pop()
    SimpleDocTemplate(str(target/'work-instructions.pdf'),pagesize=(612,792),rightMargin=40,leftMargin=40,topMargin=35,bottomMargin=40).build(story,onFirstPage=footer,onLaterPages=footer)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('config',type=Path);p.add_argument('--root',type=Path,required=True);p.add_argument('--geometry',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--previous',type=Path);a=p.parse_args()
    try: print(generate(a.config,a.root,a.geometry,a.out,a.previous))
    except (ValueError,jsonschema.ValidationError) as e:sys.exit(str(e))
