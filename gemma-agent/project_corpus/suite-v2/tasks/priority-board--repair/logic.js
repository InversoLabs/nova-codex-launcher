function num(value,min){if(String(value).trim()==='') throw Error('Enter all numeric fields'); const n=Number(value); if(!Number.isFinite(n)||n<min) throw Error('Enter a number of at least '+min); return n;}
function round(n){return Math.round((n+Number.EPSILON)*100)/100;}
function lines(s){return s.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);}
function time(s){if(!/^([01]\d|2[0-3]):[0-5]\d$/.test(s)) throw Error('Use HH:MM in 24-hour time'); const [h,m]=s.split(':').map(Number); return h*60+m;}

function run(d){
const rank={high:0,medium:1,low:2}; const tasks=lines(d.tasks).map((x,i)=>{const [title,p]=x.split(',').map(v=>v.trim()); if(!title||!(p in rank)) throw Error('Use title,priority'); return {title,p,i};}).sort((a,b)=>rank[b.p]-rank[a.p]||a.i-b.i); return {count:tasks.length,next:tasks[0]?.title||'None',order:tasks.map(x=>x.title).join(' → ')};
}
