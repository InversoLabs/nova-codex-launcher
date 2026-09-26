function num(value,min){if(String(value).trim()==='') throw Error('Enter all numeric fields'); const n=Number(value); if(!Number.isFinite(n)||n<min) throw Error('Enter a number of at least '+min); return n;}
function round(n){return Math.round((n+Number.EPSILON)*100)/100;}
function lines(s){return s.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);}
function time(s){if(!/^([01]\d|2[0-3]):[0-5]\d$/.test(s)) throw Error('Use HH:MM in 24-hour time'); const [h,m]=s.split(':').map(Number); return h*60+m;}

function run(d){
const counts={yes:0,no:0,pending:0}; for(const row of lines(d.guests)){const [name,status]=row.split(',').map(x=>x.trim().toLowerCase()); if(!name||!(status in counts)) throw Error('Use name,status'); counts[status]++;} return {attending:counts.yes,declined:counts.no,pending:counts.pending,total:counts.yes+counts.no+counts.pending};
}
