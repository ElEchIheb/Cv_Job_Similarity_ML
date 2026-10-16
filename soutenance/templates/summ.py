import json,sys,io
d=json.load(open('soutenance/templates/design_DAHXP_jZ7rA.json',encoding='utf-8'))
pages=d['design_content']['pages']
seq=[1,2,14,3,6,14,17,15,6,7,9,12,11,17,8,14,9,10,14,18,19,20,21,25,22,23,17,12,17,14,15,14,14,17,14,26,9,10,27,27,27,14,14,17,28,29,30,31]
def fillinfo(fl):
    if not isinstance(fl,dict): return None
    if 'media' in fl:
        m=fl['media']; return ('M' if fl.get('isMediaReplaceable') else 'm')+str(m.get('mediaId') or m.get('type'))
    if 'color' in fl: return str(fl['color'].get('color',fl['color'].get('type')))
def summ(e,depth=0):
    t=e.get('type'); out=[]
    pos=f"{e.get('left',0):.0f},{e.get('top',0):.0f} {e.get('width',0):.0f}x{e.get('height',0):.0f}"
    rot=e.get('rotation',0); info=''
    if t=='text':
        r=e['textRegions']; s=''.join(x['characters'] for x in r).replace('\n','\n')
        f=r[0]['formatting'] if r else {}
        info=f"\"{s[:60]}\" fs={f.get('fontSize',0):.0f} {f.get('color')} {f.get('textAlign')} rg={len(r)}"
    else:
        fills=[fillinfo(p.get('fill')) for p in (e.get('paths') or [])]+[fillinfo(e.get('fill'))]
        tc=e.get('textContents'); tx=''
        if tc:
            s='|'.join(''.join(x['characters'] for x in c.get('textRegions',[])) for c in tc)
            if s.strip('|'): tx=' txt="'+s[:50]+'"'
        info=','.join(f for f in fills if f)+tx
    out.append('  '*depth+f"{t} {e['id'][-5:]} [{pos}{' r'+str(round(rot)) if rot else ''}] {info}")
    for k in ('children','elements'):
        for c in e.get(k,[]) or []: out+=summ(c,depth+1)
    return out
if __name__=='__main__':
    want=set(int(x) for x in sys.argv[1:])
    o=io.open('soutenance/templates/summ.txt','w',encoding='utf-8')
    seen=set()
    for i,(p,l) in enumerate(zip(pages,seq),1):
        if l in seen or (want and l not in want): continue
        seen.add(l)
        o.write(f"=== page {i} L{l} {p['id']}\n")
        for e in p['elements']: o.write('\n'.join(summ(e))+'\n')
    o.close()
