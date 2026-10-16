"""Maintained contract implementation; deliberately excluded from downloads."""
import asyncio
from hashlib import sha256
import json
import sqlite3


def repair(case):
    kind = case['kind']
    if kind == 'orders':
        with sqlite3.connect(':memory:') as db:
            db.executescript('CREATE TABLE stock(qty INTEGER); CREATE TABLE orders(tenant TEXT,key TEXT,qty INTEGER, UNIQUE(tenant,key)); CREATE TABLE outbox(tenant TEXT,key TEXT, UNIQUE(tenant,key));')
            db.execute('INSERT INTO stock VALUES (?)', (case['stock'],));db.commit()
            results=[]
            for c in case['commands']:
                if c.get('tenant') != case['principal']:
                    results.append('denied');continue
                if set(c) - {'tenant','key','qty','fail'} or type(c.get('qty')) is not int or c['qty'] <= 0 or not isinstance(c.get('key'),str) or not c['key']:
                    results.append('invalid');continue
                old=db.execute('SELECT qty FROM orders WHERE tenant=? AND key=?',(c['tenant'],c['key'])).fetchone()
                if old:
                    results.append('replayed' if old[0]==c['qty'] else 'conflict');continue
                try:
                    with db:
                        changed=db.execute('UPDATE stock SET qty=qty-? WHERE qty>=?',(c['qty'],c['qty'])).rowcount
                        if not changed:
                            results.append('sold-out');continue
                        db.execute('INSERT INTO orders VALUES (?,?,?)',(c['tenant'],c['key'],c['qty']))
                        if c.get('fail'):
                            raise RuntimeError('modeled crash before outbox')
                        db.execute('INSERT INTO outbox VALUES (?,?)',(c['tenant'],c['key']))
                    results.append('created')
                except RuntimeError:
                    results.append('rolled-back')
            return {'results':results,'stock':db.execute('SELECT qty FROM stock').fetchone()[0],
                    'orders':db.execute('SELECT COUNT(*) FROM orders').fetchone()[0],'outbox':db.execute('SELECT COUNT(*) FROM outbox').fetchone()[0]}
    if kind == 'events':
        seen=set();effects=0;acks=0;retries=0;quarantined=0
        for e in case['events']:
            key=(e['tenant'],e['id']);payload=e['value']
            if e['tenant']!=case['principal']:
                quarantined+=1;continue
            if key in seen:
                acks+=1;continue
            if e.get('invalid'):
                quarantined+=1;continue
            if e.get('transient') and e['attempt']<3:
                retries+=1;continue
            if e.get('transient'):
                quarantined+=1;continue
            seen.add(key);effects+=payload
            if not e.get('lost_ack'):
                acks+=1
        return {'effects':effects,'acks':acks,'retries':retries,'quarantined':quarantined}
    if kind == 'retrieval':
        terms=set(case['query'].lower().split());hits=[]
        for d in case['documents']:
            if d['tenant']!=case['principal'] or not d['allowed'] or not d['current']:
                continue
            overlap=len(terms & set(d['text'].lower().split()))
            if overlap:hits.append((-overlap,d['id'],d['text']))
        hits=sorted(hits)[:case['k']]
        return {'citations':[h[1] for h in hits],'answer':' | '.join(h[2] for h in hits) if hits else 'No authorized support'}
    if kind == 'tool':
        seen={};results=[];ledger=0
        for p in case['proposals']:
            args=p.get('args',{})
            if p.get('name')!='add_expense' or set(args)!={'tenant','cents','category'} or type(args.get('cents')) is not int or args['cents']<=0 or not isinstance(args['category'],str) or not args['category']:
                results.append('invalid');continue
            if args['tenant']!=case['principal']:
                results.append('denied');continue
            digest=sha256(json.dumps(args,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            if p.get('approval')!=digest:
                results.append('unapproved');continue
            key=p['key']
            if key in seen:
                results.append('replayed' if seen[key]==digest else 'conflict');continue
            seen[key]=digest;ledger+=args['cents'];results.append('created')
        return {'results':results,'expense_cents':ledger,'receipts':len(seen)}
    if kind == 'report':
        with sqlite3.connect(':memory:') as db:
            db.executescript('CREATE TABLE orders(tenant TEXT,id INTEGER,cents INTEGER); CREATE TABLE items(tenant TEXT,order_id INTEGER,qty INTEGER);')
            db.executemany('INSERT INTO orders VALUES (?,?,?)',case['orders']);db.executemany('INSERT INTO items VALUES (?,?,?)',case['items']);db.commit()
            selects=[];db.set_trace_callback(lambda sql: selects.append(sql) if sql.lstrip().upper().startswith('SELECT') else None)
            rows=db.execute('SELECT o.id,o.cents,COALESCE(i.qty,0) FROM orders o LEFT JOIN (SELECT tenant,order_id,SUM(qty) qty FROM items GROUP BY tenant,order_id) i ON i.tenant=o.tenant AND i.order_id=o.id WHERE o.tenant=? ORDER BY o.id',(case['principal'],)).fetchall()
            return {'rows':[list(r) for r in rows],'selects':len(selects)}
    if kind == 'cache':
        cache={};results=[]
        for r in case['requests']:
            key=(r['tenant'],r['id'],r['version'])
            if r['tenant']!=case['principal']:
                results.append(None);continue
            if key not in cache:cache[key]=r['text']
            results.append(cache[key])
        return results
    if kind == 'async':
        async def run():
            gate=asyncio.Semaphore(case['limit']);live=0;peak=0
            async def one(job):
                nonlocal live,peak
                async with gate:
                    live+=1;peak=max(peak,live)
                    try:
                        await asyncio.sleep(job['delay'])
                        if job.get('fail'):raise ValueError('fixture')
                        return job['id']
                    finally:live-=1
            tasks=[asyncio.create_task(one(j)) for j in case['jobs']]
            try:
                values=await asyncio.wait_for(asyncio.gather(*tasks,return_exceptions=True),case['timeout'])
                results=['error' if isinstance(v,BaseException) else v for v in values]
            except TimeoutError:
                for task in tasks:task.cancel()
                await asyncio.gather(*tasks,return_exceptions=True)
                results=['timeout']
            return {'results':results,'peak':peak,'live':live}
        return asyncio.run(run())
    raise ValueError('Unknown case kind')
