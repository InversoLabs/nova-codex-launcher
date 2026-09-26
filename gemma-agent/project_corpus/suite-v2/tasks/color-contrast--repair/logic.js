function num(value,min){if(String(value).trim()==='') throw Error('Enter all numeric fields'); const n=Number(value); if(!Number.isFinite(n)||n<min) throw Error('Enter a number of at least '+min); return n;}
function round(n){return Math.round((n+Number.EPSILON)*100)/100;}
function lines(s){return s.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);}
function time(s){if(!/^([01]\d|2[0-3]):[0-5]\d$/.test(s)) throw Error('Use HH:MM in 24-hour time'); const [h,m]=s.split(':').map(Number); return h*60+m;}

function run(d){
function lum(s){if(!/^#[0-9a-f]{6}$/i.test(s)) throw Error('Use #RRGGBB colors'); const v=[1,3,5].map(i=>parseInt(s.slice(i,i+2),16)/255).map(x=>x<=0.04045?x/12.92:((x+0.055)/1.055)**2.4); return v[0]*0.2126+v[1]*0.7152+v[2]*0.0722;} const a=lum(d.foreground),b=lum(d.background),ratio=(a+0.05)/(Math.min(a,b)+0.05); return {ratio:round(ratio),normalText:ratio>=4.5?'Pass':'Fail',largeText:ratio>=3?'Pass':'Fail'};
}
