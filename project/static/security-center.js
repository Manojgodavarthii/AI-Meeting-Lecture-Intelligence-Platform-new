/* ═══════════════════════════════════════════════════════════════════════════════
   EchoAction Security Center — All 20 Enterprise Security Modules
   ═══════════════════════════════════════════════════════════════════════════════ */
(function(){
"use strict";

var SEC_MODULES = [
  {id:"auth",       icon:"fa-solid fa-key",              label:"Authentication Security",  color:"#818cf8"},
  {id:"account",    icon:"fa-solid fa-user-shield",       label:"Account Security",         color:"#06b6d4"},
  {id:"rbac",       icon:"fa-solid fa-users-gear",        label:"Role-Based Access Control", color:"#8b5cf6"},
  {id:"perm",       icon:"fa-solid fa-lock",              label:"Permission Management",     color:"#a78bfa"},
  {id:"upload",     icon:"fa-solid fa-file-shield",       label:"File Upload Security",      color:"#10b981"},
  {id:"meeting",    icon:"fa-solid fa-video-shield",      label:"Meeting Security",          color:"#f59e0b"},
  {id:"ai",         icon:"fa-solid fa-robot",             label:"AI Security",               color:"#ec4899"},
  {id:"api",        icon:"fa-solid fa-plug",              label:"API Security",              color:"#6366f1"},
  {id:"database",   icon:"fa-solid fa-database",          label:"Database Security",         color:"#14b8a6"},
  {id:"session",    icon:"fa-solid fa-desktop",           label:"Session Security",          color:"#f97316"},
  {id:"dashboard",  icon:"fa-solid fa-gauge-high",        label:"Security Dashboard",        color:"#ef4444"},
  {id:"logs",       icon:"fa-solid fa-file-lines",        label:"Security Logs",             color:"#84cc16"},
  {id:"audit",      icon:"fa-solid fa-magnifying-glass",  label:"Audit Trail",               color:"#22d3ee"},
  {id:"network",    icon:"fa-solid fa-network-wired",     label:"Network Security",          color:"#e879f9"},
  {id:"notify",     icon:"fa-solid fa-bell",              label:"Notification Security",     color:"#fbbf24"},
  {id:"risk",       icon:"fa-solid fa-triangle-exclamation",label:"Risk Detection",           color:"#f43f5e"},
  {id:"privacy",    icon:"fa-solid fa-eye-slash",         label:"Privacy Controls",          color:"#34d399"},
  {id:"backup",     icon:"fa-solid fa-cloud-arrow-up",    label:"Backup & Recovery",         color:"#38bdf8"},
  {id:"compliance", icon:"fa-solid fa-clipboard-check",   label:"Compliance Features",       color:"#c084fc"},
  {id:"enterprise", icon:"fa-solid fa-building-shield",   label:"Advanced Enterprise",       color:"#fb923c"}
];

var _secState = { activeTab:"auth" };

function h(tag, attrs, children){
  var el = document.createElement(tag);
  if(attrs) Object.keys(attrs).forEach(function(k){
    if(k==="style" && typeof attrs[k]==="object") Object.assign(el.style, attrs[k]);
    else if(k==="onclick") el.onclick = attrs[k];
    else if(k==="className") el.className = attrs[k];
    else el.setAttribute(k, attrs[k]);
  });
  if(typeof children==="string") el.innerHTML = children;
  else if(Array.isArray(children)) children.forEach(function(c){if(c)el.appendChild(c);});
  return el;
}

function _secStats(){
  var log = JSON.parse(localStorage.getItem("echoaction_security_events")||"[]");
  var logins = JSON.parse(localStorage.getItem("echoaction_login_history")||"[]");
  var auditLog = JSON.parse(localStorage.getItem("echoaction_audit_trail")||"[]");
  var secNotifs = JSON.parse(localStorage.getItem("echoaction_security_notifications")||"[]");
  var blockedIPs = JSON.parse(localStorage.getItem("echoaction_blocked_ips")||"[]");
  var sessions = JSON.parse(localStorage.getItem("echoaction_active_sessions")||"[]");
  return {events:log, logins:logins, audit:auditLog, notifs:secNotifs, blockedIPs:blockedIPs, sessions:sessions};
}

function _esc(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}

function _logSecEvent(type, desc, severity){
  var log = JSON.parse(localStorage.getItem("echoaction_security_events")||"[]");
  log.unshift({id:"se"+Date.now(), type:type, description:desc, severity:severity||"info", time:new Date().toISOString(), ip:"127.0.0.1"});
  if(log.length>500) log=log.slice(0,500);
  localStorage.setItem("echoaction_security_events", JSON.stringify(log));
}

function _logAudit(action, module, detail){
  var trail = JSON.parse(localStorage.getItem("echoaction_audit_trail")||"[]");
  trail.unshift({id:"at"+Date.now(), action:action, module:module, detail:detail||"", time:new Date().toISOString(), user:(window.currentUser||{}).email||"admin", ip:"127.0.0.1", device:navigator.userAgent.slice(0,80)});
  if(trail.length>1000) trail=trail.slice(0,1000);
  localStorage.setItem("echoaction_audit_trail", JSON.stringify(trail));
}

function _secCard(icon, num, label, color){
  return '<div style="background:rgba('+color+',0.06);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:0.75rem;text-align:center;"><div style="font-size:1.4rem;font-weight:700;color:'+color+';">'+num+'</div><div style="font-size:0.65rem;color:#8899b0;margin-top:2px;"><i class="'+icon+'" style="margin-right:3px;"></i>'+label+'</div></div>';
}

function _secToggle(label, id, checked, color){
  return '<div style="display:flex;justify-content:space-between;align-items:center;padding:0.55rem 0.75rem;background:rgba(255,255,255,0.03);border-radius:8px;"><span style="font-size:0.82rem;color:#e8edf5;">'+label+'</span><label style="position:relative;width:40px;height:22px;cursor:pointer;"><input type="checkbox" id="'+id+'" '+(checked?'checked':'')+' style="opacity:0;width:0;height:0;" onchange="if(typeof window._secToggle===\'function\')window._secToggle(\''+id+'\',this.checked)"><span style="position:absolute;inset:0;background:'+(checked?color||'#818cf8':'#374151')+';border-radius:22px;transition:0.3s;"></span><span style="position:absolute;top:2px;left:'+(checked?'20px':'2px')+';width:18px;height:18px;background:#fff;border-radius:50%;transition:0.3s;"></span></label></div>';
}

function _secInfoRow(icon, label, value, color){
  return '<div style="display:flex;align-items:center;gap:8px;padding:0.45rem 0;border-bottom:1px solid rgba(255,255,255,0.04);"><div style="width:26px;height:26px;border-radius:6px;background:rgba('+color+',0.1);display:flex;align-items:center;justify-content:center;flex-shrink:0;"><i class="'+icon+'" style="color:'+color+';font-size:0.6rem;"></i></div><span style="flex:1;font-size:0.78rem;color:#c8d0dc;">'+label+'</span><span style="font-size:0.72rem;color:#8899b0;">'+value+'</span></div>';
}

/* ─── MODULE CONTENT GENERATORS ─────────────────────────────────────────────── */

var _modContent = {};

_modContent.auth = function(s){
  return '<div style="display:flex;flex-direction:column;gap:0.75rem;">'+
    '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.6rem;">'+
      _secCard("fa-solid fa-key","Active","Password Policy","#818cf8")+
      _secCard("fa-solid fa-shield","Enabled","2FA","#10b981")+
      _secCard("fa-solid fa-lock","3","Failed Login Attempts","#f59e0b")+
      _secCard("fa-solid fa-user-lock","0","Locked Accounts","#ef4444")+
    '</div>'+
    '<div style="background:rgba(15,22,42,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:1rem;">'+
      '<div style="font-size:0.75rem;color:#818cf8;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;"><i class="fa-solid fa-key" style="margin-right:4px;"></i> Authentication Settings</div>'+
      _secToggle("Strong Password Policy","sec-auth-strong-pwd",true,"#818cf8")+
      _secToggle("Password Confirmation on Registration","sec-auth-pwd-confirm",true,"#10b981")+
      _secToggle("Password Hashing (bcrypt/scrypt)","sec-auth-pwd-hash",true,"#06b6d4")+
      _secToggle("Two-Factor Authentication (2FA)","sec-auth-2fa",true,"#8b5cf6")+
      _secToggle("CAPTCHA After Failed Attempts","sec-auth-captcha",true,"#f59e0b")+
      _secToggle("Remember Me (Secure Cookies)","sec-auth-remember",true,"#10b981")+
      _secToggle("Automatic Logout After Inactivity","sec-auth-auto-logout",true,"#ef4444")+
      _secToggle("Single Session Control","sec-auth-single-session",false,"#f97316")+
      _secToggle("Force Logout From All Devices","sec-auth-force-logout",false,"#ec4899")+
    '</div>'+
    '<div style="background:rgba(15,22,42,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:1rem;">'+
      '<div style="font-size:0.75rem;color:#f59e0b;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;"><i class="fa-solid fa-clock" style="margin-right:4px;"></i> Login Attempt Limits</div>'+
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.6rem;">'+
        '<div style="background:rgba(15,22,42,0.4);border:1px solid rgba(255,255,255,0.04);border-radius:8px;padding:0.6rem;"><div style="font-size:0.62rem;color:#6b7a8a;">Max Attempts Before Lock</div><div style="font-size:1.1rem;font-weight:700;color:#f59e0b;">5</div></div>'+
        '<div style="background:rgba(15,22,42,0.4);border:1px solid rgba(255,255,255,0.04);border-radius:8px;padding:0.6rem;"><div style="font-size:0.62rem;color:#6b7a8a;">Lock Duration</div><div style="font-size:1.1rem;font-weight:700;color:#ef4444;">30 min</div></div>'+
        '<div style="background:rgba(15,22,42,0.4);border:1px solid rgba(255,255,255,0.04);border-radius:8px;padding:0.6rem;"><div style="font-size:0.62rem;color:#6b7a8a;">Password Reset Expiry</div><div style="font-size:1.1rem;font-weight:700;color:#818cf8;">24 hrs</div></div>'+
        '<div style="background:rgba(15,22,42,0.4);border:1px solid rgba(255,255,255,0.04);border-radius:8px;padding:0.6rem;"><div style="font-size:0.62rem;color:#6b7a8a;">Temporary Lock After</div><div style="font-size:1.1rem;font-weight:700;color:#ec4899;">3 fails</div></div>'+
      '</div>'+
    '</div>'+
    '<div style="background:rgba(15,22,42,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:1rem;">'+
      '<div style="font-size:0.75rem;color:#10b981;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;"><i class="fa-solid fa-envelope" style="margin-right:4px;"></i> Password Reset & Email Verification</div>'+
      _secToggle("Email Verification on Registration","sec-auth-email-verify",true,"#10b981")+
      _secToggle("Forgot Password With Email","sec-auth-forgot-pwd",true,"#06b6d4")+
      _secToggle("Reset Token Expiration","sec-auth-reset-expire",true,"#f59e0b")+
      _secToggle("Change Password Requirement","sec-auth-change-pwd",true,"#818cf8")+
    '</div>'+
  '</div>';
};

_modContent.account = function(s){
  var logins = s.logins.slice(0,20);
  return '<div style="display:flex;flex-direction:column;gap:0.75rem;">'+
    '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.6rem;">'+
      _secCard("fa-solid fa-right-to-bracket",s.logins.length,"Total Logins","#06b6d4")+
      _secCard("fa-solid fa-desktop",Math.min(s.sessions.length||3,99),"Active Sessions","#818cf8")+
      _secCard("fa-solid fa-shield","#5","Security Score","#10b981")+
      _secCard("fa-solid fa-circle-exclamation",s.events.filter(function(e){return e.severity==='critical';}).length,"Critical Events","#ef4444")+
    '</div>'+
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;">'+
      '<div style="background:rgba(15,22,42,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:1rem;">'+
        '<div style="font-size:0.75rem;color:#06b6d4;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;"><i class="fa-solid fa-right-to-bracket" style="margin-right:4px;"></i> Last Login Details</div>'+
        _secInfoRow("fa-solid fa-clock","Last Login","Today, 10:32 AM","#06b6d4")+
        _secInfoRow("fa-solid fa-globe","IP Address","192.168.1.105","#818cf8")+
        _secInfoRow("fa-solid fa-desktop","Device","Chrome 120 / Windows 11","#10b981")+
        _secInfoRow("fa-solid fa-map-marker","Location","Hyderabad, India","#f59e0b")+
      '</div>'+
      '<div style="background:rgba(15,22,42,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:1rem;">'+
        '<div style="font-size:0.75rem;color:#818cf8;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;"><i class="fa-solid fa-desktop" style="margin-right:4px;"></i> Active Sessions</div>'+
        _secInfoRow("fa-solid fa-chrome","Chrome / Windows","Current Session","#10b981")+
        _secInfoRow("fa-solid fa-firefox","Firefox / macOS","2 hours ago","#f59e0b")+
        _secInfoRow("fa-solid fa-mobile","Safari / iOS","Yesterday","#818cf8")+
      '</div>'+
    '</div>'+
    '<div style="background:rgba(15,22,42,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:1rem;">'+
      '<div style="font-size:0.75rem;color:#f59e0b;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;"><i class="fa-solid fa-clock-rotate-left" style="margin-right:4px;"></i> Login History (Recent 10)</div>'+
      (logins.length?logins.slice(0,10).map(function(l){
        var dt=new Date(l.time||l.timestamp||Date.now());
        var success=l.success!==false;
        return '<div style="display:flex;align-items:center;gap:8px;padding:0.4rem 0.5rem;border-bottom:1px solid rgba(255,255,255,0.04);font-size:0.75rem;"><div style="width:6px;height:6px;border-radius:50%;background:'+(success?'#10b981':'#ef4444')+';flex-shrink:0;"></div><span style="flex:1;color:#c8d0dc;">'+_esc(l.email||l.user||'Unknown')+'</span><span style="color:#8899b0;">'+dt.toLocaleString()+'</span><span style="color:'+(success?'#10b981':'#ef4444')+';font-weight:600;">'+(success?'Success':'Failed')+'</span></div>';
      }).join(''):'<div style="text-align:center;color:#6b7a99;padding:1rem;font-size:0.75rem;">No login history yet</div>')+
    '</div>'+
    '<div style="background:rgba(15,22,42,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:1rem;">'+
      '<div style="font-size:0.75rem;color:#10b981;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;"><i class="fa-solid fa-shield" style="margin-right:4px;"></i> Device Management</div>'+
      '<div style="display:flex;gap:8px;flex-wrap:wrap;">'+
        '<div style="flex:1;min-width:180px;background:rgba(16,185,129,0.06);border:1px solid rgba(16,185,129,0.15);border-radius:8px;padding:0.6rem;"><div style="font-size:0.72rem;color:#10b981;font-weight:600;">Trusted Devices</div><div style="font-size:1.1rem;font-weight:700;color:#e8edf5;">2</div></div>'+
        '<div style="flex:1;min-width:180px;background:rgba(245,158,11,0.06);border:1px solid rgba(245,158,11,0.15);border-radius:8px;padding:0.6rem;"><div style="font-size:0.72rem;color:#f59e0b;font-weight:600;">Unknown Devices</div><div style="font-size:1.1rem;font-weight:700;color:#e8edf5;">1</div></div>'+
        '<div style="flex:1;min-width:180px;background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.15);border-radius:8px;padding:0.6rem;"><div style="font-size:0.72rem;color:#ef4444;font-weight:600;">Blocked Devices</div><div style="font-size:1.1rem;font-weight:700;color:#e8edf5;">0</div></div>'+
      '</div>'+
    '</div>'+
  '</div>';
};

_modContent.rbac = function(s){
  var roles = [{name:"Employee",color:"#818cf8",perms:["Own Meetings","Own Projects","Own Tasks","Own Reports"]},{name:"Student",color:"#06b6d4",perms:["Class Meetings","Notes","Assignments"]},{name:"Staff",color:"#f59e0b",perms:["Employee Management","Meeting Approval","Department Management"]},{name:"Admin",color:"#ef4444",perms:["User Management","Security Settings","System Settings","Audit Logs","Permission Management"]}];
  return '<div style="display:flex;flex-direction:column;gap:0.75rem;">'+
    '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.6rem;">'+
      _secCard("fa-solid fa-users-gear",roles.length,"Role Definitions","#818cf8")+
      _secCard("fa-solid fa-user",registeredUsers?registeredUsers.length:0,"Total Users","#10b981")+
      _secCard("fa-solid fa-shield","4","Permission Levels","#f59e0b")+
      _secCard("fa-solid fa-check-double","Active","RBAC Status","#10b981")+
    '</div>'+
    '<div style="background:rgba(15,22,42,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:1rem;">'+
      '<div style="font-size:0.75rem;color:#818cf8;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;"><i class="fa-solid fa-users-gear" style="margin-right:4px;"></i> Role Definitions & Access Levels</div>'+
      roles.map(function(r){
        return '<div style="display:flex;align-items:center;gap:10px;padding:0.6rem 0.75rem;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.04);border-radius:8px;margin-bottom:0.4rem;">'+
          '<div style="width:32px;height:32px;border-radius:8px;background:'+r.color+'20;display:flex;align-items:center;justify-content:center;flex-shrink:0;"><div style="width:10px;height:10px;border-radius:50%;background:'+r.color+';"></div></div>'+
          '<div style="flex:1;"><div style="font-size:0.82rem;color:#e8edf5;font-weight:600;">'+r.name+'</div><div style="font-size:0.65rem;color:#8899b0;margin-top:2px;">'+r.perms.join(' · ')+'</div></div>'+
          '<div style="font-size:0.68rem;color:#8899b0;">'+(registeredUsers?registeredUsers.filter(function(u){return u.portal===r.name.toLowerCase()||(r.name==='Employee'&&u.portal==='employee');}).length:0)+' users</div>'+
        '</div>';
      }).join('')+
    '</div>'+
  '</div>';
};

_modContent.perm = function(s){
  var perms = ["Create","Read","Update","Delete","Export","Upload","Download","Approve","Reject","Share","AI Access","Analytics Access","Meeting Access"];
  var modules = ["Meetings","Projects","Tasks","Reports","Users","Settings","Analytics"];
  return '<div style="display:flex;flex-direction:column;gap:0.75rem;">'+
    '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.6rem;">'+
      _secCard("fa-solid fa-lock",perms.length,"Permission Types","#818cf8")+
      _secCard("fa-solid fa-layer-group",modules.length,"Protected Modules","#f59e0b")+
      _secCard("fa-solid fa-check","Active","Permission System","#10b981")+
    '</div>'+
    '<div style="background:rgba(15,22,42,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:1rem;overflow-x:auto;">'+
      '<div style="font-size:0.75rem;color:#818cf8;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;"><i class="fa-solid fa-lock" style="margin-right:4px;"></i> Permission Matrix</div>'+
      '<table style="width:100%;border-collapse:collapse;font-size:0.7rem;">'+
      '<tr><th style="text-align:left;padding:6px 8px;color:#8899b0;border-bottom:1px solid rgba(255,255,255,0.08);">Module</th>'+
      perms.slice(0,8).map(function(p){return '<th style="text-align:center;padding:6px 4px;color:#8899b0;border-bottom:1px solid rgba(255,255,255,0.08);">'+p+'</th>';}).join('')+'</tr>'+
      modules.map(function(m){
        return '<tr><td style="padding:6px 8px;color:#e8edf5;border-bottom:1px solid rgba(255,255,255,0.04);">'+m+'</td>'+
          perms.slice(0,8).map(function(p){
            var has = m==="Settings"?p==="Read":(p!=="Delete"||m==="Tasks");
            return '<td style="text-align:center;padding:6px 4px;border-bottom:1px solid rgba(255,255,255,0.04);"><input type="checkbox" '+(has?'checked':'')+' style="accent-color:#818cf8;width:14px;height:14px;cursor:pointer;"></td>';
          }).join('')+'</tr>';
      }).join('')+'</table>'+
    '</div>'+
  '</div>';
};

_modContent.upload = function(s){
  var features = [
    {name:"File Extension Whitelist",status:true,icon:"fa-solid fa-file-code"},
    {name:"MIME Type Verification",status:true,icon:"fa-solid fa-fingerprint"},
    {name:"Maximum File Size (50MB)",status:true,icon:"fa-solid fa-weight-hanging"},
    {name:"Duplicate Detection",status:true,icon:"fa-solid fa-copy"},
    {name:"File Name Validation",status:true,icon:"fa-solid fa-font"},
    {name:"Executable File Blocking",status:true,icon:"fa-solid fa-ban"},
    {name:"Dangerous File Blocking",status:true,icon:"fa-solid fa-skull-crossbones"},
    {name:"Automatic File Renaming",status:false,icon:"fa-solid fa-pen"},
    {name:"Upload History",status:true,icon:"fa-solid fa-clock-rotate-left"}
  ];
  return '<div style="display:flex;flex-direction:column;gap:0.75rem;">'+
    '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.6rem;">'+
      _secCard("fa-solid fa-file-shield",features.filter(function(f){return f.status;}).length,"Active Protections","#10b981")+
      _secCard("fa-solid fa-ban",".exe,.bat,.cmd,.msi","Blocked Extensions","#ef4444")+
      _secCard("fa-solid fa-weight-hanging","50MB","Max File Size","#f59e0b")+
    '</div>'+
    '<div style="background:rgba(15,22,42,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:1rem;">'+
      '<div style="font-size:0.75rem;color:#10b981;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;"><i class="fa-solid fa-file-shield" style="margin-right:4px;"></i> Upload Security Controls</div>'+
      features.map(function(f){
        return '<div style="display:flex;align-items:center;gap:8px;padding:0.5rem 0.6rem;border-bottom:1px solid rgba(255,255,255,0.04);"><i class="'+f.icon+'" style="color:'+(f.status?'#10b981':'#6b7a8a')+';width:20px;text-align:center;font-size:0.72rem;"></i><span style="flex:1;font-size:0.8rem;color:#e8edf5;">'+f.name+'</span><span style="font-size:0.65rem;padding:0.15rem 0.5rem;border-radius:12px;background:'+(f.status?'rgba(16,185,129,0.12)':'rgba(107,122,138,0.12)')+';color:'+(f.status?'#10b981':'#6b7a8a')+';font-weight:600;">'+(f.status?'Enabled':'Disabled')+'</span></div>';
      }).join('')+
    '</div>'+
  '</div>';
};

_modContent.meeting = function(s){
  var features = ["Private Meetings","Password Protected Meetings","Waiting Room","Host Approval","Participant Verification","Screen Sharing Permissions","Recording Permissions","Download Permissions","Transcript Permissions","AI Summary Permissions"];
  return '<div style="display:flex;flex-direction:column;gap:0.75rem;">'+
    '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.6rem;">'+
      _secCard("fa-solid fa-video-shield",features.filter(function(f,i){return i<7;}).length,"Active Policies","#f59e0b")+
      _secCard("fa-solid fa-lock","Enabled","Meeting Privacy","#10b981")+
      _secCard("fa-solid fa-user-check","Verified","Participant Check","#06b6d4")+
      _secCard("fa-solid fa-record-vinyl","Restricted","Recording Access","#818cf8")+
    '</div>'+
    '<div style="background:rgba(15,22,42,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:1rem;">'+
      '<div style="font-size:0.75rem;color:#f59e0b;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;"><i class="fa-solid fa-video-shield" style="margin-right:4px;"></i> Meeting Security Policies</div>'+
      features.map(function(f,i){
        return _secToggle(f,"sec-meet-"+i,i<7,"#f59e0b");
      }).join('')+
    '</div>'+
  '</div>';
};

_modContent.ai = function(s){
  var features = [
    {name:"Prompt Validation & Filtering",status:true},
    {name:"AI Request Rate Limiting",status:true},
    {name:"AI Abuse Detection",status:true},
    {name:"Sensitive Data Masking",status:true},
    {name:"AI Usage History Logging",status:true},
    {name:"AI Access Permissions",status:true},
    {name:"AI Audit Logs",status:true},
    {name:"AI Token Monitoring",status:true}
  ];
  return '<div style="display:flex;flex-direction:column;gap:0.75rem;">'+
    '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.6rem;">'+
      _secCard("fa-solid fa-robot",features.filter(function(f){return f.status;}).length,"Active Safeguards","#ec4899")+
      _secCard("fa-solid fa-gauge","100/hr","Request Limit","#f59e0b")+
      _secCard("fa-solid fa-mask","Active","Data Masking","#818cf8")+
      _secCard("fa-solid fa-chart-line","1.2k","Tokens Used Today","#06b6d4")+
    '</div>'+
    '<div style="background:rgba(15,22,42,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:1rem;">'+
      '<div style="font-size:0.75rem;color:#ec4899;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;"><i class="fa-solid fa-robot" style="margin-right:4px;"></i> AI Security Controls</div>'+
      features.map(function(f,i){
        return _secToggle(f.name,"sec-ai-"+i,f.status,"#ec4899");
      }).join('')+
    '</div>'+
  '</div>';
};

_modContent.api = function(s){
  var features = [
    {name:"Authentication Required",status:true},
    {name:"Authorization Checks",status:true},
    {name:"API Rate Limiting (60 req/min)",status:true},
    {name:"Token Expiration (1hr)",status:true},
    {name:"Invalid Token Detection",status:true},
    {name:"API Request Logging",status:true},
    {name:"Request/Response Validation",status:true},
    {name:"Secure Headers",status:true},
    {name:"API Version Control",status:true}
  ];
  return '<div style="display:flex;flex-direction:column;gap:0.75rem;">'+
    '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.6rem;">'+
      _secCard("fa-solid fa-plug",features.filter(function(f){return f.status;}).length,"Active Protections","#6366f1")+
      _secCard("fa-solid fa-gauge","60/min","Rate Limit","#f59e0b")+
      _secCard("fa-solid fa-clock","60 min","Token TTL","#818cf8")+
    '</div>'+
    '<div style="background:rgba(15,22,42,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:1rem;">'+
      '<div style="font-size:0.75rem;color:#6366f1;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;"><i class="fa-solid fa-plug" style="margin-right:4px;"></i> API Security Settings</div>'+
      features.map(function(f,i){
        return _secToggle(f.name,"sec-api-"+i,f.status,"#6366f1");
      }).join('')+
    '</div>'+
  '</div>';
};

_modContent.database = function(s){
  var features = [
    {name:"Encrypted Passwords (bcrypt)",status:true},
    {name:"Sensitive Data Encryption (Fernet)",status:true},
    {name:"Database Backups",status:true},
    {name:"Backup Encryption",status:true},
    {name:"Restore System",status:true},
    {name:"Database Activity Logs",status:true},
    {name:"Database Integrity Checks",status:true},
    {name:"Secure Connections (SSL)",status:true},
    {name:"Query Monitoring",status:true}
  ];
  return '<div style="display:flex;flex-direction:column;gap:0.75rem;">'+
    '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.6rem;">'+
      _secCard("fa-solid fa-database",features.filter(function(f){return f.status;}).length,"Active Measures","#14b8a6")+
      _secCard("fa-solid fa-lock","AES-256","Encryption","#10b981")+
      _secCard("fa-solid fa-clock","Daily","Backup Schedule","#f59e0b")+
    '</div>'+
    '<div style="background:rgba(15,22,42,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:1rem;">'+
      '<div style="font-size:0.75rem;color:#14b8a6;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;"><i class="fa-solid fa-database" style="margin-right:4px;"></i> Database Security Controls</div>'+
      features.map(function(f,i){
        return _secToggle(f.name,"sec-db-"+i,f.status,"#14b8a6");
      }).join('')+
    '</div>'+
  '</div>';
};

_modContent.session = function(s){
  var features = [
    {name:"Secure Cookies",status:true},
    {name:"HTTP Only Cookies",status:true},
    {name:"SameSite Cookies",status:true},
    {name:"Session Timeout (30 min)",status:true},
    {name:"Session Renewal on Activity",status:true},
    {name:"Session Expiration",status:true},
    {name:"Logout Everywhere",status:true},
    {name:"Session Monitoring",status:true}
  ];
  return '<div style="display:flex;flex-direction:column;gap:0.75rem;">'+
    '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.6rem;">'+
      _secCard("fa-solid fa-desktop",features.filter(function(f){return f.status;}).length,"Active Controls","#f97316")+
      _secCard("fa-solid fa-clock","30 min","Session Timeout","#f59e0b")+
      _secCard("fa-solid fa-cookie","Secure","Cookie Policy","#10b981")+
      _secCard("fa-solid fa-desktop",s.sessions.length||0,"Active Sessions","#818cf8")+
    '</div>'+
    '<div style="background:rgba(15,22,42,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:1rem;">'+
      '<div style="font-size:0.75rem;color:#f97316;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;"><i class="fa-solid fa-desktop" style="margin-right:4px;"></i> Session Security Settings</div>'+
      features.map(function(f,i){
        return _secToggle(f.name,"sec-sess-"+i,f.status,"#f97316");
      }).join('')+
    '</div>'+
  '</div>';
};

_modContent.dashboard = function(s){
  var logins24h = s.logins.filter(function(l){return (Date.now()-new Date(l.time||l.timestamp||0))<86400000;});
  var blocked24h = s.events.filter(function(e){return e.severity==='blocked'||e.blocked;}).length;
  return '<div style="display:flex;flex-direction:column;gap:0.75rem;">'+
    '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.6rem;">'+
      _secCard("fa-solid fa-users",registeredUsers?registeredUsers.length:0,"Active Users","#818cf8")+
      _secCard("fa-solid fa-right-to-bracket",logins24h.length,"Logins Today","#10b981")+
      _secCard("fa-solid fa-ban",blocked24h,"Blocked Attempts","#ef4444")+
      _secCard("fa-solid fa-shield","#85","Security Score","#06b6d4")+
    '</div>'+
    '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.6rem;">'+
      _secCard("fa-solid fa-skull-crossbones",s.events.filter(function(e){return e.severity==='critical';}).length,"Suspicious Activities","#f43f5e")+
      _secCard("fa-solid fa-ban",s.blockedIPs.length,"Blocked IPs","#ef4444")+
      _secCard("fa-solid fa-bell",s.notifs.length,"Security Alerts","#f59e0b")+
      _secCard("fa-solid fa-file-arrow-up","0","Upload Stats","#10b981")+
    '</div>'+
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;">'+
      '<div style="background:rgba(15,22,42,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:1rem;">'+
        '<div style="font-size:0.75rem;color:#ef4444;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;"><i class="fa-solid fa-skull-crossbones" style="margin-right:4px;"></i> Threat Overview</div>'+
        _secInfoRow("fa-solid fa-triangle-exclamation","Failed Login Attempts (24h)",logins24h.filter(function(l){return l.success===false;}).length||0,"#f59e0b")+
        _secInfoRow("fa-solid fa-ban","Blocked Requests",blocked24h,"#ef4444")+
        _secInfoRow("fa-solid fa-shield","Firewall Status","Active","#10b981")+
        _secInfoRow("fa-solid fa-gauge","Rate Limit","60 req/min","#818cf8")+
      '</div>'+
      '<div style="background:rgba(15,22,42,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:1rem;">'+
        '<div style="font-size:0.75rem;color:#818cf8;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;"><i class="fa-solid fa-chart-line" style="margin-right:4px;"></i> Security Recommendations</div>'+
        ['Enable HTTPS in production','Rotate encryption keys monthly','Review user permissions quarterly','Enable audit logging for all admin actions','Set up automated backup verification'].map(function(r,i){
          return '<div style="display:flex;align-items:center;gap:6px;padding:0.35rem 0;border-bottom:1px solid rgba(255,255,255,0.04);"><div style="width:18px;height:18px;border-radius:4px;background:rgba(245,158,11,0.12);display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:0.55rem;color:#f59e0b;">'+(i+1)+'</div><span style="font-size:0.75rem;color:#c8d0dc;">'+r+'</span></div>';
        }).join('')+
      '</div>'+
    '</div>'+
  '</div>';
};

_modContent.logs = function(s){
  var recent = s.events.slice(0,20);
  var sevColors = {critical:"#ef4444",high:"#f59e0b",medium:"#818cf8",low:"#10b981",info:"#6b7a8a",blocked:"#ef4444"};
  return '<div style="display:flex;flex-direction:column;gap:0.75rem;">'+
    '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.6rem;">'+
      _secCard("fa-solid fa-file-lines",s.events.length,"Total Events","#84cc16")+
      _secCard("fa-solid fa-clock",s.events.filter(function(e){return (Date.now()-new Date(e.time||e.timestamp||0))<86400000;}).length,"Last 24 Hours","#06b6d4")+
      _secCard("fa-solid fa-ban",s.events.filter(function(e){return e.severity==='critical'||e.severity==='blocked';}).length,"Critical/Blocked","#ef4444")+
    '</div>'+
    '<div style="background:rgba(15,22,42,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:1rem;max-height:400px;overflow-y:auto;">'+
      '<div style="font-size:0.75rem;color:#84cc16;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;"><i class="fa-solid fa-file-lines" style="margin-right:4px;"></i> Security Event Log</div>'+
      (recent.length?recent.map(function(e){
        var dt=new Date(e.time||e.timestamp||Date.now());
        var clr=sevColors[e.severity]||'#6b7a8a';
        return '<div style="display:flex;align-items:flex-start;gap:8px;padding:0.45rem 0.5rem;border-bottom:1px solid rgba(255,255,255,0.04);"><div style="width:6px;height:6px;border-radius:50%;background:'+clr+';flex-shrink:0;margin-top:5px;"></div><div style="flex:1;min-width:0;"><div style="font-size:0.75rem;color:#e8edf5;">'+_esc(e.description||e.event||'Event')+'</div><div style="font-size:0.62rem;color:#8899b0;margin-top:2px;">'+dt.toLocaleString()+' · '+_esc(e.severity||'info')+'</div></div></div>';
      }).join(''):'<div style="text-align:center;color:#6b7a99;padding:2rem;">No security events logged yet</div>')+
    '</div>'+
  '</div>';
};

_modContent.audit = function(s){
  var trail = s.audit.slice(0,20);
  return '<div style="display:flex;flex-direction:column;gap:0.75rem;">'+
    '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.6rem;">'+
      _secCard("fa-solid fa-magnifying-glass",s.audit.length,"Audit Entries","#22d3ee")+
      _secCard("fa-solid fa-clock",s.audit.filter(function(e){return (Date.now()-new Date(e.time||0))<86400000;}).length,"Today","#06b6d4")+
      _secCard("fa-solid fa-user","Admin","Last Action By","#818cf8")+
    '</div>'+
    '<div style="background:rgba(15,22,42,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:1rem;max-height:400px;overflow-y:auto;">'+
      '<div style="font-size:0.75rem;color:#22d3ee;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;"><i class="fa-solid fa-magnifying-glass" style="margin-right:4px;"></i> Audit Trail</div>'+
      (trail.length?trail.map(function(e){
        var dt=new Date(e.time||Date.now());
        return '<div style="display:flex;align-items:center;gap:8px;padding:0.45rem 0.5rem;border-bottom:1px solid rgba(255,255,255,0.04);"><div style="width:24px;height:24px;border-radius:6px;background:rgba(34,211,238,0.1);display:flex;align-items:center;justify-content:center;flex-shrink:0;"><i class="fa-solid fa-circle" style="color:#22d3ee;font-size:0.3rem;"></i></div><div style="flex:1;min-width:0;"><div style="font-size:0.75rem;color:#e8edf5;">'+_esc(e.action||'Action')+' <span style="color:#8899b0;font-size:0.65rem;">on '+_esc(e.module||'system')+'</span></div><div style="font-size:0.62rem;color:#8899b0;margin-top:2px;">'+dt.toLocaleString()+' · '+_esc(e.user||'admin')+' · '+_esc(e.ip||'127.0.0.1')+'</div></div></div>';
      }).join(''):'<div style="text-align:center;color:#6b7a99;padding:2rem;">No audit entries yet</div>')+
    '</div>'+
  '</div>';
};

_modContent.network = function(s){
  var features = [
    {name:"HTTPS Enforcement",status:true},
    {name:"Security Headers (HSTS, CSP, X-Frame)",status:true},
    {name:"Content Security Policy",status:true},
    {name:"Referrer Policy",status:true},
    {name:"X-Frame Protection",status:true},
    {name:"MIME Type Protection",status:true},
    {name:"CORS Configuration",status:true},
    {name:"Request Validation",status:true}
  ];
  return '<div style="display:flex;flex-direction:column;gap:0.75rem;">'+
    '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.6rem;">'+
      _secCard("fa-solid fa-network-wired",features.filter(function(f){return f.status;}).length,"Active Headers","#e879f9")+
      _secCard("fa-solid fa-shield","Enabled","Firewall","#10b981")+
      _secCard("fa-solid fa-ban",s.blockedIPs.length,"Blocked IPs","#ef4444")+
    '</div>'+
    '<div style="background:rgba(15,22,42,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:1rem;">'+
      '<div style="font-size:0.75rem;color:#e879f9;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;"><i class="fa-solid fa-network-wired" style="margin-right:4px;"></i> Network Security Controls</div>'+
      features.map(function(f,i){
        return _secToggle(f.name,"sec-net-"+i,f.status,"#e879f9");
      }).join('')+
    '</div>'+
  '</div>';
};

_modContent.notify = function(s){
  var events = ["New Login","Unknown Device","Password Changed","Email Changed","Profile Updated","Permission Changed","Meeting Shared","Account Locked","Suspicious Login","Security Alert"];
  return '<div style="display:flex;flex-direction:column;gap:0.75rem;">'+
    '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.6rem;">'+
      _secCard("fa-solid fa-bell",events.length,"Notification Types","#fbbf24")+
      _secCard("fa-solid fa-check","All","Active Channels","#10b981")+
      _secCard("fa-solid fa-clock",s.notifs.length,"Pending Alerts","#f59e0b")+
    '</div>'+
    '<div style="background:rgba(15,22,42,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:1rem;">'+
      '<div style="font-size:0.75rem;color:#fbbf24;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;"><i class="fa-solid fa-bell" style="margin-right:4px;"></i> Security Notification Events</div>'+
      events.map(function(f,i){
        return _secToggle(f,"sec-notify-"+i,true,"#fbbf24");
      }).join('')+
    '</div>'+
  '</div>';
};

_modContent.risk = function(s){
  var risks = [
    {name:"Multiple Failed Logins",status:true,sev:"high"},
    {name:"Login From Unknown Device",status:true,sev:"medium"},
    {name:"Login From Different Country",status:true,sev:"medium"},
    {name:"Large Number of AI Requests",status:true,sev:"low"},
    {name:"Large File Uploads",status:true,sev:"low"},
    {name:"Multiple Password Reset Requests",status:true,sev:"high"},
    {name:"Rapid API Requests",status:true,sev:"medium"},
    {name:"Unauthorized Access Attempts",status:true,sev:"high"}
  ];
  var sevColors={high:"#ef4444",medium:"#f59e0b",low:"#10b981"};
  return '<div style="display:flex;flex-direction:column;gap:0.75rem;">'+
    '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.6rem;">'+
      _secCard("fa-solid fa-triangle-exclamation",risks.filter(function(f){return f.status;}).length,"Active Detectors","#f43f5e")+
      _secCard("fa-solid fa-high",risks.filter(function(f){return f.sev==='high';}).length,"High Risk Rules","#ef4444")+
      _secCard("fa-solid fa-shield","Monitoring","Detection Status","#10b981")+
    '</div>'+
    '<div style="background:rgba(15,22,42,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:1rem;">'+
      '<div style="font-size:0.75rem;color:#f43f5e;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;"><i class="fa-solid fa-triangle-exclamation" style="margin-right:4px;"></i> Risk Detection Rules</div>'+
      risks.map(function(f,i){
        return '<div style="display:flex;align-items:center;gap:8px;padding:0.5rem 0.6rem;border-bottom:1px solid rgba(255,255,255,0.04);">'+
          '<span style="font-size:0.6rem;padding:0.1rem 0.4rem;border-radius:8px;background:rgba('+sevColors[f.sev].replace('#','')+',0.15);color:'+sevColors[f.sev]+';font-weight:600;text-transform:uppercase;">'+f.sev+'</span>'+
          '<span style="flex:1;font-size:0.8rem;color:#e8edf5;">'+f.name+'</span>'+
          '<label style="position:relative;width:36px;height:20px;cursor:pointer;"><input type="checkbox" '+(f.status?'checked':'')+' style="opacity:0;width:0;height:0;"><span style="position:absolute;inset:0;background:'+(f.status?f.sev==='high'?'#ef4444':f.sev==='medium'?'#f59e0b':'#10b981':'#374151')+';border-radius:20px;transition:0.3s;"></span><span style="position:absolute;top:2px;left:'+(f.status?'18px':'2px')+';width:16px;height:16px;background:#fff;border-radius:50%;transition:0.3s;"></span></label>'+
        '</div>';
      }).join('')+
    '</div>'+
  '</div>';
};

_modContent.privacy = function(s){
  var features = [
    {name:"Download Personal Data",status:true},
    {name:"Delete Account Request",status:true},
    {name:"Data Sharing Permissions",status:true},
    {name:"AI Data Usage Consent",status:true},
    {name:"Meeting Privacy Settings",status:true},
    {name:"Profile Visibility Control",status:true},
    {name:"Notification Preferences",status:true}
  ];
  return '<div style="display:flex;flex-direction:column;gap:0.75rem;">'+
    '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.6rem;">'+
      _secCard("fa-solid fa-eye-slash",features.filter(function(f){return f.status;}).length,"Privacy Controls","#34d399")+
      _secCard("fa-solid fa-user","GDPR","Compliance","#818cf8")+
      _secCard("fa-solid fa-shield","Active","Protection","#10b981")+
    '</div>'+
    '<div style="background:rgba(15,22,42,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:1rem;">'+
      '<div style="font-size:0.75rem;color:#34d399;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;"><i class="fa-solid fa-eye-slash" style="margin-right:4px;"></i> Privacy Controls</div>'+
      features.map(function(f,i){
        return _secToggle(f.name,"sec-priv-"+i,f.status,"#34d399");
      }).join('')+
    '</div>'+
  '</div>';
};

_modContent.backup = function(s){
  var features = [
    {name:"Automatic Backups",status:true,schedule:"Daily at 3:00 AM"},
    {name:"Manual Backups",status:true,schedule:"On-demand"},
    {name:"Incremental Backups",status:true,schedule:"Every 6 hours"},
    {name:"Backup History",status:true,schedule:"Last 30 days"},
    {name:"Restore Backups",status:true,schedule:"Available"},
    {name:"Backup Verification",status:true,schedule:"Weekly"},
    {name:"Disaster Recovery Plan",status:true,schedule:"Active"}
  ];
  return '<div style="display:flex;flex-direction:column;gap:0.75rem;">'+
    '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.6rem;">'+
      _secCard("fa-solid fa-cloud-arrow-up",features.filter(function(f){return f.status;}).length,"Active Features","#38bdf8")+
      _secCard("fa-solid fa-clock","Daily","Last Backup","#10b981")+
      _secCard("fa-solid fa-hard-drive","1.2 GB","Backup Size","#818cf8")+
      _secCard("fa-solid fa-check","Verified","Integrity","#10b981")+
    '</div>'+
    '<div style="background:rgba(15,22,42,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:1rem;">'+
      '<div style="font-size:0.75rem;color:#38bdf8;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;"><i class="fa-solid fa-cloud-arrow-up" style="margin-right:4px;"></i> Backup & Recovery Settings</div>'+
      features.map(function(f,i){
        return '<div style="display:flex;align-items:center;gap:8px;padding:0.5rem 0.6rem;border-bottom:1px solid rgba(255,255,255,0.04);"><i class="fa-solid fa-check-circle" style="color:#10b981;width:20px;text-align:center;font-size:0.72rem;"></i><span style="flex:1;font-size:0.8rem;color:#e8edf5;">'+f.name+'</span><span style="font-size:0.65rem;color:#8899b0;">'+f.schedule+'</span></div>';
      }).join('')+
      '<div style="margin-top:0.75rem;display:flex;gap:8px;"><button style="padding:0.4rem 0.8rem;background:rgba(56,189,248,0.12);border:1px solid rgba(56,189,248,0.2);color:#38bdf8;border-radius:8px;cursor:pointer;font-size:0.72rem;font-weight:600;" onclick="showToast(\'Backup initiated!\',\'success\')"><i class="fa-solid fa-cloud-arrow-up"></i> Create Backup Now</button><button style="padding:0.4rem 0.8rem;background:rgba(245,158,11,0.12);border:1px solid rgba(245,158,11,0.2);color:#f59e0b;border-radius:8px;cursor:pointer;font-size:0.72rem;font-weight:600;" onclick="showToast(\'Verification started\',\'info\')"><i class="fa-solid fa-check-double"></i> Verify Backups</button></div>'+
    '</div>'+
  '</div>';
};

_modContent.compliance = function(s){
  var features = [
    {name:"Consent Management",status:true},
    {name:"Data Retention Policies",status:true},
    {name:"User Data Export",status:true},
    {name:"User Data Deletion",status:true},
    {name:"Audit Compliance Reports",status:true},
    {name:"Access Review Reports",status:true},
    {name:"Security Compliance Dashboard",status:true}
  ];
  return '<div style="display:flex;flex-direction:column;gap:0.75rem;">'+
    '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.6rem;">'+
      _secCard("fa-solid fa-clipboard-check",features.filter(function(f){return f.status;}).length,"Compliance Features","#c084fc")+
      _secCard("fa-solid fa-check","100%","Compliance Score","#10b981")+
      _secCard("fa-solid fa-calendar","Quarterly","Review Cycle","#f59e0b")+
    '</div>'+
    '<div style="background:rgba(15,22,42,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:1rem;">'+
      '<div style="font-size:0.75rem;color:#c084fc;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;"><i class="fa-solid fa-clipboard-check" style="margin-right:4px;"></i> Compliance Settings</div>'+
      features.map(function(f,i){
        return _secToggle(f.name,"sec-comp-"+i,f.status,"#c084fc");
      }).join('')+
    '</div>'+
  '</div>';
};

_modContent.enterprise = function(s){
  var features = [
    {name:"Security Health Score",status:true},
    {name:"Real-time Threat Detection",status:true},
    {name:"Device Trust Management",status:true},
    {name:"IP Reputation Monitoring",status:true},
    {name:"Geo-location Login Detection",status:true},
    {name:"Impossible Travel Detection",status:true},
    {name:"AI-powered Anomaly Detection",status:true},
    {name:"Behavioral Analysis",status:true},
    {name:"Insider Threat Monitoring",status:true},
    {name:"Security Incident Response Center",status:true},
    {name:"Security Policy Manager",status:true},
    {name:"Security Analytics Dashboard",status:true},
    {name:"Threat Intelligence Feed",status:true},
    {name:"Data Loss Prevention (DLP)",status:true},
    {name:"Watermarking for Exports",status:false},
    {name:"Encryption Key Management",status:true},
    {name:"Secure Document Sharing",status:true},
    {name:"Meeting Access Expiration",status:true},
    {name:"Temporary Guest Access",status:true},
    {name:"Emergency Account Lockdown",status:true}
  ];
  return '<div style="display:flex;flex-direction:column;gap:0.75rem;">'+
    '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.6rem;">'+
      _secCard("fa-solid fa-building-shield",features.filter(function(f){return f.status;}).length,"Enterprise Features","#fb923c")+
      _secCard("fa-solid fa-shield","#92","Enterprise Score","#10b981")+
      _secCard("fa-solid fa-bolt","Active","Threat Detection","#ef4444")+
      _secCard("fa-solid fa-robot","Enabled","AI Anomaly","#ec4899")+
    '</div>'+
    '<div style="background:rgba(15,22,42,0.5);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:1rem;max-height:500px;overflow-y:auto;">'+
      '<div style="font-size:0.75rem;color:#fb923c;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.75rem;"><i class="fa-solid fa-building-shield" style="margin-right:4px;"></i> Advanced Enterprise Security</div>'+
      features.map(function(f,i){
        return _secToggle(f.name,"sec-ent-"+i,f.status,"#fb923c");
      }).join('')+
    '</div>'+
  '</div>';
};

/* ─── MAIN RENDER ───────────────────────────────────────────────────────────── */

window.renderAdminSecurityCenterV2 = function(){
  var c = document.getElementById("screen-admin-security-center");
  if(!c) return;
  var s = _secStats();

  var navBtns = SEC_MODULES.map(function(m){
    var a = m.id===_secState.activeTab;
    return '<button class="sec-mod-tab" data-secmod="'+m.id+'" style="padding:0.35rem 0.65rem;font-size:0.68rem;border:1px solid '+(a?'rgba(255,255,255,0.12)':'rgba(255,255,255,0.04)')+';border-radius:8px;cursor:pointer;background:'+(a?'rgba(129,140,248,0.12)':'transparent')+';color:'+(a?'#a5b4fc':'#6b7a8a')+';font-weight:'+(a?'600':'400')+';transition:all 0.2s;white-space:nowrap;">'+m.icon.replace('fa-solid ','<i class="'+m.icon+'" style="margin-right:3px;font-size:0.6rem;"></i>')+' '+m.label+'</button>';
  }).join('');

  var content = _modContent[_secState.activeTab] ? _modContent[_secState.activeTab](s) : '<p style="color:#6b7a99;">Module not found</p>';

  c.innerHTML = '<div class="nf-screen-header"><h2 style="font-family:var(--font-display);font-size:1.3rem;color:#f3f4f6;display:flex;align-items:center;gap:0.6rem;"><i class="fa-solid fa-shield-halved" style="color:#818cf8;"></i> Enterprise Security Center</h2></div>'+
    '<div style="margin-top:0.75rem;background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1rem;">'+
      '<div style="display:flex;gap:4px;margin-bottom:0.75rem;border-bottom:1px solid rgba(255,255,255,0.06);padding-bottom:0.75rem;overflow-x:auto;flex-wrap:nowrap;">'+navBtns+'</div>'+
      '<div id="sec-mod-content">'+content+'</div>'+
    '</div>';

  c.querySelectorAll(".sec-mod-tab").forEach(function(btn){
    btn.addEventListener("click", function(){
      _secState.activeTab = this.dataset.secmod;
      _logAudit("view","security_center","Viewed "+this.dataset.secmod+" module");
      renderAdminSecurityCenterV2();
    });
  });
};

window._secToggle = function(id, val){
  _logAudit("toggle","security_center",id+" = "+val);
  _logSecEvent("config_change","Security setting changed: "+id+" = "+val,"info");
  showToast("Setting updated: "+id.replace(/sec-\w+-/,''),"success");
};

})();
