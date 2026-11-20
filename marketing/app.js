const config=window.BLEENKY||{};
const toggle=document.querySelector('.menu-toggle'),nav=document.querySelector('#nav');
if(toggle&&nav){toggle.addEventListener('click',()=>{const open=toggle.getAttribute('aria-expanded')!=='true';toggle.setAttribute('aria-expanded',String(open));nav.classList.toggle('open',open);});nav.addEventListener('click',e=>{if(e.target.closest('a')){toggle.setAttribute('aria-expanded','false');nav.classList.remove('open');}});document.addEventListener('keydown',e=>{if(e.key==='Escape'&&nav.classList.contains('open')){toggle.setAttribute('aria-expanded','false');nav.classList.remove('open');toggle.focus();}});}
document.querySelectorAll('[data-year]').forEach(el=>el.textContent=new Date().getFullYear());
if(config.reviewMode===false)document.querySelectorAll('[data-review]').forEach(el=>el.hidden=true);
if(config.dashboardUrl?.startsWith('https://'))document.querySelectorAll('[data-dashboard]').forEach(a=>a.href=config.dashboardUrl);
const email=typeof config.contactEmail==='string'?config.contactEmail.trim():'';
let selectedPlan='',opener=null;
const dialog=document.querySelector('#contact-dialog');
function emailLink(){return 'mailto:'+encodeURIComponent(email)+'?subject='+encodeURIComponent('Bleenky inquiry'+(selectedPlan?' — '+selectedPlan:''))+'&body='+encodeURIComponent('Hi Bleenky,\n\nSalon name:\nLocation:\nCurrent website (if any):\nHow we currently take appointments:\nWhat we would like help with:\n\nThanks!');}
function setContact(){document.querySelectorAll('[data-contact]').forEach(a=>a.href=email?emailLink():'#contact');}
setContact();
document.querySelectorAll('[data-plan]').forEach(a=>a.addEventListener('click',()=>{selectedPlan=a.dataset.plan;setContact();}));
document.querySelectorAll('[data-contact]').forEach(a=>a.addEventListener('click',e=>{if(email)return;e.preventDefault();opener=a;if(dialog){dialog.showModal();dialog.querySelector('button').focus();}}));
if(!email)document.querySelectorAll('[data-contact-note]').forEach(el=>el.textContent='Inquiries open after the contact address is connected.');
if(dialog){document.querySelectorAll('[data-close]').forEach(b=>b.addEventListener('click',()=>dialog.close()));dialog.addEventListener('close',()=>opener?.focus());}
