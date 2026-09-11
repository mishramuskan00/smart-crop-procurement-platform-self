// Apni Baari - Government Portal Operations Script

function toggleMenu(){
  document.querySelector('.nav-links').classList.toggle('open');
}

function searchPage(){
  const q = (document.getElementById('globalSearch')?.value || '').toLowerCase();
  if(q.includes('center') || q.includes('मंडी')) location.href = 'gov-live-centers.html';
  else if(q.includes('queue') || q.includes('कतार')) location.href = 'gov-queue-management.html';
  else if(q.includes('slot') || q.includes('स्लॉट')) location.href = 'gov-slot-management.html';
  else if(q.includes('procurement') || q.includes('उपार्जन') || q.includes('तौल')) location.href = 'gov-procurement.html';
  else if(q.includes('report') || q.includes('रिपोर्ट')) location.href = 'gov-reports.html';
  else if(q.includes('analytics') || q.includes('विश्लेषण')) location.href = 'gov-analytics.html';
  else if(q.includes('notification') || q.includes('सूचना')) location.href = 'gov-notifications.html';
  else if(q.includes('setting') || q.includes('सेटिंग')) location.href = 'gov-settings.html';
  else location.href = 'gov-dashboard.html';
}

document.querySelectorAll('[data-year]').forEach(e => e.textContent = new Date().getFullYear());

function openModal(title, body){
  let b = document.getElementById('modalBackdrop');
  if(!b) {
    b = document.createElement('div');
    b.id = 'modalBackdrop';
    b.className = 'modal-backdrop';
    b.onclick = (e) => { if(e.target === b) closeModal(); };
    b.innerHTML = `
      <div class="modal">
        <button class="modal-close" onclick="closeModal()">×</button>
        <h2 id="modalTitle"></h2>
        <div id="modalBody" style="margin:16px 0;line-height:1.6"></div>
        <button class="btn btn-green" onclick="closeModal()">बंद करें (Close)</button>
      </div>
    `;
    document.body.appendChild(b);
  }
  document.getElementById('modalTitle').textContent = title;
  document.getElementById('modalBody').innerHTML = body;
  b.classList.add('show');
}

function closeModal(){
  const b = document.getElementById('modalBackdrop');
  if(b) b.classList.remove('show');
}

// Check session on officer pages
document.addEventListener("DOMContentLoaded", () => {
  const user = getCurrentUser ? getCurrentUser() : null;
  const token = getAuthToken ? getAuthToken() : null;
  const navInner = document.querySelector(".nav-inner");

  if(navInner && !document.getElementById("officerUserBadge")) {
    const badge = document.createElement("div");
    badge.id = "officerUserBadge";
    badge.style.cssText = "margin-left:auto;display:flex;align-items:center;gap:12px;font-size:13.5px;";
    badge.innerHTML = `
      <span style="color:#17163f;font-weight:700;">🏛️ ${user?.name || 'A. Sharma'} (${user?.official_id || 'OFF-HR-701'})</span>
      <a href="javascript:void(0)" onclick="logout()" style="color:#c44720;font-weight:700;text-decoration:none;">लॉगआउट</a>
    `;
    navInner.appendChild(badge);
  }
});
