"""Construit demo.html : l'application, branchée sur des données fictives au lieu de Supabase, Gmail et Google Agenda."""
import json, pathlib
ici = pathlib.Path(__file__).parent
d = json.load(open(ici / "donnees_demo.json"))
emballe = lambda x: {"result": "<untrusted-data-demo>\n" + json.dumps(x, ensure_ascii=False) + "\n</untrusted-data-demo>"}
simulation = """<meta charset="utf-8"><meta name=viewport content='width=device-width,initial-scale=1'><script>
/* Simulation du runtime claude.ai : connecteurs et base locale, avec des données fictives. */
const FICHES=%s, OFFRES=%s, store={"semaines/2026-10-05":{debut:"2026-10-05",invitations:60,acceptees:24,reponses:6,appels:2}};
const snap=p=>({exists:!!store[p],id:p.split('/').pop(),data:()=>store[p]});
const db={doc:p=>({onSnapshot:f=>{setTimeout(()=>f(snap(p)),20);return()=>{}},set:v=>{store[p]=v;return Promise.resolve()},get:()=>Promise.resolve(snap(p)),delete:()=>Promise.resolve()}),
 collection:c=>{const o={doc:id=>db.doc(c+'/'+id),where:()=>o,orderBy:()=>o,limit:()=>o,onSnapshot:f=>{setTimeout(()=>f({docs:Object.keys(store).filter(k=>k.startsWith(c+'/')).map(snap)}),20);return()=>{}}};return o}};
const mcp={callTool:(s,t,i)=>Promise.resolve(s==='Supabase'?{payload:i.query.includes('from offres')?OFFRES:FICHES}:{payload:{}}),
 watchTool:(s,t,i,h)=>{setTimeout(()=>h({type:'data',result:{payload:s==='Gmail'?{threads:[]}:{events:[]}}}),30);return()=>{}},invalidate:()=>Promise.resolve()};
window.claude={use:n=>Promise.resolve(n==='mcp'?mcp:n==='db'?db:null)};
</script>""" % (json.dumps(emballe(d["fiches"]), ensure_ascii=False), json.dumps(emballe(d["offres"]), ensure_ascii=False))
(ici.parent / "demo.html").write_text(simulation + (ici.parent / "cockpit.html").read_text())
print("demo.html construit")
