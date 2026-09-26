function num(value,min){if(String(value).trim()==='') throw Error('Enter all numeric fields'); const n=Number(value); if(!Number.isFinite(n)||n<min) throw Error('Enter a number of at least '+min); return n;}
function round(n){return Math.round((n+Number.EPSILON)*100)/100;}
function lines(s){return s.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);}
function time(s){if(!/^([01]\d|2[0-3]):[0-5]\d$/.test(s)) throw Error('Use HH:MM in 24-hour time'); const [h,m]=s.split(':').map(Number); return h*60+m;}

function run(d){
const s=d.password; const categories=[/[a-z]/,/[A-Z]/,/\d/,/[^a-zA-Z0-9\s]/].filter(r=>r.test(s)).length; const score=(s.length>12?2:s.length>=8?1:0)+categories; return {length:s.length,categories,rating:score>=6?'Strong':score>=4?'Moderate':'Weak'};
}
