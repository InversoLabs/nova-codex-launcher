function num(value,min){if(String(value).trim()==='') throw Error('Enter all numeric fields'); const n=Number(value); if(!Number.isFinite(n)||n<min) throw Error('Enter a number of at least '+min); return n;}
function round(n){return Math.round((n+Number.EPSILON)*100)/100;}
function lines(s){return s.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);}
function time(s){if(!/^([01]\d|2[0-3]):[0-5]\d$/.test(s)) throw Error('Use HH:MM in 24-hour time'); const [h,m]=s.split(':').map(Number); return h*60+m;}

function run(d){
function date(s){if(!/^\d{4}-\d{2}-\d{2}$/.test(s)) throw Error('Use YYYY-MM-DD'); const t=Date.parse(s+'T00:00:00Z'); if(!Number.isFinite(t)||new Date(t).toISOString().slice(0,10)!==s) throw Error('Invalid date'); return t;} const days=(date(d.end)-date(d.start))/3600000; return {days,direction:days<0?'Past':days>0?'Future':'Today'};
}
