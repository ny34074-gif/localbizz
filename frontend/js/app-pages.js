document.addEventListener('DOMContentLoaded',()=>{
 const home=document.getElementById('homeSearch');
 if(home)home.addEventListener('submit',e=>{e.preventDefault();const f=new FormData(home);location.href='businesses.html?'+new URLSearchParams({q:f.get('q')||'',location:f.get('location')||''})});

 const bf=document.getElementById('businessForm');
 if(bf)bf.addEventListener('submit',async e=>{
   e.preventDefault();const btn=bf.querySelector('button');btn.disabled=true;btn.textContent='Submitting...';
   try{await api('/businesses',{method:'POST',body:new FormData(bf)});showMessage('Business submitted for admin approval');setTimeout(()=>location.href='owner-dashboard.html',700)}
   catch(err){showMessage(err.message,'error');btn.disabled=false;btn.textContent='Submit for Approval'}
 });

 const cf=document.getElementById('contactForm');
 if(cf)cf.addEventListener('submit',async e=>{
   e.preventDefault();const f=new FormData(cf);
   try{await api('/contact',{method:'POST',body:{name:f.get('name'),email:f.get('email'),subject:f.get('subject'),message:f.get('message'),business_id:f.get('business_id')||null}});cf.reset();showMessage('Message sent successfully')}
   catch(err){showMessage(err.message,'error')}
 });

 const box=document.getElementById('businessDetails');if(box)loadDetails(box);
 if(document.body.dataset.page==='owner')loadOwner();
 if(document.body.dataset.page==='admin')loadAdmin();

 if(document.getElementById('ownerBusinessTable'))loadOwnerBusinesses();
 if(document.getElementById('ownerReviewTable'))loadOwnerReviews();
 if(document.getElementById('ownerMessageTable'))loadOwnerMessages();
 if(document.getElementById('profileBox'))loadProfile();
 if(document.getElementById('adminUserTable'))loadAdminUsers();
 if(document.getElementById('adminBusinessTable'))loadAdminBusinesses();
 if(document.getElementById('adminReviewTable'))loadAdminReviews();
 if(document.getElementById('adminMessageTable'))loadAdminMessages();
});

async function loadDetails(box){
 const id=new URLSearchParams(location.search).get('id');
 if(!id){box.innerHTML='<div class="empty">Business ID missing.</div>';return}
 try{
  const d=await api('/businesses/'+id),b=d.business;
  const img=b.images?.[0]?API+b.images[0].image_path:'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1200&q=80';
  box.innerHTML=`<div><img class="gallery-main" src="${esc(img)}" alt="${esc(b.business_name)}"><div class="details-card" style="margin-top:22px"><h2>About ${esc(b.business_name)}</h2><p>${esc(b.description||'No description.')}</p><h3 style="margin-top:22px">Services</h3><div class="service-list">${String(b.services||'').split(',').filter(Boolean).map(s=>`<span class="service">${esc(s.trim())}</span>`).join('')||'<span class="muted">No services listed.</span>'}</div></div><div class="details-card" style="margin-top:22px"><h2>Customer Reviews</h2><div>${(b.reviews||[]).map(r=>`<div class="review"><div class="review-top"><strong>${esc(r.user_name)}</strong><span class="stars">★ ${r.rating}</span></div><p>${esc(r.review_text||'')}</p></div>`).join('')||'<p class="muted">No reviews yet.</p>'}</div><form id="reviewForm" style="margin-top:20px"><h3>Write a Review</h3><div class="form-row"><input name="rating" class="input" type="number" min="1" max="5" required placeholder="Rating 1-5"><input name="review_text" class="input" required placeholder="Your review"></div><button class="btn btn-primary" style="margin-top:12px">Submit Review</button></form></div></div><aside><div class="details-card"><h1>${esc(b.business_name)}</h1><div class="rating">★★★★★ ${money(b.avg_rating)} <span class="muted">(${b.review_count||0} reviews)</span></div><div class="meta">🏷️ ${esc(b.category||'Business')}</div><div class="info-list"><div class="info-item">📍<div><strong>Address</strong>${esc(b.address||b.location||'')}</div></div><div class="info-item">📞<div><strong>Phone</strong>${esc(b.phone||'')}</div></div><div class="info-item">✉️<div><strong>Email</strong>${esc(b.email||'')}</div></div><div class="info-item">🕐<div><strong>Opening Hours</strong>${esc(b.opening_time||'')} – ${esc(b.closing_time||'')}</div></div></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:20px"><a class="btn btn-primary" href="tel:${esc(b.phone||'')}">📞 Call</a><a class="btn btn-outline" href="contact.html?business_id=${b.id}">💬 Message</a></div></div></aside>`;
  document.getElementById('reviewForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.target);try{await api('/reviews/'+id,{method:'POST',body:{rating:f.get('rating'),review_text:f.get('review_text')}});showMessage('Review submitted');setTimeout(()=>location.reload(),600)}catch(err){showMessage(err.message,'error')}})
 }catch(e){box.innerHTML='<div class="empty">Business not found.</div>';showMessage(e.message,'error')}
}

async function loadOwner(){
 try{const d=await api('/businesses/owner/my'),r=d.businesses||[];document.querySelector('.stat-grid').innerHTML=`<div class="stat"><h4>Total Businesses</h4><strong>${r.length}</strong></div><div class="stat"><h4>Approved</h4><strong>${r.filter(x=>x.status==='approved').length}</strong></div><div class="stat"><h4>Pending</h4><strong>${r.filter(x=>x.status==='pending').length}</strong></div><div class="stat"><h4>Total Reviews</h4><strong>${r.reduce((a,x)=>a+Number(x.review_count||0),0)}</strong></div>`;const tb=document.querySelector('.table tbody');tb.innerHTML=r.map(b=>`<tr><td>${esc(b.business_name)}</td><td>${esc(b.category)}</td><td>★ ${money(b.avg_rating)}</td><td><span class="status ${b.status}">${b.status}</span></td><td><a class="btn btn-outline" href="business-details.html?id=${b.id}">View</a></td></tr>`).join('')||'<tr><td colspan="5" class="empty">No businesses yet.</td></tr>'}catch(e){showMessage(e.message,'error')}
}
async function loadAdmin(){
 try{const d=await api('/admin/dashboard'),s=d.stats;[s.users,s.businesses,s.pending_businesses,s.reviews].forEach((v,i)=>document.querySelectorAll('.stat strong')[i].textContent=v??0);const all=await api('/admin/businesses'),p=(all.businesses||[]).filter(b=>b.status==='pending');document.querySelector('.table tbody').innerHTML=p.map(b=>`<tr><td>${esc(b.business_name)}</td><td>${esc(b.owner_name)}</td><td>${esc(b.category)}</td><td>${new Date(b.created_at).toLocaleDateString()}</td><td><button class="btn btn-success" onclick="setStatus(${b.id},'approved')">Approve</button> <button class="btn btn-danger" onclick="setStatus(${b.id},'rejected')">Reject</button></td></tr>`).join('')||'<tr><td colspan="5" class="empty">No pending businesses.</td></tr>'}catch(e){showMessage(e.message,'error')}
}
async function setStatus(id,status){try{await api('/admin/businesses/'+id+'/status',{method:'PATCH',body:{status}});showMessage('Business '+status);setTimeout(()=>location.reload(),500)}catch(e){showMessage(e.message,'error')}}window.setStatus=setStatus;

async function guard(roles){const d=await api('/auth/me');if(!roles.includes(d.user.role))throw new Error('You do not have permission to view this page.');return d.user}
async function loadOwnerBusinesses(){const box=document.getElementById('ownerBusinessTable');try{await guard(['business_owner','admin']);const d=await api('/businesses/owner/my');box.innerHTML=(d.businesses||[]).map(b=>`<tr><td>${esc(b.business_name)}</td><td>${esc(b.category)}</td><td>★ ${money(b.avg_rating)}</td><td><span class="status ${b.status}">${b.status}</span></td><td><a class="btn btn-outline" href="business-details.html?id=${b.id}">View</a></td></tr>`).join('')||'<tr><td colspan="5" class="empty">No businesses yet.</td></tr>'}catch(e){box.innerHTML=`<tr><td colspan="5" class="empty">${esc(e.message)}</td></tr>`}}
async function loadOwnerReviews(){const box=document.getElementById('ownerReviewTable');try{await guard(['business_owner','admin']);const d=await api('/reviews/owner');box.innerHTML=(d.reviews||[]).map(r=>`<tr><td>${esc(r.business_name)}</td><td>${esc(r.user_name)}</td><td><span class="stars">★ ${r.rating}</span></td><td>${esc(r.review_text||'')}</td><td>${new Date(r.created_at).toLocaleDateString()}</td></tr>`).join('')||'<tr><td colspan="5" class="empty">No reviews yet.</td></tr>'}catch(e){box.innerHTML=`<tr><td colspan="5" class="empty">${esc(e.message)}</td></tr>`}}
async function loadOwnerMessages(){const box=document.getElementById('ownerMessageTable');try{await guard(['business_owner','admin']);const d=await api('/contact/owner');box.innerHTML=(d.messages||[]).map(m=>`<tr><td>${esc(m.business_name||'')}</td><td>${esc(m.name)}</td><td>${esc(m.email)}</td><td>${esc(m.subject)}</td><td>${esc(m.message)}</td><td>${esc(m.status)}</td></tr>`).join('')||'<tr><td colspan="6" class="empty">No messages yet.</td></tr>'}catch(e){box.innerHTML=`<tr><td colspan="6" class="empty">${esc(e.message)}</td></tr>`}}
async function loadProfile(){const box=document.getElementById('profileBox');try{const d=await api('/auth/me'),u=d.user;box.innerHTML=`<div class="details-card"><h2>My Profile</h2><div class="info-list"><div class="info-item">👤<div><strong>Name</strong>${esc(u.name)}</div></div><div class="info-item">✉️<div><strong>Email</strong>${esc(u.email)}</div></div><div class="info-item">📞<div><strong>Phone</strong>${esc(u.phone||'Not provided')}</div></div><div class="info-item">🔐<div><strong>Role</strong>${esc(u.role)}</div></div></div></div>`}catch(e){box.innerHTML=`<div class="empty">${esc(e.message)}</div>`}}

async function loadAdminUsers(){const box=document.getElementById('adminUserTable');try{await guard(['admin']);const d=await api('/admin/users');box.innerHTML=(d.users||[]).map(u=>`<tr><td>${u.id}</td><td>${esc(u.name)}</td><td>${esc(u.email)}</td><td>${esc(u.role)}</td><td>${new Date(u.created_at).toLocaleDateString()}</td></tr>`).join('')||'<tr><td colspan="5" class="empty">No users.</td></tr>'}catch(e){box.innerHTML=`<tr><td colspan="5" class="empty">${esc(e.message)}</td></tr>`}}
async function loadAdminBusinesses(){const box=document.getElementById('adminBusinessTable');try{await guard(['admin']);const d=await api('/admin/businesses');box.innerHTML=(d.businesses||[]).map(b=>`<tr><td>${esc(b.business_name)}</td><td>${esc(b.owner_name)}</td><td>${esc(b.category)}</td><td><span class="status ${b.status}">${b.status}</span></td><td><select class="select" onchange="adminStatus(${b.id},this.value)"><option value="pending" ${b.status==='pending'?'selected':''}>Pending</option><option value="approved" ${b.status==='approved'?'selected':''}>Approved</option><option value="rejected" ${b.status==='rejected'?'selected':''}>Rejected</option></select></td></tr>`).join('')||'<tr><td colspan="5" class="empty">No businesses.</td></tr>'}catch(e){box.innerHTML=`<tr><td colspan="5" class="empty">${esc(e.message)}</td></tr>`}}
async function adminStatus(id,status){try{await api('/admin/businesses/'+id+'/status',{method:'PATCH',body:{status}});showMessage('Status updated')}catch(e){showMessage(e.message,'error')}}window.adminStatus=adminStatus;
async function loadAdminReviews(){const box=document.getElementById('adminReviewTable');try{await guard(['admin']);const d=await api('/admin/reviews');box.innerHTML=(d.reviews||[]).map(r=>`<tr><td>${esc(r.business_name)}</td><td>${esc(r.user_name)}</td><td><span class="stars">★ ${r.rating}</span></td><td>${esc(r.review_text||'')}</td><td><button class="btn btn-danger" onclick="deleteAdminReview(${r.id})">Delete</button></td></tr>`).join('')||'<tr><td colspan="5" class="empty">No reviews.</td></tr>'}catch(e){box.innerHTML=`<tr><td colspan="5" class="empty">${esc(e.message)}</td></tr>`}}
async function deleteAdminReview(id){try{await api('/reviews/'+id,{method:'DELETE'});showMessage('Review deleted');loadAdminReviews()}catch(e){showMessage(e.message,'error')}}window.deleteAdminReview=deleteAdminReview;
async function loadAdminMessages(){const box=document.getElementById('adminMessageTable');try{await guard(['admin']);const d=await api('/admin/messages');box.innerHTML=(d.messages||[]).map(m=>`<tr><td>${esc(m.business_name||'General')}</td><td>${esc(m.name)}</td><td>${esc(m.email)}</td><td>${esc(m.subject)}</td><td>${esc(m.message)}</td><td>${esc(m.status)}</td></tr>`).join('')||'<tr><td colspan="6" class="empty">No messages.</td></tr>'}catch(e){box.innerHTML=`<tr><td colspan="6" class="empty">${esc(e.message)}</td></tr>`}}
