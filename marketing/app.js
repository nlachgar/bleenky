const config=window.BLEENKY||{};
const toggle=document.querySelector('.menu-toggle'),nav=document.querySelector('#nav');
if(toggle&&nav){toggle.addEventListener('click',()=>{const open=toggle.getAttribute('aria-expanded')!=='true';toggle.setAttribute('aria-expanded',String(open));nav.classList.toggle('open',open);});nav.addEventListener('click',e=>{if(e.target.closest('a')){toggle.setAttribute('aria-expanded','false');nav.classList.remove('open');}});document.addEventListener('keydown',e=>{if(e.key==='Escape'&&nav.classList.contains('open')){toggle.setAttribute('aria-expanded','false');nav.classList.remove('open');toggle.focus();}});}
document.querySelectorAll('[data-year]').forEach(el=>el.textContent=new Date().getFullYear());
if(config.reviewMode===false)document.querySelectorAll('[data-review]').forEach(el=>el.hidden=true);
if(config.dashboardUrl?.startsWith('https://'))document.querySelectorAll('[data-dashboard]').forEach(a=>a.href=config.dashboardUrl);
const interestForm=document.querySelector('#interest-form');
if(interestForm){
 const status=document.querySelector('#form-status'),submit=interestForm.querySelector('[type="submit"]');
 let token='',sending=false;
 async function prepareForm(){
  try{const response=await fetch('contact.php',{credentials:'same-origin',cache:'no-store'});const result=await response.json();if(!response.ok||!result.token)throw new Error();token=result.token;submit.disabled=false;status.textContent='';}
  catch{status.textContent='The form is temporarily unavailable. Please use the email link instead.';}
 }
 const dialog=document.querySelector('#contact');
 let opener=null,scrollPosition=0;
 function openInquiry(link){
  if(link?.dataset.interest)document.querySelector('#contact-interest').value=link.dataset.interest;
  if(dialog.open)return;
  opener=link||document.activeElement;scrollPosition=window.scrollY;
  document.body.style.setProperty('--dialog-scroll',`-${scrollPosition}px`);
  document.body.classList.add('modal-open');
  dialog.showModal();dialog.scrollTop=0;
  document.querySelector('#inquiry-title').focus({preventScroll:true});
 }
 document.querySelectorAll('a[href="#contact"]').forEach(link=>{
  link.setAttribute('aria-haspopup','dialog');link.setAttribute('aria-controls','contact');
  link.addEventListener('click',event=>{event.preventDefault();openInquiry(link);});
 });
 dialog.querySelector('.inquiry-close').addEventListener('click',()=>dialog.close());
 let backdropPressed=false;
 dialog.addEventListener('pointerdown',event=>{backdropPressed=event.target===dialog;});
 dialog.addEventListener('click',event=>{if(backdropPressed&&event.target===dialog)dialog.close();backdropPressed=false;});
 dialog.addEventListener('close',()=>{
  document.body.classList.remove('modal-open');document.body.style.removeProperty('--dialog-scroll');
  if(location.hash==='#contact')history.replaceState(null,'',location.pathname+location.search);
  window.scrollTo({top:scrollPosition,behavior:'instant'});
  if(opener instanceof HTMLElement&&opener!==document.body)opener.focus({preventScroll:true});
 });
 window.addEventListener('hashchange',()=>{if(location.hash==='#contact')openInquiry();});
 if(location.hash==='#contact')openInquiry();
 interestForm.addEventListener('submit',async event=>{
  event.preventDefault();if(sending||!token||!interestForm.reportValidity())return;
  sending=true;submit.disabled=true;submit.textContent='Sending…';status.textContent='Sending your inquiry…';status.classList.remove('is-error','is-success');
  try{
   const payload=Object.fromEntries(new FormData(interestForm));payload.token=token;
   const response=await fetch('contact.php',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
   const result=await response.json();if(!response.ok||!result.ok)throw new Error(result.error||'Your inquiry could not be sent. Please try again or email us.');
   status.textContent=result.message;status.classList.add('is-success');status.setAttribute('tabindex','-1');status.focus();interestForm.reset();token='';submit.textContent='Inquiry sent';
  }catch(error){status.textContent=error.message||'We could not connect. Please retry or use the email link.';status.classList.add('is-error');submit.disabled=false;submit.textContent='Send my inquiry';}
  finally{sending=false;}
 });
 prepareForm();
}
