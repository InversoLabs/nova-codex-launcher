"""Materialize complete references and isolated implementation/repair tasks."""
import argparse
import hashlib
import html
import json
from pathlib import Path
from catalog import PROJECTS

COMMON='''function num(value,min){if(String(value).trim()==='') throw Error('Enter all numeric fields'); const n=Number(value); if(!Number.isFinite(n)||n<min) throw Error('Enter a number of at least '+min); return n;}
function round(n){return Math.round((n+Number.EPSILON)*100)/100;}
function lines(s){return s.split(/\\r?\\n/).map(x=>x.trim()).filter(Boolean);}
function time(s){if(!/^([01]\\d|2[0-3]):[0-5]\\d$/.test(s)) throw Error('Use HH:MM in 24-hour time'); const [h,m]=s.split(':').map(Number); return h*60+m;}
'''
UI='''const form=document.querySelector('form'), result=document.querySelector('#result'), error=document.querySelector('#error');
const storageKey='nova-demo:'+document.body.dataset.project;
const history=document.querySelector('#history');
function label(key){return key.replace(/([A-Z])/g,' $1').replace(/^./,x=>x.toUpperCase());}
function render(value){result.replaceChildren(); for(const [key,text] of Object.entries(value)){const card=document.createElement('div'); card.className='metric'; const dt=document.createElement('dt'),dd=document.createElement('dd'); dt.textContent=label(key); dd.textContent=String(text); dd.dataset.metric=key;card.append(dt,dd);result.append(card);} result.hidden=false;}
function restore(){history.replaceChildren(); try{const saved=JSON.parse(localStorage.getItem(storageKey)||'null'); if(saved){const item=document.createElement('li'); item.textContent=Object.values(saved).join(' · '); history.append(item);}}catch{localStorage.removeItem(storageKey);}}
form.addEventListener('submit',event=>{event.preventDefault(); error.textContent='';result.hidden=true;try{const value=run(Object.fromEntries(new FormData(form)));render(value);if(document.body.dataset.persist==='yes'){localStorage.setItem(storageKey,JSON.stringify(value));restore();}}catch(e){result.replaceChildren();error.textContent=e.message||'Please check your input';}});
document.querySelector('#reset').addEventListener('click',()=>{HTMLFormElement.prototype.reset.call(form);result.replaceChildren();result.hidden=true;error.textContent='';});
document.querySelector('#clear').addEventListener('click',()=>{localStorage.removeItem(storageKey);restore();});
restore();
'''
CSS='''*{box-sizing:border-box} :root{color-scheme:dark;font-family:system-ui,-apple-system,sans-serif;background:#0b101b;color:#edf2ff}body{margin:0;min-height:100vh;background:radial-gradient(ellipse at top right,#242b50,transparent 65%)}a{color:#d0c4ff}header,main,footer{max-width:1040px;margin:auto;padding:24px}header{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #39425b}.brand{font-weight:750;letter-spacing:.13em}.badge{font-size:.8rem;color:#c9d1e5;border:1px solid #566180;border-radius:30px;padding:6px 12px}.intro{padding:35px 0 20px}.eyebrow{color:#b9aaff;text-transform:uppercase;letter-spacing:.16em;font-size:.78rem}h1{font-size:clamp(2rem,7vw,3.8rem);letter-spacing:-.045em;line-height:1.06;margin:12px 0}p{color:#bbc6dc;line-height:1.6;max-width:65ch}.grid{display:grid;grid-template-columns:1.15fr 1fr;gap:24px}.panel{background:#141c2ddd;border:1px solid #36405c;border-radius:20px;padding:26px;box-shadow:0 20px 60px #0003}label{display:block;margin-bottom:18px;font-size:.92rem;color:#e3eaff}input,textarea{display:block;width:100%;margin-top:8px;border:1px solid #617092;background:#0d1422;color:#fff;border-radius:10px;padding:12px;font:inherit}textarea{min-height:125px;resize:vertical}button{border:1px solid transparent;border-radius:10px;padding:12px 18px;font:inherit;font-weight:650;cursor:pointer;background:#c4b5ff;color:#17122b}button.secondary{background:transparent;color:#e5eaff;border-color:#617092}button:hover{filter:brightness(1.1)}:focus-visible{outline:3px solid #82dfff;outline-offset:3px}.actions{display:flex;flex-wrap:wrap;gap:10px}h2{font-size:1.1rem;margin:0 0 18px}.metric{padding:14px 0;border-bottom:1px solid #39435e}dt{color:#bac7de;font-size:.85rem}dd{margin:6px 0 0;font-size:1.45rem;overflow-wrap:anywhere}#error{color:#ffb7bd;line-height:1.5;min-height:1.4em}ul{padding-left:18px;color:#becae0;overflow-wrap:anywhere}footer{font-size:.8rem;color:#9fabc1}@media(max-width:680px){.grid{grid-template-columns:1fr}header,main,footer{padding:18px}.panel{padding:20px}.intro{padding-top:22px}.badge{max-width:130px;text-align:center}}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;animation:none!important;transition:none!important}}
'''

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def render(project):
    fields=[]
    for name,label,kind,value in project['fields']:
        attrs=f'id="{name}" name="{name}"'
        widget=(f'<textarea {attrs}>{html.escape(value)}</textarea>' if kind=='textarea' else
                f'<input {attrs} type="{kind}" step="any" value="{html.escape(value,quote=True)}">')
        fields.append(f'<label for="{name}">{html.escape(label)}{widget}</label>')
    persist=project['id']!='password-meter'
    return {'index.html':f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{project['title']}</title><link rel="stylesheet" href="style.css"><script defer src="logic.js"></script><script defer src="app.js"></script></head>
<body data-project="{project['id']}" data-persist="{'yes' if persist else 'no'}"><header><span class="brand">NOVA / LAB</span><span class="badge">Local browser app</span></header><main><section class="intro"><span class="eyebrow">A little tool for everyday work</span><h1>{project['title']}</h1><p>{html.escape(project['description'])}</p></section><div class="grid"><section class="panel"><h2>Your details</h2><form novalidate>{''.join(fields)}<div class="actions"><button type="submit">Calculate</button><button type="button" class="secondary" id="reset">Reset</button></div><p id="error" role="alert"></p></form></section><section class="panel"><h2>Your result</h2><dl id="result" aria-live="polite" hidden></dl><p>Enter your details, then calculate to see the result.</p><h2>Last result</h2><ul id="history"></ul><button type="button" class="secondary" id="clear">Clear saved result</button></section></div></main><footer>Runs in your browser. {'Only your most recent result is saved on this device.' if persist else 'Password inputs and results are never saved.'} Demonstration project.</footer></body></html>
''','style.css':CSS,'app.js':UI,'logic.js':COMMON+'\nfunction run(d){\n'+project['body']+'\n}\n',
        'README.md':f"# {project['title']}\n\n{project['description']}\n\nOpen index.html in a browser or serve this directory with a local static server. No build, dependencies, accounts, or external assets. Data stays on this device.\n\nThe form validates inputs, calculates a result, supports reset, and {'saves only the last result; Clear saved result removes it' if persist else 'does not store password information'}. Includes keyboard focus and a mobile layout.\n"}

def materialize(out):
    out=Path(out); out.mkdir(parents=True,exist_ok=False)
    manifest={'schema':1,'provenance':'Original assistant-authored reference projects, not generated teacher runs','projects':[]}
    for p in PROJECTS:
        files=render(p); root=out/'references'/p['id']; root.mkdir(parents=True)
        for name,content in files.items(): (root/name).write_text(content,encoding='utf-8')
        assert p['mutation'][0] in files['logic.js'],p['id']
        spec={**p,'reference_hashes':{n:sha(root/n) for n in files},'tasks':[]}
        for variant in ('implement','repair'):
            taskid=p['id']+'--'+variant; work=out/'tasks'/taskid; work.mkdir(parents=True)
            for name,content in files.items():
                if name=='logic.js':
                    content=(COMMON+"\nfunction run(d){throw Error('Calculation is not implemented');}\n" if variant=='implement' else content.replace(*p['mutation']))
                (work/name).write_text(content,encoding='utf-8')
            examples=json.dumps(p['cases'][:1],ensure_ascii=False)
            prompt=(f"Complete this browser application: {p['title']}. {p['description']}\n"
                    "Read README.md, index.html, app.js, and logic.js. "
                    +("Implement the missing run(d) function in logic.js." if variant=='implement' else "Find and repair the calculation defect in logic.js.")+
                    " Keep the existing accessible form and local-only behavior. Numeric inputs must be finite and respect the labels; reject invalid input with a useful error. "
                    "Use the example and project contract in TASK.md. Run the configured browser tests and finish only after seeing their result.")
            task_text=prompt+'\n\nExample input/output:\n'+examples+'\n\n'+CONTRACTS[p['id']]+'\n'
            (work/'TASK.md').write_text(task_text,encoding='utf-8')
            spec['tasks'].append({'id':taskid,'variant':variant,'prompt':prompt,'starter_hashes':{f.name:sha(f) for f in work.iterdir() if f.is_file()}})
        manifest['projects'].append(spec)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    return manifest

CONTRACTS={
'reading-planner':'dailyPages is pages/days rounded UP. Pages >= 0; days >= 1. Return dailyPages and totalPages.',
'event-capacity':'capacity and booked >= 0, group >= 1. Reject booked > capacity. remaining = capacity - booked. admitted is Yes if the whole group fits, including exactly filling the venue; otherwise No.',
'recipe-scaler':'amount >= 0; servings and target >= 0.01. quantity = amount * target / servings; factor = target / servings. Round both to 2 decimals.',
'inventory-alerts':'Rows are name,stock,threshold. Trim whitespace; stock and threshold >= 0. Include equality when selecting low stock. Return reorderCount and comma-space joined items, or None.',
'ticket-pricing':'Adults cost 20, children 12. Nonnegative counts. At least 10 total tickets earns 15% off the entire order. Return tickets, total rounded to 2 decimals, and discountPercent.',
'meeting-overlap':'Strict HH:MM 24-hour values, same day. Reject an end before its start. Return nonnegative overlapMinutes and available (Yes for positive overlap, No otherwise).',
'catalog-search':'Catalog: Canvas Bag 25, Desk Lamp 60, Notebook 12, Travel Mug 25. Trim and lowercase search query; substring match names, maximum price inclusive. Sort ascending price then name. Return matches and comma-space joined products, or None.',
'text-insights':'Words are nonempty whitespace-separated tokens. Characters counts Unicode code points, including whitespace. Reading speed 200 words/minute; round readingMinutes UP, zero for empty text. Return words, characters, readingMinutes.',
'trip-budget':'nights, nightly room price, daily meals, transport >= 0. There is one more day than nights. Return days, lodging (nights * nightly), and total including meals for all days and transport. Money rounded to 2 decimals.',
'color-contrast':'Accept only #RRGGBB (case insensitive). Convert sRGB channels to linear (x <= .04045: x/12.92; otherwise ((x+.055)/1.055)^2.4). Luminance coefficients .2126, .7152, .0722. Ratio (lighter+.05)/(darker+.05). Return ratio rounded to 2 decimals, normalText Pass at raw ratio >=4.5, largeText Pass at >=3; otherwise Fail.',
'priority-board':'Rows title,priority. Valid priorities high,medium,low. Sort in that order, keeping original order for ties. Return count, next (first title or None), and order joined with space-arrow-space ( → ). Reject unknown priorities.',
'shipping-quote':'weight >= .01 kg; subtotal >= 0. Shipping is free for subtotal >=75, otherwise 5 for first kg plus 2 per additional started kg. Return shipping and orderTotal rounded to 2 decimals.',
'quiz-score':'Split comma-separated answers/key, trim, compare case insensitively. Equal lengths and nonempty key entries required. Return correct, total, percent rounded to 2 decimals.',
'work-session':'blocks must be a whole integer >=1; focus >=1; rest >=0. There are blocks-1 breaks. Return focusMinutes, breakMinutes, totalMinutes.',
'duplicate-cleaner':'Ignore blank lines and trim each item. Deduplicate case insensitively; keep first spelling and order. Return unique count, removed count, and comma-space joined items.',
'subscription-budget':'monthly and annual >=0. monthlyEquivalent = monthly + annual/12. yearlyTotal = monthly*12 + annual. Round to 2 decimals.',
'unit-converter':'kilometers >=0. meters = kilometers*1000. miles = kilometers/1.609344. Round to 2 decimals.',
'pagination':'total >=0, size >=1, page >=1, all integers. pages = ceiling(total/size); cap requested page at last page. Empty results: all output values zero. Otherwise return pages, page, first 1-based index, last capped at total.',
'storage-estimate':'count and size >=0; copies >=1. megabytes = count*size*copies. Decimal gigabytes = megabytes/1000. Round to 2 decimals.',
'rsvp-summary':'Each line name,status. Trim; accept status case insensitively as yes/no/pending. Reject unknown status. Return attending, declined, pending, total.',
'date-countdown':'Require real calendar ISO YYYY-MM-DD dates; UTC midnight. days is signed end minus start in calendar days. direction Future for positive, Past for negative, Today for zero.',
'grade-planner':'Rows score,weight. Scores 0..100, weights >=0; total weights must equal 100 (tolerance .0001). average is sum(score*weight)/100 rounded to 2 decimals.',
'password-meter':'length = JavaScript string length. categories counts lowercase, uppercase, digits, and nonalphanumeric/nonwhitespace punctuation present. Score = categories plus 2 if length>=12, else 1 if >=8, else 0. rating Strong at >=6, Moderate at >=4, otherwise Weak. Never save input or results.',
'round-robin':'Trim lines and drop blanks. Reject duplicate team names. Each pair exactly once, input order, excluding self matches. Return teams count, matches count, and schedule joined with semicolon-space (A vs B), or No matches.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args()
    report=materialize(args.out);print(json.dumps({'projects':len(report['projects']),'tasks':sum(len(p['tasks']) for p in report['projects'])}))
