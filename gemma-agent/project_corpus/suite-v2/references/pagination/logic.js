function num(value,min){if(String(value).trim()==='') throw Error('Enter all numeric fields'); const n=Number(value); if(!Number.isFinite(n)||n<min) throw Error('Enter a number of at least '+min); return n;}
function round(n){return Math.round((n+Number.EPSILON)*100)/100;}
function lines(s){return s.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);}
function time(s){if(!/^([01]\d|2[0-3]):[0-5]\d$/.test(s)) throw Error('Use HH:MM in 24-hour time'); const [h,m]=s.split(':').map(Number); return h*60+m;}

function run(d){
const total=num(d.total,0),size=num(d.size,1),requested=num(d.page,1); if(![total,size,requested].every(Number.isInteger)) throw Error('Use whole numbers'); const pages=Math.ceil(total/size),page=pages?Math.min(requested,pages):0; return {pages,page,first:page?(page-1)*size+1:0,last:Math.min(page*size,total)};
}
