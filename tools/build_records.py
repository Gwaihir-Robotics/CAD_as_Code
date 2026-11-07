"""Proposed FactoryOS boundary: append-only local SQLite outbox / mock import.
No network endpoints. IDs bind build, operation and evidence to immutable instructions.
"""
import argparse, json, sqlite3, uuid
from pathlib import Path
from work_instructions import read,write,canonical,digest
TYPES={'assembly.operation_started','assembly.operation_completed','assembly.inspection_recorded','assembly.issue_reported','assembly.rework_requested','engineering.issue_evaluated','engineering.revision_issued'}
def connect(path):
    db=sqlite3.connect(path);db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA synchronous=FULL')
    db.executescript('CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY, body TEXT NOT NULL); CREATE TABLE IF NOT EXISTS outbox(id TEXT PRIMARY KEY REFERENCES events(id), attempts INTEGER NOT NULL DEFAULT 0, acknowledged INTEGER NOT NULL DEFAULT 0);');return db

def validate_event(e,definition):
    c=read(definition/'process.json');m=read(definition/'manifest.json')
    required={'schema_version','event_id','event_type','occurred_at_utc','product_id','variant_id','instruction_revision','instruction_sha256','build_id','work_order_id','operation_instance_id','operation_id','actor','payload'}
    if set(e)!=required or e['schema_version']!=1 or e['event_type'] not in TYPES:raise ValueError('Event envelope')
    uuid.UUID(e['event_id'])
    if (e['product_id'],e['variant_id'],e['instruction_revision'],e['instruction_sha256'])!=(c['product'],c['variant'],c['revision'],m['instruction_sha256']):raise ValueError('Pinned definition mismatch')
    ops={o['id']:o for o in c['operations']}
    if e['operation_instance_id']!=e['build_id']+'.'+e['operation_id']:raise ValueError('Operation instance identity')
    if e['operation_id'] not in ops:raise ValueError('Unknown operation')
    o=ops[e['operation_id']];p=e['payload']
    if 'part_instance_id' in p and p['part_instance_id'] not in o['uses']+o['install']:raise ValueError('Unknown part instance for operation')
    if e['event_type']=='assembly.inspection_recorded':
        if p.get('inspection_requirement_id') not in {x['id'] for x in o['checks']} or p.get('disposition') not in {'pending','accepted','rejected'} or not p.get('evidence_id'):raise ValueError('Inspection evidence required')
        if p['disposition']=='accepted' and any(x['acceptance']=='hold_pending_engineering' for x in o['checks'] if x['id']==p['inspection_requirement_id']):raise ValueError('Unapproved requirement cannot be accepted')
    if e['event_type']=='assembly.operation_completed' and 'disposition' in p:raise ValueError('Completion cannot grant acceptance')
    if e['event_type'] in {'assembly.issue_reported','assembly.rework_requested'} and not p.get('issue_id'):raise ValueError('Issue reference required')

def ingest(db,events,definition):
    pins={k:v['instruction_sha256'] for k,v in summary(db).items()}
    for e in events:
        if e['build_id'] in pins and pins[e['build_id']]!=e['instruction_sha256']: raise ValueError('Active build cannot switch instruction revision')
        pins[e['build_id']]=e['instruction_sha256']
    # Validate batch first, then atomically deduplicate; conflicting repeated IDs reject.
    for e in events:validate_event(e,definition)
    with db:
        for e in events:
            body=canonical(e).decode();prior=db.execute('SELECT body FROM events WHERE id=?',(e['event_id'],)).fetchone()
            if prior and prior[0]!=body:raise ValueError('Event ID reused with different content')
            db.execute('INSERT OR IGNORE INTO events VALUES (?,?)',(e['event_id'],body));db.execute('INSERT OR IGNORE INTO outbox(id) VALUES (?)',(e['event_id'],))

def export(db,path):
    with db:
        rows=db.execute('SELECT e.body FROM events e JOIN outbox o ON e.id=o.id WHERE o.acknowledged=0 ORDER BY e.rowid').fetchall()
        write(path,{'schema_version':1,'events':[json.loads(r[0]) for r in rows]})
        db.execute('UPDATE outbox SET attempts=attempts+1 WHERE acknowledged=0')

def acknowledge(db,ids):
    with db:
        for id in ids:
            if not db.execute('SELECT id FROM outbox WHERE id=?',(id,)).fetchone():raise ValueError('Unknown acknowledgement')
            db.execute('UPDATE outbox SET acknowledged=1 WHERE id=?',(id,))

def summary(db):
    result={}
    for (body,) in db.execute('SELECT body FROM events ORDER BY rowid'):
        e=json.loads(body);r=result.setdefault(e['build_id'],{'instruction_sha256':e['instruction_sha256'],'operations':{},'issues':[]})
        if r['instruction_sha256']!=e['instruction_sha256']:raise ValueError('Active build cannot switch instruction revision')
        if e['event_type']=='assembly.operation_completed':r['operations'].setdefault(e['operation_id'],{})['completion']='completed'
        if e['event_type']=='assembly.inspection_recorded':r['operations'].setdefault(e['operation_id'],{})['quality']=e['payload']['disposition']
        if 'issue_id' in e['payload']:r['issues'].append(e['event_id'])
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['import','export','ack','summary']);p.add_argument('--db',type=Path,required=True);p.add_argument('--definition',type=Path);p.add_argument('--file',type=Path);a=p.parse_args();db=connect(a.db)
    if a.command=='import':
        events=read(a.file)['events']; existing=summary(db)
        for e in events:
            if e['build_id'] in existing and e['instruction_sha256']!=existing[e['build_id']]['instruction_sha256']:raise ValueError('Active build is pinned')
        ingest(db,events,a.definition)
    elif a.command=='export':export(db,a.file)
    elif a.command=='ack':acknowledge(db,read(a.file)['event_ids'])
    else:print(json.dumps(summary(db),indent=2))
