"""Deliberately broken offline application core. Read CONTRACT.md before editing."""
import sqlite3

def repair(case):
    if case['kind'] == 'orders':
        # Deliberate faults: autocommit separates reservation/order/intent,
        # no scope, constraint, conditional reservation or retry receipt.
        with sqlite3.connect(':memory:', isolation_level=None) as db:
            db.executescript('CREATE TABLE stock(qty INTEGER); CREATE TABLE orders(tenant TEXT,key TEXT,qty INTEGER); CREATE TABLE outbox(tenant TEXT,key TEXT);')
            db.execute('INSERT INTO stock VALUES (?)', (case['stock'],))
            results = []
            for command in case['commands']:
                old = db.execute('SELECT qty FROM stock').fetchone()[0]
                db.execute('UPDATE stock SET qty=?', (old-command['qty'],))
                db.execute('INSERT INTO orders VALUES (?,?,?)', (command['tenant'],command['key'],command['qty']))
                # fail=True still leaves these committed writes behind.
                results.append('created')
            return {'results': results, 'stock': db.execute('SELECT qty FROM stock').fetchone()[0],
                    'orders': db.execute('SELECT COUNT(*) FROM orders').fetchone()[0], 'outbox': 0}
    if case['kind'] == 'events':
        return {'effects': sum(e['value'] for e in case['events']), 'acks': len(case['events']), 'retries': 0, 'quarantined': 0}
    if case['kind'] == 'retrieval':
        docs = case['documents'][:case['k']]  # ignores permissions, versions and relevance
        return {'citations': [d['id'] for d in docs], 'answer': ' | '.join(d['text'] for d in docs)}
    if case['kind'] == 'tool':
        return {'results': ['created'] * len(case['proposals']), 'expense_cents': sum(p['args']['cents'] for p in case['proposals']), 'receipts': len(case['proposals'])}
    if case['kind'] == 'report':
        # Actual N+1 queries and incomplete item key, not a guessed count.
        with sqlite3.connect(':memory:') as db:
            db.executescript('CREATE TABLE orders(tenant TEXT,id INTEGER,cents INTEGER); CREATE TABLE items(tenant TEXT,order_id INTEGER,qty INTEGER);')
            db.executemany('INSERT INTO orders VALUES (?,?,?)',case['orders'])
            db.executemany('INSERT INTO items VALUES (?,?,?)',case['items'])
            selects=[]
            db.set_trace_callback(lambda sql: selects.append(sql) if sql.lstrip().upper().startswith('SELECT') else None)
            orders=db.execute('SELECT id,cents FROM orders WHERE tenant=? ORDER BY id',(case['principal'],)).fetchall()
            rows=[]
            for id,cents in orders:
                qty=db.execute('SELECT COALESCE(SUM(qty),0) FROM items WHERE order_id=?',(id,)).fetchone()[0]
                rows.append([id,cents,qty])
            return {'rows':rows,'selects':len(selects)}
    if case['kind'] == 'cache':
        cache = {}
        return [cache.setdefault(r['id'], r['text']) for r in case['requests']]
    if case['kind'] == 'async':
        return {'results': [j['id'] for j in case['jobs']], 'peak': len(case['jobs']), 'live': len(case['jobs'])}
    raise ValueError('Unknown case kind')
