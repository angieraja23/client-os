function openJobDrawer(idx) {
  var j = _jobs[idx]; if (!j) return;
  var src = j.source || '';
  var isLI = src.indexOf('LinkedIn') > -1;
  var isIN = src.indexOf('Indeed') > -1;
  var iconBg = isLI ? '#0a66c2' : isIN ? '#003a9b' : '#555';
  var iconTxt = isLI ? 'LI' : isIN ? 'IN' : 'GJ';
  document.getElementById('drawer-content').innerHTML = '<div style="display:flex;align-items:center;gap:12px"><div style="width:48px;height:48px;border-radius:10px;background:'+iconBg+';display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;color:#fff">'+iconTxt+'</div><div><div class="drawer-name">'+j.title+'</div><div class="drawer-sub">'+j.company+(j.location?' &middot; '+j.location:'')+'</div></div></div>';
  var btns = ['applied','interviewing','offer'].map(function(s){
    var l={applied:'Applied',interviewing:'Interviewing',offer:'Offer'};
    var cl={applied:'var(--lead)',interviewing:'var(--proposal)',offer:'var(--client)'};
    var bg={applied:'var(--lead-bg)',interviewing:'var(--proposal-bg)',offer:'var(--client-bg)'};
    var a=j.stage===s?'background:'+bg[s]+';color:'+cl[s]+';border-color:'+cl[s]:'';
    return '<button class="stage-btn" style="'+a+'" onclick="setJobStage('+idx+',\''+s+'\')">'+l[s]+'</button>';
  }).join('');
  var notes=(j.notes||[]).map(function(n){return '<div class="note-entry"><div class="note-text">'+n.text+'</div><div class="note-date">'+n.date+'</div></div>';}).join('');
  var srcBadge=isLI?'<span style="background:rgba(10,102,194,.15);color:#60a5fa;padding:3px 8px;border-radius:10px;font-size:11px">LinkedIn</span>':isIN?'<span style="background:rgba(0,58,155,.15);color:#93c5fd;padding:3px 8px;border-radius:10px;font-size:11px">Indeed</span>':'<span style="background:var(--surface2);color:var(--text2);padding:3px 8px;border-radius:10px;font-size:11px">'+src+'</span>';
  var ea=src.indexOf('Easy')>-1?'<span style="background:rgba(16,185,129,.12);color:var(--client);padding:3px 8px;border-radius:10px;font-size:11px;margin-left:4px">'+(isLI?'Easy Apply':'Easily Apply')+'</span>':'';
  document.getElementById('drawer-body').innerHTML=(j.url?'<div class="drawer-section"><a href="'+j.url+'" target="_blank" style="color:var(--lead);font-size:13px;text-decoration:none;font-weight:500">&#x2197; View &amp; Apply</a></div>':'')+'<div class="drawer-section"><div class="drawer-label">Source</div>'+srcBadge+ea+'</div>'+(j.salary?'<div class="drawer-section"><div class="drawer-label">Salary</div><div style="font-size:18px;font-weight:600;color:var(--client)">'+j.salary+'</div></div>':'')+'<div class="drawer-section"><div class="drawer-label">Stage</div><div class="stage-buttons">'+btns+'</div></div><div class="drawer-section"><div class="drawer-label">Notes</div><textarea class="note-box" id="job-note-box" placeholder="Add notes..."></textarea><button class="note-save-btn" onclick="saveJobNote('+idx+')">Save Note</button><div style="margin-top:10px">'+notes+'</div></div>';
  document.getElementById('drawer').classList.add('open');
  document.getElementById('overlay').classList.add('open');
}
function setJobStage(idx,stage){_jobs[idx].stage=stage;try{localStorage.setItem('caos_jobs_stages',JSON.stringify(_jobs.map(function(j){return{id:j.id,stage:j.stage,notes:j.notes};})));}catch(e){}renderJobs();openJobDrawer(idx);}
function saveJobNote(idx){var v=document.getElementById('job-note-box').value.trim();if(!v)return;_jobs[idx].notes=_jobs[idx].notes||[];_jobs[idx].notes.unshift({text:v,date:new Date().toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'})});try{localStorage.setItem('caos_jobs_stages',JSON.stringify(_jobs.map(function(j){return{id:j.id,stage:j.stage,notes:j.notes};})));}catch(e){}openJobDrawer(idx);}
