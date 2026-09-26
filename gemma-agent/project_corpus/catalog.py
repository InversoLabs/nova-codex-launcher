"""Original, small browser applications. References are not teacher trajectories."""
PROJECTS=[]
def app(id,title,description,fields,body,cases,mutation,split='train'):
    PROJECTS.append(dict(id=id,title=title,description=description,fields=fields,body=body,cases=cases,mutation=mutation,split=split))

# Fields: name, label, input type, initial value. Cases are independently specified.
app('reading-planner','Reading Room','Plan a reading schedule around your available days.',
    [('pages','Pages remaining','number','180'),('days','Days available','number','7')],
    "const pages=num(d.pages,0), days=num(d.days,1); return {dailyPages:Math.ceil(pages/days),totalPages:pages};",
    [({'pages':'180','days':'7'},{'dailyPages':26,'totalPages':180}),({'pages':'1','days':'8'},{'dailyPages':1,'totalPages':1}),({'pages':'0','days':'1'},{'dailyPages':0,'totalPages':0})],
    ['Math.ceil(pages/days)','Math.floor(pages/days)'])
app('event-capacity','Open Doors','Check remaining seats and group admission for an event.',
    [('capacity','Venue capacity','number','120'),('booked','Seats booked','number','97'),('group','Group size','number','4')],
    "const cap=num(d.capacity,0), booked=num(d.booked,0), group=num(d.group,1); if(booked>cap) throw Error('Booked seats exceed capacity'); return {remaining:cap-booked,admitted:group<=cap-booked?'Yes':'No'};",
    [({'capacity':'10','booked':'7','group':'3'},{'remaining':3,'admitted':'Yes'}),({'capacity':'10','booked':'10','group':'1'},{'remaining':0,'admitted':'No'}),({'capacity':'30','booked':'4','group':'5'},{'remaining':26,'admitted':'Yes'})],
    ['group<=cap-booked','group<cap-booked'])
app('recipe-scaler','Kitchen Scale','Scale recipe quantities without losing fractional portions.',
    [('amount','Original quantity','number','250'),('servings','Original servings','number','4'),('target','Target servings','number','6')],
    "const amount=num(d.amount,0), servings=num(d.servings,0.01), target=num(d.target,0.01); return {quantity:round(amount*target/servings),factor:round(target/servings)};",
    [({'amount':'250','servings':'4','target':'6'},{'quantity':375,'factor':1.5}),({'amount':'3','servings':'2','target':'1'},{'quantity':1.5,'factor':0.5}),({'amount':'0','servings':'1','target':'5'},{'quantity':0,'factor':5})],
    ['amount*target/servings','amount*servings/target'])
app('inventory-alerts','Stock Watch','Find items at or below their reorder threshold. One name,stock,threshold per line.',
    [('items','Inventory rows','textarea','Paper,4,5\nInk,8,3')],
    "const rows=lines(d.items).map(x=>{const [name,stock,limit]=x.split(',').map(v=>v.trim()); if(!name) throw Error('Name required'); return {name,stock:num(stock,0),limit:num(limit,0)};}); const low=rows.filter(x=>x.stock<=x.limit); return {reorderCount:low.length,items:low.map(x=>x.name).join(', ')||'None'};",
    [({'items':'Paper,5,5\nInk,8,3'},{'reorderCount':1,'items':'Paper'}),({'items':'A,0,0\nB,1,2'},{'reorderCount':2,'items':'A, B'}),({'items':'A,9,2'},{'reorderCount':0,'items':'None'})],
    ['x.stock<=x.limit','x.stock<x.limit'])
app('ticket-pricing','Box Office','Quote group tickets with a discount for groups of ten or more.',
    [('adults','Adult tickets','number','2'),('children','Child tickets','number','1')],
    "const adults=num(d.adults,0), children=num(d.children,0); const count=adults+children, base=adults*20+children*12; const discount=count>=10?0.15:0; return {tickets:count,total:round(base*(1-discount)),discountPercent:discount*100};",
    [({'adults':'2','children':'1'},{'tickets':3,'total':52,'discountPercent':0}),({'adults':'10','children':'0'},{'tickets':10,'total':170,'discountPercent':15}),({'adults':'0','children':'10'},{'tickets':10,'total':102,'discountPercent':15})],
    ['count>=10','count>10'])
app('meeting-overlap','Meet Window','Find the overlap of two same-day availability windows in 24-hour time.',
    [('startA','First start','text','09:00'),('endA','First end','text','12:00'),('startB','Second start','text','11:00'),('endB','Second end','text','14:00')],
    "const a=time(d.startA),b=time(d.endA),c=time(d.startB),e=time(d.endB); if(b<a||e<c) throw Error('End precedes start'); const n=Math.max(0,Math.min(b,e)-Math.max(a,c)); return {overlapMinutes:n,available:n>0?'Yes':'No'};",
    [({'startA':'09:00','endA':'12:00','startB':'11:00','endB':'14:00'},{'overlapMinutes':60,'available':'Yes'}),({'startA':'09:00','endA':'10:00','startB':'10:00','endB':'11:00'},{'overlapMinutes':0,'available':'No'}),({'startA':'09:00','endA':'10:00','startB':'12:00','endB':'13:00'},{'overlapMinutes':0,'available':'No'})],
    ['Math.max(0,Math.min(b,e)-Math.max(a,c))','Math.abs(Math.min(b,e)-Math.max(a,c))'])
app('catalog-search','Small Shop','Filter a small product catalog by text and maximum price.',
    [('query','Search products','text',''),('budget','Maximum price','number','100')],
    "const budget=num(d.budget,0), q=d.query.trim().toLowerCase(); const products=[{name:'Canvas Bag',price:25},{name:'Desk Lamp',price:60},{name:'Notebook',price:12},{name:'Travel Mug',price:25}]; const found=products.filter(p=>p.price<=budget&&p.name.toLowerCase().includes(q)).sort((a,b)=>a.price-b.price||a.name.localeCompare(b.name)); return {matches:found.length,products:found.map(p=>p.name).join(', ')||'None'};",
    [({'query':' BAG ','budget':'25'},{'matches':1,'products':'Canvas Bag'}),({'query':'','budget':'25'},{'matches':3,'products':'Notebook, Canvas Bag, Travel Mug'}),({'query':'lamp','budget':'59'},{'matches':0,'products':'None'})],
    ['d.query.trim().toLowerCase()','d.query.toLowerCase()'])
app('text-insights','Draft Lens','Count words, characters, and reading minutes for a draft.',
    [('text','Your draft','textarea','A small idea can grow.')],
    "const text=d.text, words=text.trim()?text.trim().split(/\\s+/).length:0; return {words,characters:[...text].length,readingMinutes:Math.ceil(words/200)};",
    [({'text':' hello   world\nagain '},{'words':3,'characters':21,'readingMinutes':1}),({'text':''},{'words':0,'characters':0,'readingMinutes':0}),({'text':'Hi 🌙'},{'words':2,'characters':4,'readingMinutes':1})],
    ['characters:[...text].length','characters:text.length'])
app('trip-budget','Away Days','Estimate a trip budget including lodging, meals, and transport.',
    [('nights','Nights','number','3'),('nightly','Nightly room price','number','90'),('daily','Meals per day','number','30'),('transport','Transport total','number','80')],
    "const nights=num(d.nights,0), nightly=num(d.nightly,0), daily=num(d.daily,0), transport=num(d.transport,0); return {days:nights+1,lodging:round(nights*nightly),total:round(nights*nightly+(nights+1)*daily+transport)};",
    [({'nights':'3','nightly':'90','daily':'30','transport':'80'},{'days':4,'lodging':270,'total':470}),({'nights':'0','nightly':'100','daily':'20','transport':'5'},{'days':1,'lodging':0,'total':25}),({'nights':'1','nightly':'40','daily':'10','transport':'0'},{'days':2,'lodging':40,'total':60})],
    ['(nights+1)*daily','nights*daily'])
app('color-contrast','Contrast Desk','Calculate contrast between two six-digit hex colors.',
    [('foreground','Text color','text','#ffffff'),('background','Background color','text','#000000')],
    "function lum(s){if(!/^#[0-9a-f]{6}$/i.test(s)) throw Error('Use #RRGGBB colors'); const v=[1,3,5].map(i=>parseInt(s.slice(i,i+2),16)/255).map(x=>x<=0.04045?x/12.92:((x+0.055)/1.055)**2.4); return v[0]*0.2126+v[1]*0.7152+v[2]*0.0722;} const a=lum(d.foreground),b=lum(d.background),ratio=(Math.max(a,b)+0.05)/(Math.min(a,b)+0.05); return {ratio:round(ratio),normalText:ratio>=4.5?'Pass':'Fail',largeText:ratio>=3?'Pass':'Fail'};",
    [({'foreground':'#ffffff','background':'#000000'},{'ratio':21,'normalText':'Pass','largeText':'Pass'}),({'foreground':'#ffffff','background':'#ffffff'},{'ratio':1,'normalText':'Fail','largeText':'Fail'}),({'foreground':'#000000','background':'#FFFFFF'},{'ratio':21,'normalText':'Pass','largeText':'Pass'})],
    ['Math.max(a,b)+0.05','a+0.05'])
app('priority-board','Next Up','Sort tasks by priority and preserve order within each priority. One title,priority per line.',
    [('tasks','Tasks: low, medium, or high','textarea','Write draft,medium\nFix checkout,high\nChoose icon,low')],
    "const rank={high:0,medium:1,low:2}; const tasks=lines(d.tasks).map((x,i)=>{const [title,p]=x.split(',').map(v=>v.trim()); if(!title||!(p in rank)) throw Error('Use title,priority'); return {title,p,i};}).sort((a,b)=>rank[a.p]-rank[b.p]||a.i-b.i); return {count:tasks.length,next:tasks[0]?.title||'None',order:tasks.map(x=>x.title).join(' → ')};",
    [({'tasks':'A,low\nB,high\nC,medium'},{'count':3,'next':'B','order':'B → C → A'}),({'tasks':'Z,high\nA,high'},{'count':2,'next':'Z','order':'Z → A'}),({'tasks':'Solo,medium'},{'count':1,'next':'Solo','order':'Solo'})],
    ['rank[a.p]-rank[b.p]','rank[b.p]-rank[a.p]'])
app('shipping-quote','Parcel Desk','Quote parcel shipping with rounded-up weight tiers and a free-shipping threshold.',
    [('weight','Weight in kg','number','1.2'),('subtotal','Order subtotal','number','40')],
    "const weight=num(d.weight,0.01), subtotal=num(d.subtotal,0); const shipping=subtotal>=75?0:5+Math.max(0,Math.ceil(weight)-1)*2; return {shipping,orderTotal:round(subtotal+shipping)};",
    [({'weight':'1.2','subtotal':'40'},{'shipping':7,'orderTotal':47}),({'weight':'3','subtotal':'75'},{'shipping':0,'orderTotal':75}),({'weight':'1','subtotal':'0'},{'shipping':5,'orderTotal':5})],
    ['subtotal>=75','subtotal>75'])
app('quiz-score','Quiz Studio','Grade comma-separated answers against a comma-separated answer key.',
    [('answers','Answers','text','a, b, c'),('key','Answer key','text','A,B,D')],
    "const a=d.answers.split(',').map(x=>x.trim().toLowerCase()), k=d.key.split(',').map(x=>x.trim().toLowerCase()); if(!d.key.trim()||a.length!==k.length||k.some(x=>!x)) throw Error('Provide equal nonempty answer lists'); const correct=k.filter((x,i)=>x===a[i]).length; return {correct,total:k.length,percent:round(correct/k.length*100)};",
    [({'answers':'a, b, c','key':'A,B,D'},{'correct':2,'total':3,'percent':66.67}),({'answers':'x','key':'X'},{'correct':1,'total':1,'percent':100}),({'answers':'x,y','key':'a,b'},{'correct':0,'total':2,'percent':0})],
    ['correct/k.length*100','Math.floor(correct/k.length)*100'])
app('work-session','Focus Blocks','Plan focus blocks and breaks without adding a break after the last block.',
    [('blocks','Focus blocks','number','4'),('focus','Minutes per block','number','25'),('rest','Break minutes','number','5')],
    "const blocks=num(d.blocks,1),focus=num(d.focus,1),rest=num(d.rest,0); if(!Number.isInteger(blocks)) throw Error('Use whole blocks'); return {focusMinutes:blocks*focus,breakMinutes:(blocks-1)*rest,totalMinutes:blocks*focus+(blocks-1)*rest};",
    [({'blocks':'4','focus':'25','rest':'5'},{'focusMinutes':100,'breakMinutes':15,'totalMinutes':115}),({'blocks':'1','focus':'20','rest':'10'},{'focusMinutes':20,'breakMinutes':0,'totalMinutes':20}),({'blocks':'2','focus':'10','rest':'0'},{'focusMinutes':20,'breakMinutes':0,'totalMinutes':20})],
    ['(blocks-1)*rest','blocks*rest'])
app('duplicate-cleaner','Clean List','Deduplicate a list case-insensitively while preserving the first spelling and order.',
    [('items','One item per line','textarea','Alpha\nbeta\nALPHA')],
    "const seen=new Set(), source=lines(d.items), unique=source.filter(x=>{const key=x.toLowerCase(); if(seen.has(key)) return false; seen.add(key); return true;}); return {unique:unique.length,removed:source.length-unique.length,items:unique.join(', ')};",
    [({'items':' Alpha\nbeta\nALPHA '},{'unique':2,'removed':1,'items':'Alpha, beta'}),({'items':'B\nA\nB'},{'unique':2,'removed':1,'items':'B, A'}),({'items':'one'},{'unique':1,'removed':0,'items':'one'})],
    ['const key=x.toLowerCase()','const key=x'])
app('subscription-budget','Monthly View','Convert subscription prices to a monthly and annual total.',
    [('monthly','Monthly subscriptions total','number','20'),('annual','Annual subscriptions total','number','120')],
    "const monthly=num(d.monthly,0), annual=num(d.annual,0); return {monthlyEquivalent:round(monthly+annual/12),yearlyTotal:round(monthly*12+annual)};",
    [({'monthly':'20','annual':'120'},{'monthlyEquivalent':30,'yearlyTotal':360}),({'monthly':'0','annual':'60'},{'monthlyEquivalent':5,'yearlyTotal':60}),({'monthly':'5.5','annual':'0'},{'monthlyEquivalent':5.5,'yearlyTotal':66})],
    ['monthly+annual/12','monthly+annual'])

# Entire project families, including every task and variant, stay in one split.
app('unit-converter','Distance Lab','Convert kilometers into meters and miles.',
    [('kilometers','Distance in kilometers','number','5')],
    "const km=num(d.kilometers,0); return {meters:round(km*1000),miles:round(km/1.609344)};",
    [({'kilometers':'5'},{'meters':5000,'miles':3.11}),({'kilometers':'1.609344'},{'meters':1609.34,'miles':1}),({'kilometers':'0'},{'meters':0,'miles':0})],
    ['km*1000','km*100'], 'validation')
app('pagination','Page Window','Calculate page ranges for a paginated results list.',
    [('total','Total results','number','42'),('size','Results per page','number','10'),('page','Requested page','number','2')],
    "const total=num(d.total,0),size=num(d.size,1),requested=num(d.page,1); if(![total,size,requested].every(Number.isInteger)) throw Error('Use whole numbers'); const pages=Math.ceil(total/size),page=pages?Math.min(requested,pages):0; return {pages,page,first:page?(page-1)*size+1:0,last:Math.min(page*size,total)};",
    [({'total':'42','size':'10','page':'5'},{'pages':5,'page':5,'first':41,'last':42}),({'total':'0','size':'10','page':'1'},{'pages':0,'page':0,'first':0,'last':0}),({'total':'10','size':'10','page':'9'},{'pages':1,'page':1,'first':1,'last':10})],
    ['Math.ceil(total/size)','Math.floor(total/size)'], 'validation')
app('storage-estimate','Media Space','Estimate storage for a collection of media files.',
    [('count','File count','number','100'),('size','Megabytes per file','number','25'),('copies','Number of copies','number','2')],
    "const count=num(d.count,0), size=num(d.size,0), copies=num(d.copies,1); return {megabytes:round(count*size*copies),gigabytes:round(count*size*copies/1000)};",
    [({'count':'100','size':'25','copies':'2'},{'megabytes':5000,'gigabytes':5}),({'count':'0','size':'25','copies':'1'},{'megabytes':0,'gigabytes':0}),({'count':'1','size':'1000','copies':'3'},{'megabytes':3000,'gigabytes':3})],
    ['count*size*copies/1000','count*size/1000'], 'validation')
app('rsvp-summary','Guest List','Summarize invited guests by response. One name,status per line.',
    [('guests','Responses: yes, no, or pending','textarea','Ada,yes\nBen,pending\nCora,no')],
    "const counts={yes:0,no:0,pending:0}; for(const row of lines(d.guests)){const [name,status]=row.split(',').map(x=>x.trim().toLowerCase()); if(!name||!(status in counts)) throw Error('Use name,status'); counts[status]++;} return {attending:counts.yes,declined:counts.no,pending:counts.pending,total:counts.yes+counts.no+counts.pending};",
    [({'guests':'Ada,YES\nBen,pending\nCora,no'},{'attending':1,'declined':1,'pending':1,'total':3}),({'guests':'A,yes\nB,yes'},{'attending':2,'declined':0,'pending':0,'total':2}),({'guests':'A,pending'},{'attending':0,'declined':0,'pending':1,'total':1})],
    ['counts[status]++','counts[status]=1'], 'validation')
app('date-countdown','Day Marker','Count calendar days between ISO dates using UTC.',
    [('start','Start date','text','2026-01-01'),('end','End date','text','2026-02-01')],
    "function date(s){if(!/^\\d{4}-\\d{2}-\\d{2}$/.test(s)) throw Error('Use YYYY-MM-DD'); const t=Date.parse(s+'T00:00:00Z'); if(!Number.isFinite(t)||new Date(t).toISOString().slice(0,10)!==s) throw Error('Invalid date'); return t;} const days=(date(d.end)-date(d.start))/86400000; return {days,direction:days<0?'Past':days>0?'Future':'Today'};",
    [({'start':'2024-02-28','end':'2024-03-01'},{'days':2,'direction':'Future'}),({'start':'2026-01-01','end':'2026-01-01'},{'days':0,'direction':'Today'}),({'start':'2026-01-03','end':'2026-01-01'},{'days':-2,'direction':'Past'})],
    ['86400000','3600000'], 'test')
app('grade-planner','Course Balance','Calculate a weighted average from score,weight rows. Weights must total 100.',
    [('grades','Score,weight per line','textarea','80,40\n90,60')],
    "let total=0,weighted=0; for(const row of lines(d.grades)){const [a,b]=row.split(','); const score=num(a,0),weight=num(b,0); if(score>100) throw Error('Score exceeds 100'); total+=weight; weighted+=score*weight;} if(Math.abs(total-100)>0.0001) throw Error('Weights must total 100'); return {average:round(weighted/100)};",
    [({'grades':'80,40\n90,60'},{'average':86}),({'grades':'0,50\n100,50'},{'average':50}),({'grades':'100,100'},{'average':100})],
    ['weighted+=score*weight','weighted+=score'], 'test')
app('password-meter','Passphrase Lens','Give local-only password structure feedback. Nothing is transmitted.',
    [('password','Example password (do not use a real one)','text','Demo phrase 42!')],
    "const s=d.password; const categories=[/[a-z]/,/[A-Z]/,/\\d/,/[^a-zA-Z0-9\\s]/].filter(r=>r.test(s)).length; const score=(s.length>=12?2:s.length>=8?1:0)+categories; return {length:s.length,categories,rating:score>=6?'Strong':score>=4?'Moderate':'Weak'};",
    [({'password':'abcdefgh'},{'length':8,'categories':1,'rating':'Weak'}),({'password':'Abcdefgh12!?'},{'length':12,'categories':4,'rating':'Strong'}),({'password':''},{'length':0,'categories':0,'rating':'Weak'})],
    ['s.length>=12','s.length>12'], 'test')
app('round-robin','Match Day','Calculate pairings for a single round-robin tournament.',
    [('teams','Teams (one per line)','textarea','Owls\nFoxes\nBears')],
    "const teams=lines(d.teams); if(new Set(teams).size!==teams.length) throw Error('Team names must be unique'); const matches=[]; for(let i=0;i<teams.length;i++) for(let j=i+1;j<teams.length;j++) matches.push(teams[i]+' vs '+teams[j]); return {teams:teams.length,matches:matches.length,schedule:matches.join('; ')||'No matches'};",
    [({'teams':'A\nB\nC'},{'teams':3,'matches':3,'schedule':'A vs B; A vs C; B vs C'}),({'teams':'Solo'},{'teams':1,'matches':0,'schedule':'No matches'}),({'teams':'A\nB'},{'teams':2,'matches':1,'schedule':'A vs B'})],
    ['j=i+1','j=i'], 'test')
