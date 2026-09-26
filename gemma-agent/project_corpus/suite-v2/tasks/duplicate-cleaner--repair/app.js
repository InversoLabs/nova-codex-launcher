const form=document.querySelector('form'), result=document.querySelector('#result'), error=document.querySelector('#error');
const storageKey='nova-demo:'+document.body.dataset.project;
const history=document.querySelector('#history');
function label(key){return key.replace(/([A-Z])/g,' $1').replace(/^./,x=>x.toUpperCase());}
function render(value){result.replaceChildren(); for(const [key,text] of Object.entries(value)){const card=document.createElement('div'); card.className='metric'; const dt=document.createElement('dt'),dd=document.createElement('dd'); dt.textContent=label(key); dd.textContent=String(text); dd.dataset.metric=key;card.append(dt,dd);result.append(card);} result.hidden=false;}
function restore(){history.replaceChildren(); try{const saved=JSON.parse(localStorage.getItem(storageKey)||'null'); if(saved){const item=document.createElement('li'); item.textContent=Object.values(saved).join(' · '); history.append(item);}}catch{localStorage.removeItem(storageKey);}}
form.addEventListener('submit',event=>{event.preventDefault(); error.textContent='';result.hidden=true;try{const value=run(Object.fromEntries(new FormData(form)));render(value);if(document.body.dataset.persist==='yes'){localStorage.setItem(storageKey,JSON.stringify(value));restore();}}catch(e){result.replaceChildren();error.textContent=e.message||'Please check your input';}});
document.querySelector('#reset').addEventListener('click',()=>{HTMLFormElement.prototype.reset.call(form);result.replaceChildren();result.hidden=true;error.textContent='';});
document.querySelector('#clear').addEventListener('click',()=>{localStorage.removeItem(storageKey);restore();});
restore();
