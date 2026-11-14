// EchoAction AI - New Features Module
(function() {
  'use strict';

  // Register render functions
  window.__nf = window.__nf || {};

  // ---- MOCK DATA ----
  const NF_DATA = {
    topics: ["AI","Backend","Frontend","Database","Cloud","Testing","Security","Deployment","Budget","Recruitment","Marketing"],
    topicDetails: {
      AI: { meetings:10, tasks:8, docs:5, decisions:3, people:["Sarah","Marcus","Elena"] },
      Backend: { meetings:15, tasks:12, docs:7, decisions:5, people:["Sarah","Alex"] },
      Frontend: { meetings:8, tasks:10, docs:4, decisions:2, people:["Marcus","Chloe"] },
      Security: { meetings:6, tasks:5, docs:3, decisions:4, people:["Alex","Sarah"] }
    },
    people: [
      { name:"Sarah Jenkins", email:"sarah@echoaction.ai", role:"Lead Backend", meetings:12, projects:3, tasksAssigned:15, tasksCompleted:11, ideas:8, speakingPct:32, decisions:5, docs:7, recent:"Reviewed API architecture, Updated database schema" },
      { name:"Marcus Chen", email:"marcus@echoaction.ai", role:"Frontend Developer", meetings:9, projects:2, tasksAssigned:10, tasksCompleted:9, ideas:5, speakingPct:18, decisions:2, docs:4, recent:"Implemented dark mode, Fixed responsive layout" },
      { name:"Elena Rodriguez", email:"elena@echoaction.ai", role:"Lead Designer", meetings:14, projects:4, tasksAssigned:12, tasksCompleted:10, ideas:12, speakingPct:25, decisions:4, docs:6, recent:"Redesigned dashboard, Created new component library" },
      { name:"Alex Thompson", email:"alex@echoaction.ai", role:"DevOps", meetings:7, projects:3, tasksAssigned:8, tasksCompleted:7, ideas:3, speakingPct:10, decisions:3, docs:2, recent:"Deployed staging environment, Configured CI/CD" },
      { name:"Chloe Kim", email:"chloe@echoaction.ai", role:"Product Manager", meetings:20, projects:5, tasksAssigned:18, tasksCompleted:15, ideas:15, speakingPct:15, decisions:8, docs:10, recent:"Finalized Q2 roadmap, Prioritized feature backlog" }
    ],
    similarMeetings: [
      { title:"Sprint Planning - Week 12", similarity:92, date:"2026-02-15" },
      { title:"Architecture Review", similarity:87, date:"2026-02-10" },
      { title:"QA Pipeline Discussion", similarity:81, date:"2026-01-28" },
      { title:"Database Migration Planning", similarity:78, date:"2026-01-20" },
      { title:"Security Audit Meeting", similarity:74, date:"2026-01-15" }
    ],
    decisions: [
      { decision:"Migrate to PostgreSQL", project:"Platform", owner:"Sarah", date:"2026-02-10", priority:"High", status:"Completed", confidence:92, reason:"Better scalability", impl:"In Progress" },
      { decision:"Adopt React 18", project:"Frontend", owner:"Marcus", date:"2026-02-05", priority:"Medium", status:"Active", confidence:85, reason:"Performance improvements", impl:"Not Started" },
      { decision:"AWS Reserved Instances", project:"Infrastructure", owner:"Alex", date:"2026-01-28", priority:"High", status:"Completed", confidence:90, reason:"Cost reduction", impl:"Completed" },
      { decision:"Dark Mode Support", project:"Frontend", owner:"Chloe", date:"2026-01-20", priority:"Low", status:"Active", confidence:78, reason:"User requests", impl:"In Progress" },
      { decision:"Automated Testing Pipeline", project:"QA", owner:"Sarah", date:"2026-01-15", priority:"Medium", status:"Changed", confidence:70, reason:"Reduce manual testing", impl:"On Hold" },
      { decision:"Budget Freeze Q2", project:"Finance", owner:"Chloe", date:"2026-01-10", priority:"High", status:"Completed", confidence:95, reason:"Cost optimization", impl:"Completed" }
    ],
    timeline: [
      { time:"09:15", label:"Requirement Discussion", desc:"Discussed new feature requirements for Q2 roadmap" },
      { time:"09:28", label:"Budget Discussion", desc:"Reviewed Q2 budget allocation and resource planning" },
      { time:"09:40", label:"Architecture Review", desc:"Evaluated proposed architecture changes for scalability" },
      { time:"10:05", label:"Deadline Change", desc:"Extended sprint deadline by 3 days due to dependencies" },
      { time:"10:30", label:"Final Approval", desc:"Approved architecture proposal and budget changes" }
    ],
    aiInsights: [
      "Testing delays increasing by 15% this quarter",
      "Security discussions up 40% after recent audit",
      "Budget approvals slowing down - average 5 days",
      "Customer complaints reduced by 25%",
      "Backend meetings decreasing - consider check-in"
    ],
    aiSuggestions: [
      "Review testing coverage before next sprint",
      "Schedule follow-up with QA team",
      "Invite security team to architecture review",
      "Update project documentation",
      "Review pending risks in Risk Register"
    ],
    chatHistory: {},
    projectHealth: { score:82, completed:45, delayed:8, pendingApprovals:6, attendance:87, riskScore:23, budgetHealth:78, sprintProgress:70, productivity:85, blockedTasks:3 },
    coachData: { score:92, participation:78, interruptions:3, speakingBalance:65, questionsAsked:12, ideasShared:8, decisionClarity:85, focusScore:90, timeUsage:80, communicationScore:88 },
    predictions: [
      { label:"Project Delay Probability", value:32, desc:"Based on current velocity and blockers", status:"warning" },
      { label:"Risk Probability", value:18, desc:"Security and budget risks analyzed", status:"good" },
      { label:"Meeting Effectiveness", value:78, desc:"Trending upward with coaching", status:"good" },
      { label:"Budget Overrun Risk", value:25, desc:"Spending is 5% above projection", status:"warning" },
      { label:"Task Completion Date", value:"Mar 15", desc:"Estimated based on 85% velocity", status:"info" },
      { label:"Employee Workload", value:"High (3)", desc:"3 team members at capacity", status:"warning" },
      { label:"Upcoming Bottlenecks", value:"QA Capacity", desc:"Testing queue growing 20%", status:"warning" },
      { label:"Customer Satisfaction", value:88, desc:"Based on latest survey data", status:"good" }
    ]
  };
  Object.keys(NF_DATA.topicDetails).forEach(k => {
    if (!NF_DATA.topicDetails[k].documents) NF_DATA.topicDetails[k].documents = NF_DATA.topicDetails[k].docs;
    if (!NF_DATA.topicDetails[k].reports) NF_DATA.topicDetails[k].reports = Math.ceil(NF_DATA.topicDetails[k].meetings/2);
    if (!NF_DATA.topicDetails[k].relatedTopics) NF_DATA.topicDetails[k].relatedTopics = "";
  });

  // ---- HELPER ----
  function el(id) { return document.getElementById(id); }
  function esc(s) { return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }

  function _getLD() {
    const ms = (window.meetings && window.meetings.length > 0) ? window.meetings : null;
    if (!ms) return NF_DATA;
    const topics = [...new Set(ms.map(m => m.category || "General").filter(Boolean))];
    const topicDetails = {};
    topics.forEach(t => {
      const m = ms.filter(x => (x.category || "General") === t);
      const allPeople = [...new Set(m.flatMap(x => x.attendees || []))];
      topicDetails[t] = { meetings: m.length, tasks: m.reduce((s,x) => s + (x.actionItems||[]).length, 0), docs: m.reduce((s,x) => s + ((x.summary&&x.summary.keyPoints)||[]).length*2, 0), decisions: m.reduce((s,x) => s + (x.jiraTickets||[]).length, 0), people: allPeople };
    });
    const peopleMap = {};
    ms.forEach(m => (m.attendees||[]).forEach(a => {
      if (!peopleMap[a]) peopleMap[a] = { name:a, email:a.toLowerCase().replace(/\s+/g,'.')+'@echoaction.ai', role:'Team Member', meetings:0, projects:0, tasksAssigned:0, tasksCompleted:0, ideas:Math.floor(Math.random()*5)+3, speakingPct:Math.floor(Math.random()*30)+10, decisions:0, docs:0, recent:'' };
      peopleMap[a].meetings++;
      peopleMap[a].tasksAssigned += (m.actionItems||[]).length;
      peopleMap[a].tasksCompleted += (m.actionItems||[]).filter(x => x.status==='Completed').length;
      peopleMap[a].decisions += (m.jiraTickets||[]).length;
      peopleMap[a].recent = (m.summary && m.summary.overview || '').substring(0,50);
    }));
    const people = Object.values(peopleMap);
    const decisions = ms.flatMap(m => (m.actionItems||[]).slice(0,3).map((a,i) => ({
      decision: a.title, project: m.category || 'General', owner: a.assignee || 'Unassigned', date: m.date || '', priority: a.priority || 'Medium',
      status: a.status === 'Completed' ? 'Completed' : 'Active', confidence: Math.floor(Math.random()*30)+70, reason: (m.summary&&m.summary.overview||'').substring(0,40)||'Key decision', impl: a.status === 'Completed' ? 'Completed' : 'In Progress'
    }))).slice(0,12);
    const totalScore = ms.reduce((s,m) => s + ((m.summary&&m.summary.meetingScore)||80), 0);
    const avgScore = Math.round(totalScore / ms.length);
    const allTasks = ms.flatMap(m => m.actionItems||[]);
    const completedTasks = allTasks.filter(t => t.status === 'Completed');
    return {
      topics, topicDetails, people,
      similarMeetings: ms.slice(0,5).map(m => ({ title:m.title||'Meeting', similarity:Math.floor(Math.random()*20)+75, date:m.date||'' })),
      decisions,
      timeline: ms.slice(0,5).map(m => ({ time:m.date||'', label:m.title||'Meeting', desc:(m.summary&&m.summary.overview||'').substring(0,60)||'Meeting recording' })),
      aiInsights: ms.slice(0,5).map(m => (m.summary&&m.summary.keyPoints||[]).slice(0,1)).flat().filter(Boolean),
      aiSuggestions: topics.slice(0,5).map(t => `Review ${t} topics in next meeting`),
      projectHealth: {
        score: avgScore, completed: completedTasks.length, delayed: allTasks.filter(t => t.status!=='Completed').length,
        pendingApprovals: Math.floor(allTasks.length*0.2), attendance: Math.round(ms.reduce((s,m)=>(m.attendees||[]).length,0)/Math.max(ms.length,1)*10)+70,
        riskScore: Math.floor(Math.random()*30)+10, budgetHealth: Math.floor(Math.random()*20)+75,
        sprintProgress: avgScore, productivity: Math.floor(Math.random()*15)+75, blockedTasks: Math.floor(allTasks.length*0.1)
      },
      coachData: {
        score: avgScore, participation: Math.floor(Math.random()*20)+70, interruptions: Math.floor(Math.random()*5)+1,
        speakingBalance: Math.floor(Math.random()*20)+60, questionsAsked: Math.floor(Math.random()*10)+5,
        ideasShared: Math.floor(Math.random()*8)+3, decisionClarity: Math.floor(Math.random()*15)+75,
        focusScore: Math.floor(Math.random()*15)+80, timeUsage: Math.floor(Math.random()*20)+70,
        communicationScore: Math.floor(Math.random()*15)+75
      },
      predictions: [
        { label:"Project Delay Probability", value:Math.floor(Math.random()*30)+20, desc:"Based on current velocity and blockers", status:"warning" },
        { label:"Risk Probability", value:Math.floor(Math.random()*20)+10, desc:"Security and budget risks analyzed", status:"good" },
        { label:"Meeting Effectiveness", value:avgScore, desc:"Trending upward with coaching", status:"good" },
        { label:"Budget Overrun Risk", value:Math.floor(Math.random()*25)+10, desc:"Spending analysis", status:"warning" },
        { label:"Task Completion Date", value:"Est. "+new Date(Date.now()+14*86400000).toLocaleDateString(), desc:"Based on current velocity", status:"info" },
        { label:"Employee Workload", value:"High ("+Math.min(people.length,5)+")", desc:people.length+" team members at capacity", status:"warning" },
        { label:"Upcoming Bottlenecks", value:"QA Capacity", desc:"Testing queue growing", status:"warning" },
        { label:"Customer Satisfaction", value:Math.floor(Math.random()*15)+80, desc:"Based on meeting sentiment", status:"good" }
      ]
    };
  }

  // ============ 1. MEETING BRAIN ============
  window.__nf["screen-mbrain"] = function() {
    const c = el("screen-mbrain");
    if (!c) return;
    const LD = _getLD();
    let tabs = ["Ask AI","Topic Explorer","People History","Project History","Similar Meetings","AI Recommendations"];
    let activeTab = c.__mbrainTab || "Ask AI";
    c.innerHTML = `
      <div class="nf-screen-header">
        <h2 style="font-family:var(--font-display);font-size:1.3rem;color:#f3f4f6;display:flex;align-items:center;gap:0.6rem;"><i class="fa-solid fa-brain" style="color:#818cf8;"></i> Meeting Brain <span style="font-size:0.7rem;background:rgba(129,140,248,0.15);color:#818cf8;padding:0.15rem 0.5rem;border-radius:20px;">Cross-Meeting Intelligence</span></h2>
        <p style="font-size:0.8rem;color:#8899b0;margin:0.3rem 0 0 2.1rem;">Search across all meetings, projects, tasks and decisions</p>
      </div>
      <div class="nf-tabs" id="mbrain-tabs">${tabs.map(t => `<button class="nf-tab ${t===activeTab?'nf-tab-active':''}" data-mbtab="${t}">${t}</button>`).join("")}</div>
      <div class="nf-tab-content" id="mbrain-content"></div>
    `;
    c.__mbrainTab = activeTab;
    _renderMBrainTab(activeTab, c);
  };

  function _renderMBrainTab(tab, c) {
    const area = el("mbrain-content");
    if (!area) return;
    switch(tab) {
      case "Ask AI": area.innerHTML = `
        <div style="max-width:800px;margin:1.5rem auto 0;">
          <div style="background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.5rem;">
            <div style="display:flex;gap:0.75rem;margin-bottom:1.25rem;">
              <input type="text" id="mbrain-query" class="form-input" placeholder="Ask anything about your meetings..." style="flex:1;font-size:0.95rem;padding:0.75rem 1rem;">
              <button class="btn btn-primary" id="mbrain-ask-btn" style="padding:0.75rem 1.5rem;white-space:nowrap;"><i class="fa-solid fa-magnifying-glass"></i> Ask</button>
            </div>
            <p style="font-size:0.75rem;color:#8899b0;margin-bottom:0.5rem;">Example questions:</p>
            <div class="nf-suggested-q" style="display:flex;flex-wrap:wrap;gap:0.4rem;">
              ${["Why did we change the database?","Show all meetings discussing AI","Who approved AWS?","Show all pending risks","What decisions were made about Project Alpha?","Which customer requested dark mode?"].map(q => `<button class="nf-q-chip" data-mbrainq="${esc(q)}">${esc(q)}</button>`).join("")}
            </div>
          </div>
          <div id="mbrain-answer" style="margin-top:1rem;display:none;"></div>
        </div>`;
        // Wire up ask button and chips
        setTimeout(() => {
          const btn = el("mbrain-ask-btn");
          const inp = el("mbrain-query");
          if (btn && inp) {
            function ask() {
              const q = inp.value.trim();
              if (!q) return;
              el("mbrain-answer").style.display = "block";
              el("mbrain-answer").innerHTML = ` <div style="background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.5rem;">
                <div style="display:flex;align-items:flex-start;gap:0.75rem;margin-bottom:1rem;">
                  <div style="width:32px;height:32px;border-radius:50%;background:rgba(129,140,248,0.2);display:flex;align-items:center;justify-content:center;flex-shrink:0;"><i class="fa-solid fa-brain" style="color:#818cf8;font-size:0.8rem;"></i></div>
                  <div><p style="color:#e8edf5;font-size:0.9rem;">Based on my analysis of all meetings:</p><p style="color:#c8d0dc;font-size:0.85rem;margin-top:0.4rem;line-height:1.6;">${q.includes("database")?"The database was changed from MongoDB to PostgreSQL for better scalability and ACID compliance during the sprint planning on Feb 10, 2026.":q.includes("AI")?"AI was discussed in 12 meetings, primarily around automated summarization and smart recommendations. Key decisions were made in the Feb 5 architecture review.":q.includes("AWS")?"AWS Reserved Instances were approved by Alex Thompson (DevOps) on Jan 28, 2026 to reduce infrastructure costs by an estimated 30%.":q.includes("risk")?"There are 5 open risks: QA capacity bottleneck (High), Budget overrun potential (Medium), Timeline slippage (High), Security compliance gap (High), Dependency on external API (Medium).":q.includes("Project Alpha")?"Project Alpha decisions: 1) Use React 18 (Approved), 2) PostgreSQL for data layer (Approved), 3) Two-week sprint cycle (Approved), 4) External QA review (Pending).":q.includes("dark")?"Dark mode was requested by 3 enterprise customers during the Q1 feedback session. It was prioritized as Medium and assigned to Marcus Chen.":"I found relevant information across 5 meetings. Key highlights include discussions about architecture changes, budget approvals, and timeline updates."}</p></div>
                </div>
                <div style="border-top:1px solid rgba(255,255,255,0.06);padding-top:0.75rem;margin-top:0.5rem;">
                  <p style="font-size:0.75rem;color:#8899b0;margin-bottom:0.5rem;">Referenced Meetings</p>
                  <div style="display:flex;flex-wrap:wrap;gap:0.4rem;">${["Sprint Planning W12","Architecture Review","Budget Meeting","QA Sync"].map(m => `<span style="background:rgba(99,102,241,0.1);color:#a5b4fc;font-size:0.75rem;padding:0.2rem 0.6rem;border-radius:6px;">${m}</span>`).join("")}</div>
                </div>
                <div style="margin-top:0.75rem;display:flex;flex-wrap:wrap;gap:0.75rem;">
                  <span style="font-size:0.75rem;color:#8899b0;"><i class="fa-solid fa-list-check" style="color:#10b981;margin-right:0.3rem;"></i> 3 Related Tasks</span>
                  <span style="font-size:0.75rem;color:#8899b0;"><i class="fa-solid fa-scale-balanced" style="color:#f59e0b;margin-right:0.3rem;"></i> 2 Decisions</span>
                  <span style="font-size:0.75rem;color:#8899b0;"><i class="fa-solid fa-file-lines" style="color:#06b6d4;margin-right:0.3rem;"></i> 4 Documents</span>
                </div>
              </div>`;
            }
            btn.onclick = ask;
            inp.onkeydown = (e) => { if(e.key==="Enter") ask(); };
          }
          document.querySelectorAll("[data-mbrainq]").forEach(b => {
            b.onclick = () => { const i = el("mbrain-query"); if(i){ i.value = b.textContent; el("mbrain-ask-btn").click(); } };
          });
        }, 50);
        break;
      case "Topic Explorer": area.innerHTML = `
        <div style="max-width:900px;margin:1.5rem auto 0;">
          <div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:1.25rem;">${LD.topics.map(t => `<button class="nf-topic-chip" data-mbtopic="${esc(t)}" style="background:rgba(99,102,241,0.1);color:#a5b4fc;border:1px solid rgba(99,102,241,0.2);padding:0.45rem 1rem;border-radius:20px;cursor:pointer;font-size:0.8rem;transition:var(--transition-fast);">${t}</button>`).join("")}</div>
          <div id="mbrain-topic-detail" style="background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.5rem;text-align:center;color:#8899b0;font-size:0.85rem;">Click a topic to explore related items</div>
        </div>`;
        setTimeout(() => {
          document.querySelectorAll("[data-mbtopic]").forEach(b => {
            b.onclick = () => {
              const t = b.textContent;
              const d = LD.topicDetails[t] || LD.topicDetails[Object.keys(LD.topicDetails)[0]];
              document.querySelectorAll("[data-mbtopic]").forEach(x => x.style.background="rgba(99,102,241,0.1)");
              b.style.background = "rgba(129,140,248,0.3)";
              el("mbrain-topic-detail").innerHTML = `
                <h3 style="color:#f3f4f6;font-size:1rem;margin-bottom:1rem;"><i class="fa-solid fa-tag" style="color:#818cf8;margin-right:0.4rem;"></i>${t}</h3>
                <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:0.75rem;">
                  <div class="nf-stat-card"><span class="nf-stat-num">${d.meetings}</span><span class="nf-stat-label">Meetings</span></div>
                  <div class="nf-stat-card"><span class="nf-stat-num">${d.tasks}</span><span class="nf-stat-label">Tasks</span></div>
                  <div class="nf-stat-card"><span class="nf-stat-num">${d.docs||d.documents}</span><span class="nf-stat-label">Documents</span></div>
                  <div class="nf-stat-card"><span class="nf-stat-num">${d.decisions}</span><span class="nf-stat-label">Decisions</span></div>
                  <div class="nf-stat-card"><span class="nf-stat-num">${d.reports||Math.ceil(d.meetings/2)}</span><span class="nf-stat-label">Reports</span></div>
                  <div class="nf-stat-card"><span class="nf-stat-num">${d.people.length}</span><span class="nf-stat-label">People</span></div>
                </div>
                <div style="margin-top:1rem;display:flex;flex-wrap:wrap;gap:0.4rem;justify-content:center;">
                  ${d.people.map(p => `<span style="background:rgba(16,185,129,0.1);color:#6ee7b7;font-size:0.75rem;padding:0.2rem 0.6rem;border-radius:6px;">${p}</span>`).join("")}
                </div>`;
            };
          });
        }, 50);
        break;
      case "People History": area.innerHTML = `
        <div style="max-width:800px;margin:1.5rem auto 0;">
          <div style="margin-bottom:1rem;">
            <input type="text" id="mbrain-people-search" class="form-input" placeholder="Search any employee..." style="width:100%;padding:0.75rem 1rem;font-size:0.9rem;">
          </div>
          <div id="mbrain-people-results"></div>
        </div>`;
        setTimeout(() => {
          const inp = el("mbrain-people-search");
          const res = el("mbrain-people-results");
          if(!inp||!res) return;
          function searchPeople(q) {
            const ql = q.toLowerCase();
            const matches = LD.people.filter(p => p.name.toLowerCase().includes(ql) || p.role.toLowerCase().includes(ql) || p.email.toLowerCase().includes(ql));
            if (!matches.length) { res.innerHTML = '<p style="color:#8899b0;text-align:center;padding:1rem;font-size:0.85rem;">No matching employees found.</p>'; return; }
            res.innerHTML = matches.map(p => `
              <div class="nf-person-card" style="background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.25rem;margin-bottom:0.75rem;">
                <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.75rem;">
                  <div style="width:40px;height:40px;border-radius:50%;background:rgba(129,140,248,0.2);display:flex;align-items:center;justify-content:center;color:#818cf8;font-weight:700;font-size:1rem;">${p.name.charAt(0)}</div>
                  <div><p style="color:#f3f4f6;font-size:0.9rem;font-weight:600;">${esc(p.name)}</p><p style="color:#8899b0;font-size:0.78rem;">${esc(p.role)} · ${esc(p.email)}</p></div>
                </div>
                <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:0.5rem;">
                  <div class="nf-mini-stat"><span class="nf-mini-num">${p.meetings}</span> Meetings</div>
                  <div class="nf-mini-stat"><span class="nf-mini-num">${p.projects}</span> Projects</div>
                  <div class="nf-mini-stat"><span class="nf-mini-num">${p.tasksAssigned}</span> Tasks</div>
                  <div class="nf-mini-stat"><span class="nf-mini-num">${p.tasksCompleted}</span> Completed</div>
                  <div class="nf-mini-stat"><span class="nf-mini-num">${p.ideas}</span> Ideas</div>
                  <div class="nf-mini-stat"><span class="nf-mini-num">${p.speakingPct}%</span> Speaking</div>
                  <div class="nf-mini-stat"><span class="nf-mini-num">${p.decisions}</span> Decisions</div>
                  <div class="nf-mini-stat"><span class="nf-mini-num">${p.docs}</span> Documents</div>
                </div>
                <div style="margin-top:0.5rem;font-size:0.78rem;color:#c8d0dc;"><i class="fa-solid fa-clock-rotate-left" style="color:#8899b0;margin-right:0.3rem;"></i>${esc(p.recent)}</div>
              </div>`).join("");
          }
          inp.oninput = () => searchPeople(inp.value);
          searchPeople("");
        }, 50);
        break;
      case "Project History": area.innerHTML = `
        <div style="max-width:800px;margin:1.5rem auto 0;">
          ${LD.topics.slice(0,6).map(p => {
            const td = LD.topicDetails[p] || {meetings:0,tasks:0};
            return `<div class="nf-project-card" style="background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.25rem;margin-bottom:0.75rem;cursor:pointer;">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <h4 style="color:#f3f4f6;font-size:0.9rem;margin:0;"><i class="fa-solid fa-folder-open" style="color:#818cf8;margin-right:0.4rem;"></i>${p}</h4>
                <i class="fa-solid fa-chevron-down" style="color:#8899b0;font-size:0.75rem;"></i>
              </div>
              <div class="nf-project-flow" style="display:none;margin-top:0.75rem;gap:0.5rem;flex-wrap:wrap;">
                ${[`Meetings (${td.meetings})`,`Tasks (${td.tasks})`,`Documents (${td.docs||0})`,`People (${(td.people||[]).length})`,`Decisions (${td.decisions||0})`].map((s,i) =>
                  `<span style="background:${i===4?"rgba(16,185,129,0.15)":"rgba(255,255,255,0.04)"};color:${i===4?"#6ee7b7":"#8899b0"};font-size:0.75rem;padding:0.3rem 0.7rem;border-radius:6px;display:flex;align-items:center;gap:0.3rem;"><i class="fa-solid fa-${["comments","list-check","file-lines","users","scale-balanced"][i]}" style="font-size:0.65rem;"></i> ${s}</span>`
                ).join("")}
              </div>
            </div>`;
          }).join("")}
        </div>`;
        setTimeout(() => {
          document.querySelectorAll(".nf-project-card").forEach(card => {
            card.onclick = () => { const flow = card.querySelector(".nf-project-flow"); flow.style.display = flow.style.display==="none"?"flex":"none"; };
          });
        }, 50);
        break;
      case "Similar Meetings": area.innerHTML = `
        <div style="max-width:800px;margin:1.5rem auto 0;">
          <p style="font-size:0.8rem;color:#8899b0;margin-bottom:1rem;">Meetings related to current context based on topics, decisions, and participants</p>
          ${LD.similarMeetings.map(m => `
            <div style="background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1rem;margin-bottom:0.5rem;display:flex;justify-content:space-between;align-items:center;">
              <div><p style="color:#f3f4f6;font-size:0.85rem;">${esc(m.title)}</p><p style="color:#8899b0;font-size:0.73rem;">${m.date}</p></div>
              <div style="background:rgba(16,185,129,${m.similarity/100});color:#6ee7b7;font-size:0.8rem;font-weight:600;padding:0.3rem 0.7rem;border-radius:8px;">${m.similarity}%</div>
            </div>`).join("")}
        </div>`;
        break;
      case "AI Recommendations": area.innerHTML = `
        <div style="max-width:800px;margin:1.5rem auto 0;">
          <div style="background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.5rem;">
            <h4 style="color:#f3f4f6;font-size:0.95rem;margin-bottom:1rem;"><i class="fa-solid fa-wand-magic-sparkles" style="color:#f59e0b;margin-right:0.4rem;"></i> AI Recommendations</h4>
            <div style="display:flex;flex-direction:column;gap:0.5rem;">
              ${LD.aiSuggestions.map(s => `<div style="background:rgba(245,158,11,0.08);border-left:3px solid #f59e0b;padding:0.65rem 0.85rem;border-radius:0 8px 8px 0;font-size:0.82rem;color:#e8edf5;display:flex;align-items:center;gap:0.5rem;"><i class="fa-solid fa-lightbulb" style="color:#f59e0b;font-size:0.75rem;flex-shrink:0;"></i> ${esc(s)}</div>`).join("")}
            </div>
          </div>
          <div style="margin-top:1rem;background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.5rem;">
            <h4 style="color:#f3f4f6;font-size:0.95rem;margin-bottom:0.75rem;"><i class="fa-solid fa-message" style="color:#06b6d4;margin-right:0.4rem;"></i> Organization Memory</h4>
            <p style="font-size:0.82rem;color:#8899b0;line-height:1.6;">The organization memory contains <strong style="color:#c8d0dc;">${LD.topics.length} topics</strong>, <strong style="color:#c8d0dc;">${LD.decisions.length} decisions</strong>, <strong style="color:#c8d0dc;">${LD.people.length} people</strong>, and <strong style="color:#c8d0dc;">${LD.projectHealth.completed} completed tasks</strong>. Ask the Meeting Brain or AI Chat to retrieve specific information.</p>
          </div>
        </div>`;
        break;
    }
  }

  // ---- Tab switching for Meeting Brain ----
  document.addEventListener("click", function(e) {
    const tab = e.target.closest("[data-mbtab]");
    if (!tab) return;
    const c = el("screen-mbrain");
    if (!c) return;
    c.__mbrainTab = tab.textContent;
    document.querySelectorAll("[data-mbtab]").forEach(t => t.classList.remove("nf-tab-active"));
    tab.classList.add("nf-tab-active");
    _renderMBrainTab(tab.textContent, c);
  });

  // ============ 2. AI CHAT ============
  window.__nf["screen-ai-chat"] = function() {
    const c = el("screen-ai-chat");
    if (!c) return;
    c.innerHTML = `
      <div class="nf-screen-header">
        <h2 style="font-family:var(--font-display);font-size:1.3rem;color:#f3f4f6;display:flex;align-items:center;gap:0.6rem;"><i class="fa-solid fa-headset" style="color:#06b6d4;"></i> Support & AI Help <span style="font-size:0.7rem;background:rgba(6,182,212,0.15);color:#06b6d4;padding:0.15rem 0.5rem;border-radius:20px;">Customer Care</span></h2>
        <p style="font-size:0.8rem;color:#8899b0;margin:0.3rem 0 0 2.1rem;">Get help with issues, support requests, and customer care inquiries</p>
      </div>
      <div class="nf-chat-layout" style="display:flex;gap:1rem;margin-top:1rem;height:calc(100vh - 280px);min-height:400px;">
        <div style="flex:1;display:flex;flex-direction:column;background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;overflow:hidden;">
          <div id="aichat-messages" style="flex:1;overflow-y:auto;padding:1rem;display:flex;flex-direction:column;gap:0.75rem;">
            <div style="text-align:center;padding:2rem 1rem;color:#8899b0;">
              <i class="fa-solid fa-robot" style="font-size:2rem;color:#10b981;margin-bottom:0.5rem;"></i>
              <p style="font-size:0.85rem;">Ask anything about your organization's meetings, decisions, and knowledge.</p>
            </div>
          </div>
          <div style="padding:0.75rem 1rem;border-top:1px solid rgba(255,255,255,0.06);display:flex;gap:0.75rem;">
            <input type="text" id="aichat-input" class="form-input" placeholder="Ask a question..." style="flex:1;padding:0.65rem 1rem;">
            <button class="btn btn-primary" id="aichat-send" style="padding:0.65rem 1.2rem;"><i class="fa-solid fa-paper-plane"></i></button>
          </div>
        </div>
        <div style="width:280px;flex-shrink:0;display:flex;flex-direction:column;gap:0.75rem;">
          <div style="background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1rem;">
            <p style="font-size:0.78rem;color:#8899b0;margin-bottom:0.5rem;font-weight:600;">SUGGESTED QUESTIONS</p>
            ${["Who approved AWS?","Show all security meetings","Why was React replaced?","What tasks remain pending?","What changed last week?","Who talked most about AI?"].map(q =>
              `<button class="nf-chat-qchip" data-aichatq="${esc(q)}" style="display:block;width:100%;text-align:left;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:0.5rem 0.65rem;margin-bottom:0.4rem;font-size:0.75rem;color:#c8d0dc;cursor:pointer;transition:var(--transition-fast);">${esc(q)}</button>`
            ).join("")}
          </div>
          <div style="background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1rem;">
            <p style="font-size:0.78rem;color:#8899b0;margin-bottom:0.5rem;font-weight:600;">RECENT SEARCHES</p>
            ${["Database migration","Security audit","Budget Q2","Dark mode","React migration"].map(s =>
              `<div style="font-size:0.75rem;color:#8899b0;padding:0.3rem 0;border-bottom:1px solid rgba(255,255,255,0.04);display:flex;align-items:center;gap:0.4rem;"><i class="fa-solid fa-clock-rotate-left" style="font-size:0.6rem;"></i> ${s}</div>`
            ).join("")}
          </div>
        </div>
      </div>`;
    setTimeout(() => {
      const inp = el("aichat-input");
      const send = el("aichat-send");
      const msgs = el("aichat-messages");
      if (!inp||!send||!msgs) return;
      function addMsg(text, isUser) {
        const d = document.createElement("div");
        d.style.cssText = `display:flex;align-items:flex-start;gap:0.65rem;${isUser?"flex-direction:row-reverse;":""}`;
        d.innerHTML = `
          <div style="width:30px;height:30px;border-radius:50%;background:${isUser?"rgba(99,102,241,0.2)":"rgba(16,185,129,0.2)"};display:flex;align-items:center;justify-content:center;flex-shrink:0;"><i class="fa-solid ${isUser?"fa-user":"fa-robot"}" style="color:${isUser?"#818cf8":"#10b981"};font-size:0.7rem;"></i></div>
          <div style="background:${isUser?"rgba(99,102,241,0.12)":"rgba(16,185,129,0.08)"};border:1px solid ${isUser?"rgba(99,102,241,0.15)":"rgba(16,185,129,0.12)"};border-radius:${isUser?"14px 14px 4px 14px":"14px 14px 14px 4px"};padding:0.65rem 0.9rem;max-width:80%;">
            <p style="color:#e8edf5;font-size:0.82rem;line-height:1.5;">${text}</p>
            ${!isUser?`<div style="margin-top:0.5rem;padding-top:0.5rem;border-top:1px solid rgba(255,255,255,0.06);">
              <p style="font-size:0.7rem;color:#6ee7b7;margin-bottom:0.3rem;"><i class="fa-solid fa-link"></i> Referenced: Sprint Planning, Architecture Review</p>
              <p style="font-size:0.7rem;color:#fbbf24;"><i class="fa-solid fa-scale-balanced"></i> Related Decision: Approved Feb 10</p>
            </div>`:""}
          </div>`;
        msgs.appendChild(d);
        msgs.scrollTop = msgs.scrollHeight;
      }
      function sendMsg() {
        const q = inp.value.trim();
        if (!q) return;
        addMsg(q, true);
        inp.value = "";
        setTimeout(() => addMsg("I've analyzed the relevant meetings. Here's what I found based on the organization's knowledge base and meeting history.", false), 600);
      }
      send.onclick = sendMsg;
      inp.onkeydown = (e) => { if(e.key==="Enter") sendMsg(); };
      document.querySelectorAll("[data-aichatq]").forEach(b => {
        b.onclick = () => { inp.value = b.textContent; sendMsg(); };
      });
    }, 50);
  };

  // ============ 3. DECISION CENTER ============
  window.__nf["screen-decision-center"] = function() {
    const c = el("screen-decision-center");
    if (!c) return;
    const LD = _getLD();
    let tabs = ["Active","Completed","Changed","Archived","Conflict Detection"];
    let activeTab = c.__dcTab || "Active";
    c.innerHTML = `
      <div class="nf-screen-header">
        <h2 style="font-family:var(--font-display);font-size:1.3rem;color:#f3f4f6;display:flex;align-items:center;gap:0.6rem;"><i class="fa-solid fa-scale-balanced" style="color:#f59e0b;"></i> Decision Center <span style="font-size:0.7rem;background:rgba(245,158,11,0.15);color:#f59e0b;padding:0.15rem 0.5rem;border-radius:20px;">Decision Ledger</span></h2>
        <p style="font-size:0.8rem;color:#8899b0;margin:0.3rem 0 0 2.1rem;">Every important decision stored separately</p>
      </div>
      <div style="background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;margin-top:1rem;overflow:auto;">
        <table style="width:100%;border-collapse:collapse;font-size:0.78rem;">
          <thead><tr style="background:rgba(255,255,255,0.03);">
            <th style="padding:0.65rem 0.75rem;text-align:left;color:#8899b0;font-weight:600;">Decision</th>
            <th style="padding:0.65rem 0.75rem;text-align:left;color:#8899b0;font-weight:600;">Project</th>
            <th style="padding:0.65rem 0.75rem;text-align:left;color:#8899b0;font-weight:600;">Owner</th>
            <th style="padding:0.65rem 0.75rem;text-align:left;color:#8899b0;font-weight:600;">Date</th>
            <th style="padding:0.65rem 0.75rem;text-align:left;color:#8899b0;font-weight:600;">Priority</th>
            <th style="padding:0.65rem 0.75rem;text-align:left;color:#8899b0;font-weight:600;">Status</th>
            <th style="padding:0.65rem 0.75rem;text-align:left;color:#8899b0;font-weight:600;">Confidence</th>
            <th style="padding:0.65rem 0.75rem;text-align:left;color:#8899b0;font-weight:600;">Implementation</th>
          </tr></thead>
          <tbody>${LD.decisions.map(d => `
            <tr style="border-top:1px solid rgba(255,255,255,0.05);">
              <td style="padding:0.65rem 0.75rem;color:#e8edf5;">${esc(d.decision)}</td>
              <td style="padding:0.65rem 0.75rem;color:#c8d0dc;">${esc(d.project)}</td>
              <td style="padding:0.65rem 0.75rem;color:#a5b4fc;">${esc(d.owner)}</td>
              <td style="padding:0.65rem 0.75rem;color:#8899b0;">${d.date}</td>
              <td style="padding:0.65rem 0.75rem;"><span style="background:${d.priority==="High"?"rgba(244,63,94,0.15)":"rgba(245,158,11,0.15)"};color:${d.priority==="High"?"#fb7185":"#fbbf24"};padding:0.15rem 0.5rem;border-radius:4px;font-size:0.7rem;">${d.priority}</span></td>
              <td style="padding:0.65rem 0.75rem;"><span style="background:${d.status==="Completed"?"rgba(16,185,129,0.15)":d.status==="Active"?"rgba(99,102,241,0.15)":"rgba(245,158,11,0.15)"};color:${d.status==="Completed"?"#6ee7b7":d.status==="Active"?"#a5b4fc":"#fbbf24"};padding:0.15rem 0.5rem;border-radius:4px;font-size:0.7rem;">${d.status}</span></td>
              <td style="padding:0.65rem 0.75rem;color:#e8edf5;">${d.confidence}%</td>
              <td style="padding:0.65rem 0.75rem;"><span style="background:${d.impl==="Completed"?"rgba(16,185,129,0.15)":d.impl==="In Progress"?"rgba(99,102,241,0.15)":"rgba(255,255,255,0.05)"};color:${d.impl==="Completed"?"#6ee7b7":d.impl==="In Progress"?"#a5b4fc":"#8899b0"};padding:0.15rem 0.5rem;border-radius:4px;font-size:0.7rem;">${d.impl}</span></td>
            </tr>`).join("")}
          </tbody>
        </table>
      </div>
      <div class="nf-tabs" style="margin-top:1rem;" id="dc-tabs">${tabs.map(t => `<button class="nf-tab ${t===activeTab?'nf-tab-active':''}" data-dctab="${t}">${t}</button>`).join("")}</div>
      <div id="dc-tab-content" style="margin-top:0.75rem;"></div>`;
    c.__dcTab = activeTab;
    _renderDCTab(activeTab);
  };

  function _renderDCTab(tab) {
    const area = el("dc-tab-content");
    if (!area) return;
    const LD = _getLD();
    const filtered = LD.decisions.filter(d => d.status===tab || (tab==="Conflict Detection"));
    if (tab === "Conflict Detection") {
      area.innerHTML = `<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:0.75rem;">
        ${["Deadline conflicts","Budget conflicts","Requirement conflicts","Technology conflicts","Task conflicts","Resource conflicts","Approval conflicts"].map(c =>
          `<div style="background:rgba(15,22,42,0.65);border:1px solid rgba(244,63,94,0.15);border-radius:14px;padding:1rem;">
            <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem;">
              <i class="fa-solid fa-triangle-exclamation" style="color:#fb7185;font-size:0.85rem;"></i>
              <h4 style="color:#f3f4f6;font-size:0.82rem;margin:0;">${c}</h4>
            </div>
            <p style="color:#8899b0;font-size:0.73rem;">${Math.floor(Math.random()*5)+1} potential conflicts detected. Review recommended.</p>
            <button class="btn btn-secondary" style="margin-top:0.5rem;padding:0.3rem 0.7rem;font-size:0.7rem;width:100%;justify-content:center;">Resolve</button>
          </div>`
        ).join("")}
      </div>
      <div style="margin-top:1rem;background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.25rem;">
        <h4 style="color:#f3f4f6;font-size:0.9rem;margin-bottom:0.75rem;"><i class="fa-solid fa-timeline" style="color:#818cf8;margin-right:0.4rem;"></i> Decision Timeline</h4>
        <div style="display:flex;flex-direction:column;gap:0.5rem;position:relative;padding-left:1.5rem;">
          <div style="position:absolute;left:0.5rem;top:0.3rem;bottom:0.3rem;width:2px;background:rgba(99,102,241,0.3);"></div>
          ${["Created","Updated","Approved","Implemented","Completed","Archived"].map((s,i) =>
            `<div style="display:flex;align-items:center;gap:0.5rem;position:relative;">
              <div style="width:10px;height:10px;border-radius:50%;background:${i===3?"#f59e0b":"rgba(99,102,241,0.5)"};border:2px solid ${i===3?"#f59e0b":"rgba(99,102,241,0.3)"};margin-left:-1rem;flex-shrink:0;"></div>
              <span style="color:${i===3?"#fbbf24":"#c8d0dc"};font-size:0.78rem;">${s}</span>
            </div>`
          ).join("")}
        </div>
      </div>`;
    } else {
      area.innerHTML = filtered.length ? filtered.map(d => `
        <div class="nf-dc-item" data-dcdecision="${esc(d.decision)}" style="background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:0.75rem 1rem;margin-bottom:0.5rem;cursor:pointer;">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <div><p style="color:#f3f4f6;font-size:0.82rem;">${esc(d.decision)}</p><p style="color:#8899b0;font-size:0.72rem;">${esc(d.project)} · ${esc(d.owner)} · ${d.date}</p></div>
            <div style="display:flex;align-items:center;gap:0.5rem;">
              <span style="background:rgba(16,185,129,0.15);color:#6ee7b7;padding:0.15rem 0.5rem;border-radius:4px;font-size:0.7rem;">${d.confidence}%</span>
              <i class="fa-solid fa-chevron-right" style="color:#8899b0;font-size:0.7rem;transition:transform 0.2s;"></i>
            </div>
          </div>
          <div class="nf-dc-detail" style="display:none;margin-top:0.5rem;padding-top:0.5rem;border-top:1px solid rgba(255,255,255,0.06);font-size:0.78rem;color:#c8d0dc;">
            <p><strong style="color:#f3f4f6;">Reason:</strong> ${esc(d.reason)}</p>
            <p style="margin-top:0.3rem;"><strong style="color:#f3f4f6;">Implementation:</strong> ${d.impl}</p>
            <p style="margin-top:0.3rem;"><strong style="color:#f3f4f6;">Priority:</strong> ${d.priority}</p>
            <div style="margin-top:0.5rem;display:flex;gap:0.3rem;">
              <span style="background:rgba(99,102,241,0.1);color:#a5b4fc;padding:0.15rem 0.5rem;border-radius:4px;font-size:0.68rem;"><i class="fa-solid fa-tag"></i> ${d.project}</span>
              <span style="background:rgba(245,158,11,0.1);color:#fbbf24;padding:0.15rem 0.5rem;border-radius:4px;font-size:0.68rem;"><i class="fa-solid fa-user"></i> ${d.owner}</span>
            </div>
          </div>
        </div>`).join("") : `<p style="color:#8899b0;text-align:center;padding:1rem;font-size:0.85rem;">No ${tab.toLowerCase()} decisions.</p>`;
      setTimeout(() => {
        document.querySelectorAll(".nf-dc-item").forEach(item => {
          item.onclick = function() {
            const detail = this.querySelector(".nf-dc-detail");
            const arrow = this.querySelector(".fa-chevron-right");
            if (detail.style.display === "none") {
              detail.style.display = "block";
              arrow.style.transform = "rotate(90deg)";
            } else {
              detail.style.display = "none";
              arrow.style.transform = "";
            }
          };
        });
      }, 50);
    }
  }

  document.addEventListener("click", function(e) {
    const tab = e.target.closest("[data-dctab]");
    if (!tab) return;
    const c = el("screen-decision-center");
    if (!c) return;
    c.__dcTab = tab.textContent;
    document.querySelectorAll("[data-dctab]").forEach(t => t.classList.remove("nf-tab-active"));
    tab.classList.add("nf-tab-active");
    _renderDCTab(tab.textContent);
  });

  // ============ 4. HISTORICAL ANALYTICS (Updated - Analysis & Project Intelligence) ============
  window.__nf["screen-historical-analytics"] = function() {
    const c = el("screen-historical-analytics");
    if (!c) return;
    const LD = _getLD();
    const ms = (window.meetings&&window.meetings.length>0)?window.meetings:[];
    const allTasks = ms.flatMap(m=>m.actionItems||[]);
    const compTasks = allTasks.filter(t=>t.status==='Completed').length;
    const taskCompletionRate = allTasks.length ? Math.round(compTasks/allTasks.length*100) : 82;
    const topCats = [...new Set(ms.map(m=>m.category||'General'))].slice(0,5);
    const catCounts = topCats.map(c => ms.filter(m=>(m.category||'General')===c).length);
    const projects = DATA.projects || [];
    c.innerHTML = `
      <div class="nf-screen-header">
        <h2 style="font-family:var(--font-display);font-size:1.3rem;color:#f3f4f6;display:flex;align-items:center;gap:0.6rem;"><i class="fa-solid fa-chart-simple" style="color:#06b6d4;"></i> Historical Analytics <span style="font-size:0.7rem;background:rgba(6,182,212,0.15);color:#06b6d4;padding:0.15rem 0.5rem;border-radius:20px;">Trends & Insights</span></h2>
        <p style="font-size:0.8rem;color:#8899b0;margin:0.3rem 0 0 2.1rem;">Analyze trends and project performance over time</p>
      </div>
      <div class="nf-tabs" style="margin-top:1rem;">
        <button class="nf-tab nf-tab-active" data-hatab="analysis">Analysis</button>
        <button class="nf-tab" data-hatab="project-intelligence">Project Intelligence</button>
      </div>
      <div id="ha-content" style="margin-top:1rem;"></div>`;
    const showHA = (tab) => {
      const area = el("ha-content");
      if (!area) return;
      if (tab === "analysis") {
        area.innerHTML = `
          <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:0.75rem;">
            ${[{l:"Meeting Trends",v:ms.length+" meetings this period",c:"#818cf8",pct:Math.min(ms.length*5,100)},{l:"Attendance Trends",v:ms.length>0?Math.round(ms.reduce((s,m)=>(m.attendees||[]).length,0)/ms.length)+" avg attendees":"No data",c:"#34d399",pct:ms.length>0?Math.min(Math.round(ms.reduce((s,m)=>(m.attendees||[]).length,0)/ms.length)*15,100):0},{l:"Productivity Trends",v:taskCompletionRate+"% task completion",c:"#fbbf24",pct:taskCompletionRate},{l:"Communication Trends",v:LD.people.length+" active participants",c:"#f472b6",pct:Math.min(LD.people.length*15,100)}].map(ch =>
              `<div style="background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1rem;">
                <p style="font-size:0.78rem;color:#8899b0;margin-bottom:0.5rem;font-weight:600;">${ch.l}</p>
                <div style="display:flex;align-items:baseline;gap:0.5rem;margin-bottom:0.5rem;"><span style="font-size:1.3rem;font-weight:700;color:${ch.c};">${ch.v.split(" ")[0]}</span><span style="font-size:0.72rem;color:var(--text-muted);">${ch.v.substring(ch.v.indexOf(" ")+1)}</span></div>
                <div style="height:6px;background:rgba(255,255,255,0.06);border-radius:3px;"><div style="height:100%;width:${ch.pct}%;background:${ch.c};border-radius:3px;"></div></div>
              </div>`
            ).join("")}
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;margin-top:1rem;">
            <div style="background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.25rem;">
              <h4 style="color:#f3f4f6;font-size:0.85rem;margin-bottom:0.75rem;"><i class="fa-solid fa-chart-bar" style="color:#818cf8;margin-right:0.3rem;"></i> Department Comparisons</h4>
              ${DATA.departments.slice(0,4).map(d => `<div style="margin-bottom:0.5rem;"><div style="display:flex;justify-content:space-between;font-size:0.72rem;color:var(--text-muted);margin-bottom:0.15rem;"><span>${esc(d.name)}</span><span>${d.health}%</span></div><div style="height:4px;background:rgba(255,255,255,0.06);border-radius:2px;"><div style="height:100%;width:${d.health}%;background:${d.color};border-radius:2px;"></div></div></div>`).join("")}
            </div>
            <div style="background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.25rem;">
              <h4 style="color:#f3f4f6;font-size:0.85rem;margin-bottom:0.75rem;"><i class="fa-solid fa-wand-magic-sparkles" style="color:#f59e0b;margin-right:0.3rem;"></i> AI-Generated Insights</h4>
              <div style="display:flex;flex-direction:column;gap:0.4rem;">
                ${(LD.aiInsights.length?LD.aiInsights:["Meeting productivity trending upward","Task completion rate stable at "+taskCompletionRate+"%","Team engagement improving across departments"]).slice(0,4).map(s =>
                  `<div style="background:rgba(245,158,11,0.06);border-left:3px solid #f59e0b;padding:0.4rem 0.6rem;border-radius:0 6px 6px 0;font-size:0.75rem;color:#e8edf5;">${esc(s)}</div>`
                ).join("")}
              </div>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.75rem;margin-top:0.75rem;">
            <div style="background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1rem;text-align:center;"><span style="font-size:1.2rem;font-weight:700;color:#818cf8;">${ms.length}</span><p style="font-size:0.68rem;color:var(--text-muted);margin-top:0.2rem;">Monthly Stats</p></div>
            <div style="background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1rem;text-align:center;"><span style="font-size:1.2rem;font-weight:700;color:#34d399;">${Math.round(ms.length*2.5)}</span><p style="font-size:0.68rem;color:var(--text-muted);margin-top:0.2rem;">Yearly Stats</p></div>
            <div style="background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1rem;text-align:center;"><span style="font-size:1.2rem;font-weight:700;color:#fbbf24;">${topCats.slice(0,3).join(", ")||"General"}</span><p style="font-size:0.68rem;color:var(--text-muted);margin-top:0.2rem;">Top Categories</p></div>
          </div>`;
      } else {
        area.innerHTML = `
          <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:0.75rem;">
            ${projects.map(p => {
              const completedMilestones = Math.floor(Math.random()*4)+2;
              const delayedMilestones = Math.floor(Math.random()*3);
              return `<div style="background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.25rem;">
                <h4 style="color:#f3f4f6;font-size:0.85rem;margin-bottom:0.5rem;">${esc(p.name)}</h4>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;font-size:0.72rem;">
                  <div style="padding:0.4rem;background:rgba(99,102,241,0.05);border-radius:6px;"><span style="color:var(--text-muted);">Timeline</span><br><span style="color:#e8edf5;font-weight:600;">${esc(p.deadline)}</span></div>
                  <div style="padding:0.4rem;background:rgba(99,102,241,0.05);border-radius:6px;"><span style="color:var(--text-muted);">Progress</span><br><span style="color:${p.progress>80?"#34d399":p.progress>40?"#fbbf24":"#f43f5e"};font-weight:600;">${p.progress}%</span></div>
                  <div style="padding:0.4rem;background:rgba(16,185,129,0.05);border-radius:6px;"><span style="color:var(--text-muted);">Completed</span><br><span style="color:#6ee7b7;font-weight:600;">${completedMilestones} milestones</span></div>
                  <div style="padding:0.4rem;background:rgba(244,63,94,0.05);border-radius:6px;"><span style="color:var(--text-muted);">Delayed</span><br><span style="color:${delayedMilestones>0?"#fca5a5":"#6ee7b7"};font-weight:600;">${delayedMilestones} milestones</span></div>
                </div>
                <div style="margin-top:0.5rem;font-size:0.68rem;color:var(--text-muted);">Team: ${esc(p.lead)} · Budget: $${p.spent.toLocaleString()}/${p.budget.toLocaleString()}</div>
              </div>`;
            }).join("")}
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;margin-top:1rem;">
            <div style="background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.25rem;">
              <h4 style="color:#f3f4f6;font-size:0.85rem;margin-bottom:0.5rem;">Resource Utilization</h4>
              <div style="display:flex;flex-direction:column;gap:0.4rem;">${DATA.employees.slice(0,4).map(e => `<div><div style="display:flex;justify-content:space-between;font-size:0.7rem;color:var(--text-muted);margin-bottom:0.15rem;"><span>${esc(e.name)}</span><span>${e.workload}%</span></div><div style="height:4px;background:rgba(255,255,255,0.06);border-radius:2px;"><div style="height:100%;width:${e.workload}%;background:${e.workload>80?"#f43f5e":e.workload>60?"#fbbf24":"#34d399"};border-radius:2px;"></div></div></div>`).join("")}</div>
            </div>
            <div style="background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.25rem;">
              <h4 style="color:#f3f4f6;font-size:0.85rem;margin-bottom:0.5rem;">Risk History</h4>
              <div style="display:flex;flex-direction:column;gap:0.4rem;">${projects.map(p => `<div style="display:flex;justify-content:space-between;padding:0.3rem 0;border-bottom:1px solid rgba(255,255,255,0.04);font-size:0.72rem;"><span style="color:#e8edf5;">${esc(p.name)}</span><span style="color:${p.risk==="Low"?"#34d399":p.risk==="Medium"?"#fbbf24":"#f43f5e"};">${p.risk} Risk</span></div>`).join("")}</div>
            </div>
          </div>
          <div style="margin-top:1rem;background:rgba(245,158,11,0.06);border:1px solid rgba(245,158,11,0.15);border-radius:12px;padding:1rem;">
            <p style="font-size:0.8rem;color:#fbbf24;"><i class="fa-solid fa-robot" style="margin-right:0.3rem;"></i> AI Project Insight: ${projects.length} projects tracked. ${projects.filter(p=>p.risk==="High").length} high-risk projects detected. Overall completion rate: ${Math.round(projects.reduce((s,p)=>s+p.progress,0)/projects.length)}%</p>
          </div>`;
      }
    };
    showHA("analysis");
    document.querySelectorAll("[data-hatab]").forEach(t => {
      t.onclick = function() {
        document.querySelectorAll("[data-hatab]").forEach(x => { x.classList.remove("nf-tab-active"); x.style.background="transparent";x.style.color="var(--text-secondary)"; });
        this.classList.add("nf-tab-active"); this.style.background="rgba(99,102,241,0.15)"; this.style.color="#a5b4fc";
        showHA(this.dataset.hatab);
      };
    });
  };

  // ============ 5. PROJECT HEALTH ============
  window.__nf["screen-project-health"] = function() {
    const c = el("screen-project-health");
    if (!c) return;
    const h = _getLD().projectHealth;
    c.innerHTML = `
      <div class="nf-screen-header">
        <h2 style="font-family:var(--font-display);font-size:1.3rem;color:#f3f4f6;display:flex;align-items:center;gap:0.6rem;"><i class="fa-solid fa-heart-pulse" style="color:#fb7185;"></i> Project Health <span style="font-size:0.7rem;background:rgba(244,63,94,0.15);color:#fb7185;padding:0.15rem 0.5rem;border-radius:20px;">Health Dashboard</span></h2>
        <p style="font-size:0.8rem;color:#8899b0;margin:0.3rem 0 0 2.1rem;">Predict and monitor project success</p>
      </div>
      <div style="display:flex;gap:1rem;margin-top:1rem;align-items:center;">
        <div style="width:160px;height:160px;border-radius:50%;background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);display:flex;flex-direction:column;align-items:center;justify-content:center;flex-shrink:0;">
          <div style="position:relative;width:120px;height:120px;">
            <svg viewBox="0 0 36 36" style="width:100%;height:100%;transform:rotate(-90deg);">
              <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="3"/>
              <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="${h.score>80?"#10b981":h.score>60?"#f59e0b":"#ef4444"}" stroke-width="3" stroke-dasharray="${h.score}, ${100-h.score}"/>
            </svg>
            <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;">
              <span style="font-size:1.8rem;font-weight:700;color:#f3f4f6;">${h.score}%</span>
              <span style="font-size:0.65rem;color:#8899b0;">Overall Health</span>
            </div>
          </div>
        </div>
        <div style="flex:1;display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:0.75rem;">
          ${[{l:"Completed Tasks",v:h.completed,ic:"list-check",c:"#10b981"},{l:"Delayed Tasks",v:h.delayed,ic:"clock",c:"#f59e0b"},{l:"Pending Approvals",v:h.pendingApprovals,ic:"hourglass",c:"#818cf8"},{l:"Meeting Attendance",v:h.attendance+"%",ic:"users",c:"#06b6d4"},{l:"Risk Score",v:h.riskScore+"/100",ic:"shield",c:h.riskScore>50?"#fb7185":"#6ee7b7"},{l:"Budget Health",v:h.budgetHealth+"%",ic:"wallet",c:"#a5b4fc"},{l:"Sprint Progress",v:h.sprintProgress+"%",ic:"arrow-trend-up",c:"#67e8f9"},{l:"Blocked Tasks",v:h.blockedTasks,ic:"ban",c:"#fb7185"}].map(w =>
            `<div style="background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:0.85rem;">
              <div style="display:flex;align-items:center;gap:0.4rem;margin-bottom:0.3rem;"><i class="fa-solid fa-${w.ic}" style="color:${w.c};font-size:0.7rem;"></i><span style="font-size:0.7rem;color:#8899b0;">${w.l}</span></div>
              <span style="font-size:1.1rem;font-weight:700;color:${w.c};">${w.v}</span>
            </div>`
          ).join("")}
        </div>
      </div>
      <div style="margin-top:1rem;background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.25rem;">
        <h4 style="color:#f3f4f6;font-size:0.9rem;margin-bottom:0.75rem;"><i class="fa-solid fa-wand-magic-sparkles" style="color:#f59e0b;margin-right:0.4rem;"></i> AI Suggestions</h4>
        <div style="display:flex;flex-direction:column;gap:0.4rem;">
          ${[h.blockedTasks > 0 ? "Conduct review meeting to address "+h.blockedTasks+" blockers" : "Good - no blockers detected", "Increase testing coverage to reduce risks", "Focus on "+h.completed+" completed tasks", "Resolve "+h.pendingApprovals+" pending approvals", "Improve sprint progress from "+h.sprintProgress+"%"].map(s =>
            `<div style="background:rgba(245,158,11,0.06);border-left:3px solid #f59e0b;padding:0.5rem 0.65rem;border-radius:0 6px 6px 0;font-size:0.78rem;color:#e8edf5;display:flex;align-items:center;gap:0.5rem;"><i class="fa-solid fa-lightbulb" style="color:#f59e0b;font-size:0.7rem;flex-shrink:0;"></i> ${s}</div>`
          ).join("")}
        </div>
      </div>`;
  };

  // ============ 6. KNOWLEDGE GRAPH ============
  window.__nf["screen-knowledge-graph"] = function() {
    const c = el("screen-knowledge-graph");
    if (!c) return;
    const LD = _getLD();
    const ms = (window.meetings && window.meetings.length > 0) ? window.meetings : [];
    const totalMeetings = ms.length;
    const allTasks = ms.flatMap(m => m.actionItems||[]);
    const completedTasks = allTasks.filter(t => t.status==='Completed').length;
    const totalDecisions = LD.decisions.length;
    const allAttendees = [...new Set(ms.flatMap(m => m.attendees||[]))];
    const totalTopics = LD.topics.length;
    const totalDocs = totalMeetings * 2;
    const totalProjects = [...new Set(ms.map(m => m.category||'General'))].length;
    const nodes = ["Meetings","Projects","People","Tasks","Topics","Documents","Decisions","Departments","Clients"];
    c.innerHTML = `
      <div class="nf-screen-header">
        <h2 style="font-family:var(--font-display);font-size:1.3rem;color:#f3f4f6;display:flex;align-items:center;gap:0.6rem;"><i class="fa-solid fa-diagram-project" style="color:#a78bfa;"></i> Knowledge Graph <span style="font-size:0.7rem;background:rgba(167,139,250,0.15);color:#a78bfa;padding:0.15rem 0.5rem;border-radius:20px;">Visual Relationships</span></h2>
        <p style="font-size:0.8rem;color:#8899b0;margin:0.3rem 0 0 2.1rem;">Visual relationship between everything in your organization</p>
      </div>
      <div style="display:flex;gap:1rem;margin-top:1rem;">
        <div style="flex:1;min-height:450px;background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.5rem;position:relative;overflow:hidden;">
          <div class="nf-graph-container" style="position:relative;width:100%;height:420px;display:flex;align-items:center;justify-content:center;">
            <div style="position:relative;width:360px;height:360px;">
              ${nodes.map((n,i) => {
                const angle = (i / nodes.length) * 2 * Math.PI - Math.PI/2;
                const r = 150;
                const x = 180 + r * Math.cos(angle);
                const y = 180 + r * Math.sin(angle);
                const colors = ["#818cf8","#10b981","#f59e0b","#06b6d4","#a78bfa","#f472b6","#fb7185","#34d399","#fbbf24"];
                return `<div class="nf-graph-node" data-ngnode="${n}" style="position:absolute;left:${x-35}px;top:${y-35}px;width:70px;height:70px;border-radius:50%;background:rgba(15,22,42,0.9);border:2px solid ${colors[i]};display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all 0.3s;z-index:2;box-shadow:0 0 15px ${colors[i]}40;">
                  <span style="font-size:0.6rem;color:#c8d0dc;text-align:center;line-height:1.2;font-weight:600;">${n}</span>
                </div>`;
              }).join("")}
              ${[0,1,2,3,4,5,6,7,8].map(i => {
                const connections = [[1,2],[0,3],[4,5],[2,6],[7,8]];
                return connections.map(([a,b]) => {
                  const angleA = (a/9)*2*Math.PI - Math.PI/2;
                  const angleB = (b/9)*2*Math.PI - Math.PI/2;
                  const r = 150;
                  const x1 = 180 + r * Math.cos(angleA);
                  const y1 = 180 + r * Math.sin(angleA);
                  const x2 = 180 + r * Math.cos(angleB);
                  const y2 = 180 + r * Math.sin(angleB);
                  return `<svg style="position:absolute;inset:0;width:100%;height:100%;z-index:1;pointer-events:none;"><line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="rgba(99,102,241,0.15)" stroke-width="1.5"/></svg>`;
                }).join("");
              }).join("")}
            </div>
          </div>
        </div>
        <div id="ng-detail" style="width:280px;flex-shrink:0;background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.25rem;">
          <p style="color:#8899b0;font-size:0.8rem;text-align:center;padding:2rem 0;">Click a node to see<br>connected items</p>
        </div>
      </div>`;
    setTimeout(() => {
      document.querySelectorAll("[data-ngnode]").forEach(n => {
        n.onclick = function() {
          const label = this.textContent.trim();
          const details = {
            "Meetings":totalMeetings+" connected meetings<br>"+totalTopics+" related topics<br>"+allAttendees.length+" participants",
            "Projects":totalProjects+" active projects<br>"+allTasks.length+" associated tasks<br>",
            "People":allAttendees.length+" team members<br>"+totalMeetings+" total meetings attended",
            "Tasks":allTasks.length+" total tasks<br>"+completedTasks+" completed<br>"+(allTasks.length-completedTasks)+" pending",
            "Topics":totalTopics+" tracked topics<br>Most discussed: "+(LD.topics.slice(0,3).join(", ")||"General"),
            "Documents":totalDocs+" total documents<br>"+(totalMeetings)+" meeting transcripts",
            "Decisions":totalDecisions+" decisions made<br>"+LD.decisions.filter(d=>d.status==='Completed').length+" implemented",
            "Departments":[...new Set(ms.flatMap(m=>(m.attendees||[]).map(a=>a.split(/\s*\(|\s+-\s+/).pop()||'General')))].join(", ")||"Engineering, Product, Design",
            "Clients":Math.max(1,Math.floor(totalMeetings/3))+" active clients<br>"+Math.max(1,Math.floor(totalMeetings/5))+" prospective"
          };
          el("ng-detail").innerHTML = `
            <h4 style="color:#f3f4f6;font-size:0.9rem;margin-bottom:0.75rem;"><i class="fa-solid fa-circle-nodes" style="color:#a78bfa;margin-right:0.4rem;"></i> ${label}</h4>
            <div style="font-size:0.78rem;color:#c8d0dc;line-height:1.8;">${details[label]||"No details available"}</div>
            <div style="margin-top:0.75rem;display:flex;flex-wrap:wrap;gap:0.3rem;">
              ${["Connected Meetings","Related Tasks","Decisions","People"].map(t =>
                `<span style="background:rgba(99,102,241,0.1);color:#a5b4fc;font-size:0.65rem;padding:0.2rem 0.5rem;border-radius:4px;">${t}</span>`
              ).join("")}
            </div>`;
        };
      });
    }, 50);
  };

  // ============ 7. MEETING COACH ============
  window.__nf["screen-meeting-coach"] = function() {
    const c = el("screen-meeting-coach");
    if (!c) return;
    const cd = _getLD().coachData;
    c.innerHTML = `
      <div class="nf-screen-header">
        <h2 style="font-family:var(--font-display);font-size:1.3rem;color:#f3f4f6;display:flex;align-items:center;gap:0.6rem;"><i class="fa-solid fa-chalkboard-user" style="color:#10b981;"></i> Meeting Coach <span style="font-size:0.7rem;background:rgba(16,185,129,0.15);color:#10b981;padding:0.15rem 0.5rem;border-radius:20px;">Effectiveness Score</span></h2>
        <p style="font-size:0.8rem;color:#8899b0;margin:0.3rem 0 0 2.1rem;">Improve meeting effectiveness with AI-powered coaching</p>
      </div>
      <div style="display:flex;gap:1rem;margin-top:1rem;">
        <div style="width:180px;flex-shrink:0;display:flex;flex-direction:column;align-items:center;background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.5rem;">
          <div style="position:relative;width:130px;height:130px;">
            <svg viewBox="0 0 36 36" style="width:100%;height:100%;transform:rotate(-90deg);">
              <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="3"/>
              <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#10b981" stroke-width="3" stroke-dasharray="${cd.score}, ${100-cd.score}"/>
            </svg>
            <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;">
              <span style="font-size:1.8rem;font-weight:700;color:#f3f4f6;">${cd.score}</span>
              <span style="font-size:0.6rem;color:#8899b0;">/100</span>
            </div>
          </div>
          <p style="font-size:0.75rem;color:#6ee7b7;margin-top:0.5rem;">Excellent!</p>
        </div>
        <div style="flex:1;display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:0.5rem;">
          ${[{l:"Participation",v:cd.participation+"%"},{l:"Interruptions",v:cd.interruptions},{l:"Speaking Balance",v:cd.speakingBalance+"%"},{l:"Questions Asked",v:cd.questionsAsked},{l:"Ideas Shared",v:cd.ideasShared},{l:"Decision Clarity",v:cd.decisionClarity+"%"},{l:"Focus Score",v:cd.focusScore+"%"},{l:"Time Usage",v:cd.timeUsage+"%"},{l:"Communication",v:cd.communicationScore+"%"}].map(a =>
            `<div style="background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:0.75rem;">
              <p style="font-size:0.68rem;color:#8899b0;margin-bottom:0.3rem;">${a.l}</p>
              <div style="display:flex;align-items:center;gap:0.5rem;">
                <div style="flex:1;height:4px;background:rgba(255,255,255,0.06);border-radius:2px;"><div style="height:100%;width:${typeof a.v==="string"?parseInt(a.v):a.v}%;background:${parseInt(a.v)>70?"#10b981":parseInt(a.v)>40?"#f59e0b":"#ef4444"};border-radius:2px;"></div></div>
                <span style="font-size:0.75rem;color:#e8edf5;font-weight:600;min-width:35px;text-align:right;">${a.v}</span>
              </div>
            </div>`
          ).join("")}
        </div>
      </div>
      <div style="margin-top:1rem;background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.25rem;">
        <h4 style="color:#f3f4f6;font-size:0.9rem;margin-bottom:0.75rem;"><i class="fa-solid fa-wand-magic-sparkles" style="color:#f59e0b;margin-right:0.4rem;"></i> AI Coaching Suggestions</h4>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.4rem;">
          ${[cd.interruptions > 2 ? "Reduce interruptions (currently "+cd.interruptions+")" : "Good - low interruption rate", cd.speakingBalance < 70 ? "Improve speaking balance from "+cd.speakingBalance+"%" : "Speaking balance is good", cd.focusScore < 80 ? "Improve focus score from "+cd.focusScore : "Focus score is strong", cd.timeUsage < 75 ? "Improve time usage from "+cd.timeUsage+"%" : "Time usage is good", cd.participation < 75 ? "Increase participation from "+cd.participation+"%" : "Participation is healthy", cd.decisionClarity < 80 ? "Improve decision clarity from "+cd.decisionClarity+"%" : "Decision clarity is excellent"].map(s =>
            `<div style="background:rgba(245,158,11,0.06);border-left:3px solid #f59e0b;padding:0.5rem 0.65rem;border-radius:0 6px 6px 0;font-size:0.78rem;color:#e8edf5;"><i class="fa-solid fa-lightbulb" style="color:#f59e0b;font-size:0.7rem;margin-right:0.4rem;"></i>${s}</div>`
          ).join("")}
        </div>
      </div>`;
  };

  // ============ 8. AUTO DOCUMENTATION ============
  window.__nf["screen-auto-documentation"] = function() {
    const c = el("screen-auto-documentation");
    if (!c) return;
    const docs = [
      {l:"Minutes of Meeting",ic:"file-lines",c:"#818cf8"},
      {l:"Project Report",ic:"folder-open",c:"#10b981"},
      {l:"Sprint Report",ic:"arrow-trend-up",c:"#06b6d4"},
      {l:"Weekly Report",ic:"calendar-week",c:"#a78bfa"},
      {l:"Monthly Report",ic:"calendar",c:"#f472b6"},
      {l:"Client Report",ic:"briefcase",c:"#f59e0b"},
      {l:"Executive Summary",ic:"crown",c:"#fbbf24"},
      {l:"Technical Documentation",ic:"code",c:"#34d399"},
      {l:"SRS Document",ic:"book",c:"#60a5fa"},
      {l:"Release Notes",ic:"rocket",c:"#fb7185"},
      {l:"Presentation",ic:"presentation-screen",c:"#c084fc"},
      {l:"Status Report",ic:"chart-line",c:"#67e8f9"}
    ];
    c.innerHTML = `
      <div class="nf-screen-header">
        <h2 style="font-family:var(--font-display);font-size:1.3rem;color:#f3f4f6;display:flex;align-items:center;gap:0.6rem;"><i class="fa-solid fa-file-pen" style="color:#a78bfa;"></i> Auto Documentation <span style="font-size:0.7rem;background:rgba(167,139,250,0.15);color:#a78bfa;padding:0.15rem 0.5rem;border-radius:20px;">AI Generated</span></h2>
        <p style="font-size:0.8rem;color:#8899b0;margin:0.3rem 0 0 2.1rem;">Generate professional documents automatically from meeting data</p>
      </div>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:0.75rem;margin-top:1rem;">
        ${docs.map(d => `
          <div class="nf-doc-card" style="background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.25rem;text-align:center;cursor:pointer;transition:var(--transition-fast);">
            <i class="fa-solid fa-${d.ic}" style="font-size:1.5rem;color:${d.c};margin-bottom:0.5rem;"></i>
            <p style="font-size:0.82rem;color:#e8edf5;margin-bottom:0.5rem;">${d.l}</p>
            <button class="btn btn-primary nf-gen-btn" style="padding:0.35rem 0.75rem;font-size:0.72rem;width:100%;justify-content:center;"><i class="fa-solid fa-wand-magic-sparkles"></i> Generate</button>
            <div class="nf-gen-status" style="display:none;font-size:0.7rem;color:#6ee7b7;margin-top:0.4rem;"><i class="fa-solid fa-check-circle"></i> Generated!</div>
          </div>`).join("")}
      </div>
      <div id="doc-preview" style="display:none;margin-top:1rem;background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.5rem;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem;">
          <h4 id="doc-preview-title" style="color:#f3f4f6;font-size:0.9rem;margin:0;"></h4>
          <button class="btn btn-secondary" id="doc-preview-close" style="padding:0.3rem 0.7rem;font-size:0.72rem;"><i class="fa-solid fa-xmark"></i></button>
        </div>
        <div id="doc-preview-content" style="font-size:0.82rem;color:#c8d0dc;line-height:1.7;max-height:400px;overflow-y:auto;padding:0.5rem;background:rgba(0,0,0,0.2);border-radius:8px;white-space:pre-wrap;"></div>
        <div style="margin-top:0.75rem;display:flex;gap:0.5rem;">
          <button class="btn btn-primary" style="padding:0.4rem 1rem;font-size:0.75rem;"><i class="fa-solid fa-download"></i> Download</button>
          <button class="btn btn-secondary" style="padding:0.4rem 1rem;font-size:0.75rem;"><i class="fa-solid fa-share"></i> Share</button>
        </div>
      </div>`;
    setTimeout(() => {
      document.querySelectorAll(".nf-gen-btn").forEach(btn => {
        btn.onclick = function(e) {
          e.stopPropagation();
          const card = this.closest(".nf-doc-card");
          const label = card.querySelector("p").textContent;
          const status = card.querySelector(".nf-gen-status");
          this.textContent = "Generating...";
          this.disabled = true;
          setTimeout(() => {
            this.style.display = "none";
            status.style.display = "block";
            setTimeout(() => { status.style.display = "none"; this.style.display = ""; this.textContent = "Generate"; this.disabled = false; }, 2000);
            const preview = el("doc-preview");
            el("doc-preview-title").textContent = label + " - Generated";
            const mCount = (window.meetings&&window.meetings.length)||0;
            const tCount = mCount>0?window.meetings.flatMap(m=>m.actionItems||[]).length:23;
            const cCount = mCount>0?window.meetings.flatMap(m=>m.actionItems||[]).filter(t=>t.status==='Completed').length:18;
            el("doc-preview-content").textContent = `# ${label}\n\nGenerated: ${new Date().toLocaleString()}\n\n## Executive Summary\nThis document provides a comprehensive overview based on ${mCount} meetings, ${tCount} tasks, and ${cCount} completed actions.\n\n## Key Findings\n1. ${mCount||15} meetings analyzed for content generation\n2. ${tCount} total action items extracted\n3. ${cCount} tasks completed successfully\n\n## Action Items\n- Review pending tasks\n- Schedule follow-ups as needed\n- Update relevant documentation\n\n## Recommendations\nBased on analysis of ${mCount||15} meetings and ${tCount||23} tasks, the following recommendations are made:\n1. Continue tracking progress\n2. Address any blockers\n3. Plan for next cycle\n\n---\nAutomatically generated by EchoAction AI`;
            preview.style.display = "block";
          }, 1500);
        };
      });
      if (el("doc-preview-close")) el("doc-preview-close").onclick = () => { el("doc-preview").style.display = "none"; };
    }, 50);
  };

  // ============ 9. MEETING REPLAY ============
  window.__nf["screen-meeting-replay"] = function() {
    const c = el("screen-meeting-replay");
    if (!c) return;
    const allMeetings = (window.meetings && window.meetings.length > 0)
      ? window.meetings
      : (() => { try { const m = JSON.parse(localStorage.getItem("echoaction_meetings") || "[]"); return m; } catch(e) { return []; } })();
    const selectOptions = allMeetings.length > 0
      ? allMeetings.map((m,i) => `<option value="${i}">${m.title || "Meeting " + (i+1)}${m.date ? " - " + m.date : ""}</option>`).join("")
      : '<option>No meetings uploaded yet</option>';
    const durationText = allMeetings.length > 0 ? (allMeetings[0].duration || "45:00") : "00:00";
    const timelineItems = allMeetings.length > 0 ? allMeetings.slice(0,5).map((m,i) => ({
      time: m.date || "N/A",
      label: m.title || "Meeting " + (i+1),
      desc: ((m.summary && m.summary.overview) || "").substring(0,60) || "Meeting recording"
    })) : NF_DATA.timeline;
    c.innerHTML = `
      <div class="nf-screen-header">
        <h2 style="font-family:var(--font-display);font-size:1.3rem;color:#f3f4f6;display:flex;align-items:center;gap:0.6rem;"><i class="fa-solid fa-rotate-left" style="color:#60a5fa;"></i> Meeting Replay <span style="font-size:0.7rem;background:rgba(96,165,250,0.15);color:#60a5fa;padding:0.15rem 0.5rem;border-radius:20px;">Timeline</span></h2>
        <p style="font-size:0.8rem;color:#8899b0;margin:0.3rem 0 0 2.1rem;">Navigate through meeting timelines and jump to key moments</p>
      </div>
      <div style="display:flex;gap:1rem;margin-top:1rem;">
        <div style="flex:1;background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.25rem;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;">
            <select id="replay-meeting-select" class="form-input" style="width:auto;padding:0.4rem 0.75rem;font-size:0.8rem;max-width:300px;">
              ${selectOptions}
            </select>
            <div style="display:flex;align-items:center;gap:0.5rem;">
              <span style="font-size:0.75rem;color:#8899b0;" id="replay-duration">Duration: ${durationText}</span>
              <button class="btn btn-primary" id="replay-play-btn" style="padding:0.4rem 0.8rem;font-size:0.75rem;"><i class="fa-solid fa-play"></i> Play</button>
            </div>
          </div>
          <div style="position:relative;padding:0.5rem 0 0.5rem 1.5rem;">
            <div style="position:absolute;left:0.5rem;top:0;bottom:0;width:2px;background:rgba(99,102,241,0.3);"></div>
            ${timelineItems.map((t,i) => `
              <div class="nf-replay-item" data-replay="${i}" style="display:flex;align-items:flex-start;gap:0.75rem;padding:0.5rem 0;cursor:pointer;transition:var(--transition-fast);border-radius:8px;padding:0.5rem 0.75rem;margin-bottom:0.25rem;">
                <div style="width:50px;flex-shrink:0;font-size:0.7rem;color:#818cf8;font-weight:600;text-align:right;margin-top:0.1rem;">${t.time}</div>
                <div style="width:12px;height:12px;border-radius:50%;background:${i===timelineItems.length-1?"#10b981":"rgba(99,102,241,0.5)"};border:2px solid ${i===timelineItems.length-1?"#10b981":"rgba(99,102,241,0.3)"};margin-left:-0.75rem;flex-shrink:0;margin-top:0.1rem;"></div>
                <div>
                  <p style="color:#f3f4f6;font-size:0.82rem;font-weight:600;">${t.label}</p>
                  <p style="color:#8899b0;font-size:0.73rem;">${t.desc}</p>
                </div>
              </div>`).join("")}
          </div>
        </div>
        <div style="width:300px;flex-shrink:0;background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.25rem;">
          <h4 style="color:#f3f4f6;font-size:0.85rem;margin-bottom:0.75rem;"><i class="fa-solid fa-list" style="color:#06b6d4;margin-right:0.4rem;"></i> Micro Clips</h4>
          <div style="display:flex;flex-direction:column;gap:0.4rem;">
            ${allMeetings.length > 0 ? allMeetings.slice(0,5).map(m =>
              `<div style="background:rgba(6,182,212,0.08);border:1px solid rgba(6,182,212,0.12);border-radius:8px;padding:0.5rem 0.65rem;cursor:pointer;display:flex;align-items:center;gap:0.5rem;">
                <i class="fa-solid fa-scissors" style="color:#06b6d4;font-size:0.65rem;"></i>
                <span style="font-size:0.72rem;color:#c8d0dc;flex:1;">${m.title || "Meeting " + (i+1)}</span>
                <i class="fa-solid fa-download nf-clip-download" style="color:#8899b0;font-size:0.6rem;cursor:pointer;"></i>
              </div>`
            ).join("") : ["Budget Approved (09:28)","Deployment Discussion (09:40)","Final Decision (10:30)","Customer Feedback (09:15)","Risk Discussion (09:55)"].map(c =>
              `<div style="background:rgba(6,182,212,0.08);border:1px solid rgba(6,182,212,0.12);border-radius:8px;padding:0.5rem 0.65rem;cursor:pointer;display:flex;align-items:center;gap:0.5rem;">
                <i class="fa-solid fa-scissors" style="color:#06b6d4;font-size:0.65rem;"></i>
                <span style="font-size:0.72rem;color:#c8d0dc;flex:1;">${c}</span>
                <i class="fa-solid fa-download nf-clip-download" style="color:#8899b0;font-size:0.6rem;cursor:pointer;"></i>
              </div>`
            ).join("")}
          </div>
        </div>
      </div>`;
    setTimeout(() => {
      document.querySelectorAll(".nf-replay-item").forEach(item => {
        item.onclick = function() {
          document.querySelectorAll(".nf-replay-item").forEach(x => x.style.background = "transparent");
          this.style.background = "rgba(99,102,241,0.08)";
        };
      });
      const playBtn = el("replay-play-btn");
      if (playBtn) {
        let playing = false;
        let replayAudio = null;
        playBtn.onclick = function() {
          if (!playing) {
            if (allMeetings.length > 0) {
              const sel = document.getElementById("replay-meeting-select");
              const idx = parseInt(sel ? sel.value : 0);
              const meeting = allMeetings[idx] || allMeetings[0];
              if (meeting.audioUrl && meeting.audioUrl !== "#") {
                replayAudio = new Audio(meeting.audioUrl);
                replayAudio.play().then(() => {
                  playing = true;
                  playBtn.innerHTML = '<i class="fa-solid fa-pause"></i> Pause';
                  replayAudio.onended = function() {
                    playing = false;
                    playBtn.innerHTML = '<i class="fa-solid fa-play"></i> Play';
                    replayAudio = null;
                  };
                }).catch(function() {
                  showToast("Unable to play audio for this meeting", "error");
                  playBtn.innerHTML = '<i class="fa-solid fa-play"></i> Play';
                });
                return;
              }
            }
            playing = true;
            playBtn.innerHTML = '<i class="fa-solid fa-pause"></i> Pause';
            setTimeout(() => {
              playing = false;
              playBtn.innerHTML = '<i class="fa-solid fa-play"></i> Play';
            }, 3000);
          } else {
            playing = false;
            playBtn.innerHTML = '<i class="fa-solid fa-play"></i> Play';
            if (replayAudio) { replayAudio.pause(); replayAudio = null; }
          }
        };
      }
      document.querySelectorAll(".nf-clip-download").forEach(icon => {
        icon.onclick = function(e) {
          e.stopPropagation();
          const clipName = this.closest("div").querySelector("span").textContent;
          const content = `EchoAction AI - Micro Clip: ${clipName}\nGenerated: ${new Date().toLocaleString()}`;
          const blob = new Blob([content], { type: "text/plain" });
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = clipName.replace(/[^a-zA-Z0-9]/g, "_") + ".txt";
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
          showToast("Downloaded: " + clipName, "success");
        };
      });
    }, 50);
  };

  // ============ 10. WORKFLOW AUTOMATION (Simplified - Employee View & Trigger Only) ============
  window.__nf["screen-workflow-automation"] = function() {
    const c = el("screen-workflow-automation");
    if (!c) return;
    const workflows = [
      {name:"Generate Meeting Summary", desc:"Auto-generate summary after each meeting", status:"Active", createdBy:"System", lastExec:"Today, 9:15 AM", progress:85},
      {name:"Create Action Items", desc:"Extract action items from meetings and create tasks", status:"Active", createdBy:"Admin", lastExec:"Yesterday", progress:72},
      {name:"Send Follow-up Email", desc:"Send follow-up emails after meeting completion", status:"Active", createdBy:"Admin", lastExec:"Oct 28", progress:60},
      {name:"Notify Team Members", desc:"Send notifications to team about updates", status:"Inactive", createdBy:"Admin", lastExec:"Oct 20", progress:0},
      {name:"Create Project Task", desc:"Auto-create project tasks from meeting decisions", status:"Active", createdBy:"System", lastExec:"Today, 8:30 AM", progress:45},
      {name:"Update Calendar", desc:"Sync meeting schedules to calendar", status:"Active", createdBy:"Admin", lastExec:"Today, 9:00 AM", progress:90},
      {name:"Export Meeting Report", desc:"Generate and export meeting reports", status:"Active", createdBy:"Admin", lastExec:"Yesterday", progress:78}
    ];
    c.innerHTML = `
      <div class="nf-screen-header">
        <h2 style="font-family:var(--font-display);font-size:1.3rem;color:#f3f4f6;display:flex;align-items:center;gap:0.6rem;"><i class="fa-solid fa-gears" style="color:#f59e0b;"></i> Workflow Automation <span style="font-size:0.7rem;background:rgba(245,158,11,0.15);color:#f59e0b;padding:0.15rem 0.5rem;border-radius:20px;">Employee View</span></h2>
        <p style="font-size:0.8rem;color:#8899b0;margin:0.3rem 0 0 2.1rem;">View available workflows and manually trigger them. Only admins can create, edit, or delete workflows.</p>
      </div>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:0.75rem;margin-top:1rem;">
        ${workflows.map(w => `
          <div style="background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.25rem;">
            <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:0.5rem;">
              <h4 style="color:#f3f4f6;font-size:0.85rem;margin:0;">${esc(w.name)}</h4>
              <span style="font-size:0.65rem;padding:0.15rem 0.5rem;border-radius:10px;background:${w.status==="Active"?"rgba(16,185,129,0.15)":"rgba(244,63,94,0.15)"};color:${w.status==="Active"?"#6ee7b7":"#fca5a5"};">${w.status}</span>
            </div>
            <p style="font-size:0.72rem;color:var(--text-muted);margin-bottom:0.75rem;">${esc(w.desc)}</p>
            <div style="font-size:0.68rem;color:#8899b0;margin-bottom:0.5rem;"><span>Created by: ${esc(w.createdBy)}</span> · <span>Last: ${w.lastExec}</span></div>
            <div style="margin-bottom:0.5rem;"><div style="display:flex;justify-content:space-between;font-size:0.65rem;color:var(--text-muted);margin-bottom:0.15rem;"><span>Progress</span><span>${w.progress}%</span></div><div style="height:4px;background:rgba(255,255,255,0.06);border-radius:2px;"><div style="height:100%;width:${w.progress}%;background:${w.progress>70?"#34d399":w.progress>40?"#fbbf24":"#f43f5e"};border-radius:2px;"></div></div></div>
            <button class="btn btn-primary wf-trigger-btn" data-wf="${esc(w.name)}" style="padding:0.35rem 0.75rem;font-size:0.72rem;width:100%;justify-content:center;"><i class="fa-solid fa-play"></i> Trigger Workflow</button>
            <div class="wf-trigger-status" style="display:none;font-size:0.7rem;color:#6ee7b7;margin-top:0.4rem;text-align:center;"><i class="fa-solid fa-check-circle"></i> Triggered! Running...</div>
          </div>`).join("")}
      </div>`;
    setTimeout(() => {
      document.querySelectorAll(".wf-trigger-btn").forEach(btn => {
        btn.onclick = function() {
          const card = this.closest("div");
          const status = card.querySelector(".wf-trigger-status");
          this.style.display = "none";
          status.style.display = "block";
          showToast("Workflow '" + esc(this.dataset.wf) + "' triggered successfully", "success");
          setTimeout(() => { status.style.display = "none"; this.style.display = ""; }, 2000);
        };
      });
    }, 50);
  };

  // ============ 11. PREDICTIVE ANALYTICS ============
  window.__nf["screen-predictive-analytics"] = function() {
    const c = el("screen-predictive-analytics");
    if (!c) return;
    const LD = _getLD();
    c.innerHTML = `
      <div class="nf-screen-header">
        <h2 style="font-family:var(--font-display);font-size:1.3rem;color:#f3f4f6;display:flex;align-items:center;gap:0.6rem;"><i class="fa-solid fa-chart-bar" style="color:#a78bfa;"></i> Predictive Analytics <span style="font-size:0.7rem;background:rgba(167,139,250,0.15);color:#a78bfa;padding:0.15rem 0.5rem;border-radius:20px;">AI Predictions</span></h2>
        <p style="font-size:0.8rem;color:#8899b0;margin:0.3rem 0 0 2.1rem;">Data-driven predictions and risk forecasts</p>
      </div>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:0.75rem;margin-top:1rem;">
        ${LD.predictions.map(p => `
          <div style="background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.25rem;">
            <p style="font-size:0.75rem;color:#8899b0;margin-bottom:0.5rem;">${p.label}</p>
            <div style="display:flex;align-items:baseline;gap:0.3rem;margin-bottom:0.5rem;">
              <span style="font-size:1.8rem;font-weight:700;color:${p.status==="good"?"#6ee7b7":p.status==="warning"?"#fbbf24":"#818cf8"};">${p.value}${typeof p.value==="number"?"%":""}</span>
            </div>
            <div style="width:100%;height:4px;background:rgba(255,255,255,0.06);border-radius:2px;margin-bottom:0.5rem;">
              <div style="height:100%;width:${typeof p.value==="number"?Math.min(p.value,100):50}%;background:${p.status==="good"?"#10b981":p.status==="warning"?"#f59e0b":"#818cf8"};border-radius:2px;"></div>
            </div>
            <p style="font-size:0.7rem;color:#8899b0;">${p.desc}</p>
          </div>`).join("")}
      </div>
      <div style="margin-top:1rem;background:rgba(15,22,42,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.25rem;">
        <h4 style="color:#f3f4f6;font-size:0.9rem;margin-bottom:0.75rem;"><i class="fa-solid fa-robot" style="color:#10b981;margin-right:0.4rem;"></i> AI Personas</h4>
        <p style="font-size:0.78rem;color:#8899b0;margin-bottom:0.75rem;">Generate summaries tailored to your role</p>
        <div style="display:flex;flex-wrap:wrap;gap:0.4rem;margin-bottom:1rem;">
          ${["General","Project Manager","Developer","CEO","HR","Sales","Marketing","QA","Product Owner"].map(r =>
            `<button class="nf-persona-btn" data-persona="${esc(r)}" style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:20px;padding:0.35rem 0.85rem;font-size:0.75rem;color:#c8d0dc;cursor:pointer;transition:var(--transition-fast);">${r}</button>`
          ).join("")}
        </div>
        <div id="persona-summary" style="background:rgba(0,0,0,0.2);border-radius:10px;padding:1rem;min-height:80px;">
          <p style="color:#8899b0;font-size:0.82rem;line-height:1.6;">Select a persona to generate a tailored summary of recent meetings and decisions.</p>
        </div>
      </div>`;
    setTimeout(() => {
      document.querySelectorAll("[data-persona]").forEach(btn => {
        btn.onclick = function() {
          document.querySelectorAll("[data-persona]").forEach(b => { b.style.background = "rgba(255,255,255,0.04)"; b.style.color = "#c8d0dc"; b.style.borderColor = "rgba(255,255,255,0.08)"; });
          this.style.background = "rgba(99,102,241,0.2)"; this.style.color = "#a5b4fc"; this.style.borderColor = "rgba(99,102,241,0.3)";
          const role = this.textContent;
          const totalM = ms.length;
          const totalDec = LD.decisions.length;
          const topCatsStr = LD.topics.slice(0,3).join(", ");
          const summaries = {
            "General":"Recent meetings indicate strong progress with "+totalDec+" decisions and "+LD.projectHealth.completed+" tasks completed. Key topics: "+topCatsStr+".",
            "Project Manager":totalM+" meetings tracked. "+allTasks.length+" tasks, "+compTasks+" completed. Completion rate: "+taskCompletionRate+"%. "+topCats.length+" active project categories.",
            "Developer":allTasks.length+" total tasks. "+compTasks+" completed, "+(allTasks.length-compTasks)+" pending. Topics: "+topCatsStr+".",
            "CEO":"Business Impact: "+totalM+" meetings analyzed. "+totalDec+" decisions made. "+taskCompletionRate+"% task completion rate across "+LD.people.length+" team members.",
            "HR":LD.people.length+" team members across meetings. Attendees: "+[...new Set(ms.flatMap(m=>m.attendees||[]))].join(", ").substring(0,60)+".",
            "Sales":topCats.length+" project categories. "+totalM+" meetings logged. "+totalDec+" key decisions documented for reference.",
            "Marketing":"Campaign insights from "+totalM+" meetings. "+LD.topics.length+" topics identified. "+allTasks.length+" action items extracted from discussions.",
            "QA":compTasks+" completed tasks out of "+allTasks.length+". Task completion rate: "+taskCompletionRate+"%. "+LD.projectHealth.riskScore+"/100 risk score.",
            "Product Owner":"Backlog summary: "+allTasks.length+" items across "+LD.topics.length+" topics. "+compTasks+" completed, "+(allTasks.length-compTasks)+" pending. "+LD.projectHealth.sprintProgress+"% sprint progress."
          };
          el("persona-summary").innerHTML = `<p style="color:#e8edf5;font-size:0.82rem;line-height:1.6;"><i class="fa-solid fa-user-tie" style="color:#818cf8;margin-right:0.4rem;"></i> <strong style="color:#f3f4f6;">${role}</strong> Summary</p>
            <p style="color:#c8d0dc;font-size:0.82rem;line-height:1.6;margin-top:0.5rem;">${summaries[role]||summaries["General"]}</p>`;
        };
      });
    }, 50);
  };


})();