function num(value,min){if(String(value).trim()==='') throw Error('Enter all numeric fields'); const n=Number(value); if(!Number.isFinite(n)||n<min) throw Error('Enter a number of at least '+min); return n;}
function round(n){return Math.round((n+Number.EPSILON)*100)/100;}
function lines(s){return s.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);}
function time(s){if(!/^([01]\d|2[0-3]):[0-5]\d$/.test(s)) throw Error('Use HH:MM in 24-hour time'); const [h,m]=s.split(':').map(Number); return h*60+m;}

function run(d){
const teams=lines(d.teams); if(new Set(teams).size!==teams.length) throw Error('Team names must be unique'); const matches=[]; for(let i=0;i<teams.length;i++) for(let j=i;j<teams.length;j++) matches.push(teams[i]+' vs '+teams[j]); return {teams:teams.length,matches:matches.length,schedule:matches.join('; ')||'No matches'};
}
