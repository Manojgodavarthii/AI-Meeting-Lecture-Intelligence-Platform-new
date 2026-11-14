// EchoAction AI - Features Expansion (v2)
(function() {
  'use strict';
  window.__nf = window.__nf || {};

  const el = id => document.getElementById(id);
  const esc = s => String(s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  const _getLD = () => (window.meetings && window.meetings.length) ? (window.LD || window.__LD || {topics:[],people:[],decisions:[],timeline:[],similarMeetings:[],aiInsights:[],aiSuggestions:[],predictions:[],projectHealth:{}}) : {topics:DATA.topics||[],people:DATA.employees||[],decisions:DATA.decisions||[],timeline:[],similarMeetings:[],aiInsights:[],aiSuggestions:[],predictions:[],projectHealth:{}};

  // Shared mock data
  const DATA = {
    departments: [
      {name:"Engineering", head:"Sarah Jenkins", color:"#818cf8", employees:12, projects:5, health:88, meetings:45},
      {name:"Design", head:"Elena Rodriguez", color:"#f472b6", employees:8, projects:3, health:92, meetings:30},
      {name:"Product", head:"Chloe Kim", color:"#fbbf24", employees:6, projects:4, health:80, meetings:55},
      {name:"DevOps", head:"Alex Thompson", color:"#34d399", employees:5, projects:2, health:78, meetings:22},
      {name:"Marketing", head:"Marcus Chen", color:"#a78bfa", employees:7, projects:3, health:85, meetings:35}
    ],
    projects: [
      {id:"p1", name:"Platform Migration", lead:"Sarah", status:"In Progress", progress:72, risk:"Medium", deadline:"2026-08-15", budget:450000, spent:320000},
      {id:"p2", name:"Mobile App v2", lead:"Marcus", status:"In Progress", progress:45, risk:"High", deadline:"2026-09-01", budget:300000, spent:180000},
      {id:"p3", name:"AI Features", lead:"Chloe", status:"Planning", progress:20, risk:"Low", deadline:"2026-10-01", budget:500000, spent:120000},
      {id:"p4", name:"Security Audit", lead:"Alex", status:"Completed", progress:100, risk:"Low", deadline:"2026-06-30", budget:150000, spent:145000}
    ],
    employees: [
      {name:"Sarah Jenkins", role:"Lead Backend", dept:"Engineering", email:"sarah@echoaction.ai", workload:85, skills:["Python","Node","Database","AWS"], meetings:12, tasksComp:11, tasksTotal:15, performance:92},
      {name:"Marcus Chen", role:"Frontend Developer", dept:"Engineering", email:"marcus@echoaction.ai", workload:70, skills:["React","TypeScript","CSS"], meetings:9, tasksComp:9, tasksTotal:10, performance:88},
      {name:"Elena Rodriguez", role:"Lead Designer", dept:"Design", email:"elena@echoaction.ai", workload:65, skills:["Figma","UI/UX","Prototyping"], meetings:14, tasksComp:10, tasksTotal:12, performance:90},
      {name:"Alex Thompson", role:"DevOps", dept:"DevOps", email:"alex@echoaction.ai", workload:55, skills:["Docker","K8s","AWS","CI/CD"], meetings:7, tasksComp:7, tasksTotal:8, performance:80},
      {name:"Chloe Kim", role:"Product Manager", dept:"Product", email:"chloe@echoaction.ai", workload:90, skills:["Strategy","Analytics","Roadmap"], meetings:20, tasksComp:15, tasksTotal:18, performance:85}
    ],
    ideas: [
      {title:"AI-powered code review", author:"Sarah", votes:15, status:"In Review", impact:"High", effort:"Medium"},
      {title:"Dark mode for dashboard", author:"Marcus", votes:22, status:"Approved", impact:"Medium", effort:"Low"},
      {title:"Automated meeting summaries", author:"Chloe", votes:18, status:"Implemented", impact:"High", effort:"Medium"},
      {title:"Mobile notifications", author:"Elena", votes:12, status:"Planning", impact:"Medium", effort:"Low"},
      {title:"Customer sentiment analysis", author:"Alex", votes:8, status:"Proposed", impact:"High", effort:"High"}
    ],
    reports: [
      {name:"Weekly Summary", desc:"Overview of all activities", formats:["PDF","Word","Excel"]},
      {name:"Monthly Performance", desc:"Team and individual metrics", formats:["PDF","Word","PowerPoint"]},
      {name:"Meeting Effectiveness", desc:"Meeting quality analysis", formats:["PDF","Excel"]},
      {name:"Project Status", desc:"Project health and milestones", formats:["PDF","Word","PowerPoint"]},
      {name:"Cost Analysis", desc:"Budget and resource utilization", formats:["PDF","Excel"]},
      {name:"Executive Summary", desc:"CEO-level organization overview", formats:["PDF","PowerPoint"]}
    ],
    knowledgeDocs: [
      {title:"Company Leave Policy", type:"HR Policy", updated:"2026-06-01", dept:"HR"},
      {title:"Security Best Practices", type:"SOP", updated:"2026-05-15", dept:"Engineering"},
      {title:"Employee Onboarding Guide", type:"Handbook", updated:"2026-04-20", dept:"HR"},
      {title:"API Documentation v3", type:"Technical", updated:"2026-06-10", dept:"Engineering"},
      {title:"Design System Guidelines", type:"Design", updated:"2026-05-01", dept:"Design"},
      {title:"Remote Work Policy", type:"HR Policy", updated:"2026-03-15", dept:"HR"},
      {title:"Data Privacy Policy", type:"Compliance", updated:"2026-06-05", dept:"Legal"},
      {title:"Incident Response Plan", type:"SOP", updated:"2026-04-10", dept:"DevOps"}
    ],
    workflows: [
      {name:"Meeting Follow-up", trigger:"Meeting Ends", actions:["Generate Summary","Create Tasks","Send Email","Notify Team"], active:true, runs:47},
      {name:"New Hire Onboarding", trigger:"User Created", actions:["Send Welcome Email","Create Slack Account","Assign Mentor","Schedule Training"], active:true, runs:23},
      {name:"Daily Standup Report", trigger:"Scheduled 9AM", actions:["Collect Updates","Generate Report","Post to Slack"], active:false, runs:156},
      {name:"Task Escalation", trigger:"Task Overdue 3d", actions:["Notify Manager","Increase Priority","Send Reminder"], active:true, runs:12}
    ],
    decisions: [
      {id:"d1", decision:"Migrate to PostgreSQL", impact:"Reduced latency by 40%", date:"2026-02-10", success:true, cost:50000, dept:"Engineering"},
      {id:"d2", decision:"Adopt React 18", impact:"30% faster rendering", date:"2026-02-05", success:true, cost:20000, dept:"Engineering"},
      {id:"d3", decision:"AWS Reserved Instances", impact:"35% cost reduction", date:"2026-01-28", success:true, cost:120000, dept:"DevOps"},
      {id:"d4", decision:"Dark Mode Support", impact:"User satisfaction +15%", date:"2026-01-20", success:true, cost:15000, dept:"Design"},
      {id:"d5", decision:"Automated Testing Pipeline", impact:"Bug detection +60%", date:"2026-01-15", success:false, cost:40000, dept:"Engineering"}
    ]
  };

  // ============================
  // 1. AI Organization Brain
  // ============================
  window.__nf["screen-org-brain"] = function() {
    const c = el("screen-org-brain"); if (!c) return;
    const content = c.querySelector(".nf-screen-content") || c;
    const LD = _getLD();
    const ms = window.meetings || [];
    content.innerHTML = `
      <div style="padding:1rem 1.5rem;">
        <h2 style="font-family:var(--font-display);font-size:1.1rem;color:#f3f4f6;margin-bottom:0.25rem;"><i class="fa-solid fa-brain" style="color:#818cf8;margin-right:0.5rem;"></i>AI Organization Brain</h2>
        <p style="font-size:0.8rem;color:var(--text-muted);margin-bottom:1.25rem;">Company memory connecting meetings, projects, documents, tasks, and decisions.</p>
        <div style="display:flex;gap:0.75rem;margin-bottom:1.25rem;flex-wrap:wrap;">
          <button class="nf-brain-tab active" data-section="overview" style="padding:0.4rem 1rem;border-radius:8px;border:1px solid rgba(99,102,241,0.3);background:rgba(99,102,241,0.15);color:#a5b4fc;font-size:0.78rem;cursor:pointer;font-weight:600;">Overview</button>
          <button class="nf-brain-tab" data-section="timeline" style="padding:0.4rem 1rem;border-radius:8px;border:1px solid var(--card-border);background:transparent;color:var(--text-secondary);font-size:0.78rem;cursor:pointer;">Timeline</button>
          <button class="nf-brain-tab" data-section="knowledge" style="padding:0.4rem 1rem;border-radius:8px;border:1px solid var(--card-border);background:transparent;color:var(--text-secondary);font-size:0.78rem;cursor:pointer;">Knowledge Base</button>
          <button class="nf-brain-tab" data-section="graph" style="padding:0.4rem 1rem;border-radius:8px;border:1px solid var(--card-border);background:transparent;color:var(--text-secondary);font-size:0.78rem;cursor:pointer;">Connections</button>
          <button class="nf-brain-tab" data-section="knowledge-graph" style="padding:0.4rem 1rem;border-radius:8px;border:1px solid var(--card-border);background:transparent;color:var(--text-secondary);font-size:0.78rem;cursor:pointer;"><i class="fa-solid fa-diagram-project"></i> Knowledge Graph</button>
          <button class="nf-brain-tab" data-section="search" style="padding:0.4rem 1rem;border-radius:8px;border:1px solid var(--card-border);background:transparent;color:var(--text-secondary);font-size:0.78rem;cursor:pointer;"><i class="fa-solid fa-search"></i> Cross-Meeting Search</button>
        </div>
        <div id="nf-brain-content"></div>
      </div>`;
    const tabs = content.querySelectorAll(".nf-brain-tab");
    const brainContent = content.querySelector("#nf-brain-content");
    const showSection = (sec) => {
      tabs.forEach(t => { t.style.background = "transparent"; t.style.color = "var(--text-secondary)"; t.style.borderColor = "var(--card-border)"; t.classList.remove("active"); });
      tabs.forEach(t => { if (t.dataset.section === sec) { t.style.background = "rgba(99,102,241,0.15)"; t.style.color = "#a5b4fc"; t.style.borderColor = "rgba(99,102,241,0.3)"; t.classList.add("active"); }});
      if (sec === "overview") {
        const dc = DATA.decisions || [];
        const ideas = DATA.ideas || [];
        brainContent.innerHTML = `
          <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:0.75rem;margin-bottom:1rem;">
            <div class="glass-card" style="padding:1rem;text-align:center;"><div style="font-size:1.5rem;font-weight:700;color:#818cf8;">${ms.length}</div><div style="font-size:0.72rem;color:var(--text-muted);">Meetings</div></div>
            <div class="glass-card" style="padding:1rem;text-align:center;"><div style="font-size:1.5rem;font-weight:700;color:#34d399;">${dc.length}</div><div style="font-size:0.72rem;color:var(--text-muted);">Decisions</div></div>
            <div class="glass-card" style="padding:1rem;text-align:center;"><div style="font-size:1.5rem;font-weight:700;color:#fbbf24;">${ideas.length}</div><div style="font-size:0.72rem;color:var(--text-muted);">Ideas</div></div>
            <div class="glass-card" style="padding:1rem;text-align:center;"><div style="font-size:1.5rem;font-weight:700;color:#f472b6;">${DATA.employees.length}</div><div style="font-size:0.72rem;color:var(--text-muted);">People</div></div>
          </div>
          <div class="glass-card" style="padding:1rem;">
            <h4 style="font-size:0.85rem;color:#e8edf5;margin-bottom:0.75rem;"><i class="fa-solid fa-diagram-project" style="color:#818cf8;margin-right:0.4rem;"></i> Connected Knowledge Graph</h4>
            <div style="display:flex;flex-wrap:wrap;gap:0.5rem;justify-content:center;padding:1rem;">
              ${["Meetings","Projects","Tasks","Decisions","People","Documents"].map((n,i) => `<div style="background:rgba(99,102,241,${0.05+i*0.03});border:1px solid rgba(99,102,241,0.15);border-radius:50%;width:90px;height:90px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:0.72rem;color:#a5b4fc;"><i class="fa-solid ${["fa-folder-open","fa-diagram-project","fa-list-check","fa-scale-balanced","fa-users","fa-file-lines"][i]}" style="font-size:1.1rem;margin-bottom:0.3rem;color:#818cf8;"></i>${n}</div>`).join("")}
            </div>
            <p style="text-align:center;font-size:0.72rem;color:var(--text-muted);">Everything is connected — click any node to explore relationships</p>
          </div>`;
      } else if (sec === "timeline") {
        const tl = LD.timeline || [{time:"09:00",label:"Meeting Started",desc:"Daily standup begins"},{time:"09:15",label:"Sprint Review",desc:"Completed tasks reviewed"},{time:"09:30",label:"Q&A",desc:"Team questions answered"}];
        brainContent.innerHTML = `
          <div class="glass-card" style="padding:1rem;">
            <h4 style="font-size:0.85rem;color:#e8edf5;margin-bottom:0.75rem;"><i class="fa-solid fa-clock-rotate-left" style="color:#818cf8;margin-right:0.4rem;"></i> Organization Timeline</h4>
            <div style="position:relative;padding-left:1.5rem;">
              <div style="position:absolute;left:0.5rem;top:0;bottom:0;width:2px;background:rgba(99,102,241,0.2);"></div>
              ${tl.map((t,i) => `<div style="position:relative;padding:0.5rem 0 0.5rem 1rem;border-left:2px solid rgba(99,102,241,${0.2+i*0.15});margin-left:-0.5rem;">
                <div style="position:absolute;left:-7px;top:0.7rem;width:12px;height:12px;border-radius:50%;background:rgba(99,102,241,${0.3+i*0.15});border:2px solid #818cf8;"></div>
                <div style="font-size:0.68rem;color:#818cf8;font-weight:600;">${t.time||""}</div>
                <div style="font-size:0.8rem;color:#e8edf5;font-weight:600;">${esc(t.label)}</div>
                <div style="font-size:0.72rem;color:var(--text-muted);">${esc(t.desc||"")}</div>
              </div>`).join("")}
            </div>
          </div>`;
      } else if (sec === "knowledge") {
        const docs = DATA.knowledgeDocs || [];
        brainContent.innerHTML = `
          <div class="glass-card" style="padding:1rem;">
            <h4 style="font-size:0.85rem;color:#e8edf5;margin-bottom:0.75rem;"><i class="fa-solid fa-file-lines" style="color:#818cf8;margin-right:0.4rem;"></i> Knowledge Base (${docs.length} documents)</h4>
            <div style="display:grid;gap:0.5rem;">${docs.map(d => `<div style="display:flex;align-items:center;justify-content:space-between;padding:0.5rem 0.75rem;background:rgba(99,102,241,0.04);border:1px solid var(--card-border);border-radius:6px;">
              <div><div style="font-size:0.8rem;color:#e8edf5;">${esc(d.title)}</div><div style="font-size:0.68rem;color:var(--text-muted);">${esc(d.type)} · ${esc(d.dept)} · Updated ${d.updated}</div></div>
              <i class="fa-solid fa-arrow-up-right-from-square" style="color:#818cf8;font-size:0.75rem;cursor:pointer;"></i>
            </div>`).join("")}</div>
          </div>`;
      } else if (sec === "graph") {
        brainContent.innerHTML = `
          <div class="glass-card" style="padding:1.5rem;text-align:center;">
            <div style="position:relative;width:100%;height:300px;background:rgba(99,102,241,0.03);border-radius:12px;border:1px solid rgba(99,102,241,0.08);display:flex;align-items:center;justify-content:center;">
              <canvas id="nf-org-graph" style="width:100%;height:100%;"></canvas>
              <div style="position:absolute;font-size:0.8rem;color:var(--text-muted);">Organization Connection Map</div>
            </div>
            <p style="font-size:0.72rem;color:var(--text-muted);margin-top:0.5rem;">Visual graph showing connections between employees, projects, meetings, and decisions</p>
          </div>`;
      } else if (sec === "knowledge-graph") {
        const ms = window.meetings || [];
        const allTasks = ms.flatMap(m=>m.actionItems||[]);
        const allAttendees = [...new Set(ms.flatMap(m=>m.attendees||[]))];
        const nodes = ["Meetings","Projects","People","Tasks","Topics","Documents","Decisions","Departments","Clients"];
        brainContent.innerHTML = `
          <div class="glass-card" style="padding:1.25rem;">
            <h4 style="font-size:0.85rem;color:#e8edf5;margin-bottom:0.75rem;"><i class="fa-solid fa-diagram-project" style="color:#a78bfa;margin-right:0.4rem;"></i> Knowledge Graph</h4>
            <p style="font-size:0.72rem;color:var(--text-muted);margin-bottom:1rem;">Visual relationship between everything in your organization</p>
            <div style="display:flex;gap:1rem;">
              <div style="flex:1;min-height:350px;background:rgba(15,22,42,0.4);border:1px solid rgba(255,255,255,0.05);border-radius:12px;padding:1rem;position:relative;overflow:hidden;">
                <div style="position:relative;width:100%;height:350px;display:flex;align-items:center;justify-content:center;">
                  <div style="position:relative;width:320px;height:320px;">
                    ${nodes.map((n,i) => {
                      const angle = (i / nodes.length) * 2 * Math.PI - Math.PI/2;
                      const r = 130;
                      const x = 160 + r * Math.cos(angle);
                      const y = 160 + r * Math.sin(angle);
                      const colors = ["#818cf8","#10b981","#f59e0b","#06b6d4","#a78bfa","#f472b6","#fb7185","#34d399","#fbbf24"];
                      return `<div class="nf-graph-node" data-kgnode="${n}" style="position:absolute;left:${x-30}px;top:${y-30}px;width:60px;height:60px;border-radius:50%;background:rgba(15,22,42,0.9);border:2px solid ${colors[i]};display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all 0.3s;z-index:2;box-shadow:0 0 10px ${colors[i]}40;font-size:0.55rem;color:#c8d0dc;text-align:center;line-height:1.2;font-weight:600;">${n}</div>`;
                    }).join("")}
                  </div>
                </div>
              </div>
              <div id="kg-detail" style="width:240px;flex-shrink:0;background:rgba(15,22,42,0.4);border:1px solid rgba(255,255,255,0.05);border-radius:12px;padding:1rem;">
                <p style="color:var(--text-muted);font-size:0.78rem;text-align:center;padding:2rem 0;">Click a node to see<br>connected items</p>
              </div>
            </div>
          </div>`;
        setTimeout(() => {
          document.querySelectorAll("[data-kgnode]").forEach(n => {
            n.onclick = function() {
              const label = this.textContent.trim();
              const totalMeetings = ms.length;
              const completedTasks = allTasks.filter(t=>t.status==='Completed').length;
              const totalDecisions = (DATA.decisions||[]).length;
              const totalTopics = [...new Set(ms.map(m=>m.category||'General'))].length;
              const details = {
                "Meetings":totalMeetings+" connected meetings<br>"+totalTopics+" related topics<br>"+allAttendees.length+" participants",
                "Projects":totalTopics+" active projects<br>"+allTasks.length+" associated tasks",
                "People":allAttendees.length+" team members<br>"+totalMeetings+" total meetings attended",
                "Tasks":allTasks.length+" total tasks<br>"+completedTasks+" completed<br>"+(allTasks.length-completedTasks)+" pending",
                "Topics":totalTopics+" tracked topics<br>Most discussed: "+ms.map(m=>m.category||'General').filter((v,i,a)=>a.indexOf(v)===i).slice(0,3).join(", "),
                "Documents":(totalMeetings*2)+" total documents",
                "Decisions":totalDecisions+" decisions made",
                "Departments":[...new Set(ms.flatMap(m=>(m.attendees||[]).map(a=>a.split(/\s*\(|\s+-\s+/).pop()||'General')))].join(", ")||"Engineering, Product, Design",
                "Clients":Math.max(1,Math.floor(totalMeetings/3))+" active clients"
              };
              const d = el("kg-detail");
              if (d) d.innerHTML = '<h4 style="color:#e8edf5;font-size:0.85rem;margin-bottom:0.75rem;"><i class="fa-solid fa-circle-nodes" style="color:#a78bfa;margin-right:0.3rem;"></i> '+label+'</h4><div style="font-size:0.75rem;color:#c8d0dc;line-height:1.8;">'+(details[label]||"No details available")+'</div>';
            };
          });
        }, 100);
      } else if (sec === "search") {
        brainContent.innerHTML = `
          <div class="glass-card" style="padding:1rem;">
            <h4 style="font-size:0.85rem;color:#e8edf5;margin-bottom:0.75rem;"><i class="fa-solid fa-search" style="color:#818cf8;margin-right:0.4rem;"></i> Cross-Meeting Semantic Search</h4>
            <div style="display:flex;gap:0.5rem;margin-bottom:0.75rem;">
              <input type="text" id="nf-brain-search-input" placeholder="Search meetings, decisions, documents..." class="form-input" style="flex:1;padding:0.5rem 0.75rem;font-size:0.8rem;">
              <button id="nf-brain-search-btn" class="btn btn-primary" style="padding:0.5rem 1rem;font-size:0.78rem;"><i class="fa-solid fa-search"></i> Search</button>
            </div>
            <div id="nf-brain-search-results" style="font-size:0.78rem;color:var(--text-muted);">Ask anything about your organization data.</div>
          </div>`;
        setTimeout(() => {
          const inp = el("nf-brain-search-input");
          const btn = el("nf-brain-search-btn");
          const res = el("nf-brain-search-results");
          if (!inp || !btn || !res) return;
          const doSearch = () => {
            const q = inp.value.trim().toLowerCase();
            if (!q) { res.innerHTML = "Enter a search query."; return; }
            const results = [];
            (ms||[]).forEach(m => { if ((m.title||"").toLowerCase().includes(q)||(m.agenda||"").toLowerCase().includes(q)) results.push({type:"Meeting", title:m.title, desc:m.agenda||m.title}); });
            DATA.employees.forEach(e => { if (e.name.toLowerCase().includes(q)||e.skills.some(s=>s.toLowerCase().includes(q))) results.push({type:"Employee", title:e.name, desc:e.role+" · "+e.dept}); });
            (DATA.decisions||[]).forEach(d => { if (d.decision.toLowerCase().includes(q)) results.push({type:"Decision", title:d.decision, desc:d.impact||""}); });
            (DATA.knowledgeDocs||[]).forEach(d => { if (d.title.toLowerCase().includes(q)) results.push({type:"Document", title:d.title, desc:d.type+" · "+d.dept}); });
            if (results.length === 0) { res.innerHTML = "<p style='color:var(--text-muted);'>No results found.</p>"; return; }
            res.innerHTML = results.slice(0,15).map(r => `<div style="display:flex;align-items:center;gap:0.5rem;padding:0.4rem 0;border-bottom:1px solid var(--card-border);">
              <span style="font-size:0.65rem;padding:0.1rem 0.4rem;border-radius:4px;background:rgba(99,102,241,0.1);color:#a5b4fc;">${r.type}</span>
              <span style="color:#e8edf5;">${esc(r.title)}</span>
              <span style="color:var(--text-muted);font-size:0.72rem;">${esc(r.desc)}</span>
            </div>`).join("");
          };
          btn.onclick = doSearch;
          inp.onkeydown = e => { if (e.key === "Enter") doSearch(); };
        }, 100);
      }
    };
    showSection("overview");
    tabs.forEach(t => t.addEventListener("click", () => showSection(t.dataset.section)));
  };

  // ============================
  // 2. AI Command Center
  // ============================
  window.__nf["screen-ai-command"] = function() {
    const c = el("screen-ai-command"); if (!c) return;
    const content = c.querySelector(".nf-screen-content") || c;
    const suggestions = ["Show today's meetings","Find delayed tasks","Open Project Alpha","Generate weekly report","Schedule a meeting with Sarah","Create new task","Analyze this month's productivity"];
    content.innerHTML = `
      <div style="padding:1rem 1.5rem;">
        <h2 style="font-family:var(--font-display);font-size:1.1rem;color:#f3f4f6;margin-bottom:0.25rem;"><i class="fa-solid fa-terminal" style="color:#818cf8;margin-right:0.5rem;"></i>AI Command Center</h2>
        <p style="font-size:0.8rem;color:var(--text-muted);margin-bottom:1rem;">One AI assistant to control the entire platform using natural language.</p>
        <div class="glass-card" style="padding:1.25rem;margin-bottom:1rem;background:linear-gradient(135deg,rgba(99,102,241,0.06),rgba(15,22,42,0.4));">
          <div style="display:flex;align-items:center;gap:0.75rem;background:rgba(12,16,28,0.6);border:1px solid rgba(99,102,241,0.2);border-radius:10px;padding:0.1rem 0.1rem 0.1rem 1rem;">
            <i class="fa-solid fa-robot" style="color:#818cf8;font-size:1rem;"></i>
            <input type="text" id="nf-command-input" placeholder="Ask AI to do anything..." class="form-input" style="flex:1;border:none;background:transparent;padding:0.75rem 0.5rem;font-size:0.85rem;color:#e8edf5;outline:none;">
            <button id="nf-command-submit" class="btn btn-primary" style="padding:0.6rem 1rem;border-radius:8px;font-size:0.78rem;"><i class="fa-solid fa-arrow-right"></i></button>
          </div>
        </div>
        <div id="nf-command-response" class="glass-card" style="padding:1rem;margin-bottom:1rem;display:none;"></div>
        <div style="margin-bottom:1rem;">
          <p style="font-size:0.75rem;color:var(--text-muted);margin-bottom:0.5rem;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Suggested Commands</p>
          <div style="display:flex;gap:0.5rem;flex-wrap:wrap;">${suggestions.map(s => `<button class="nf-command-suggestion" style="padding:0.35rem 0.75rem;border-radius:20px;border:1px solid var(--card-border);background:rgba(99,102,241,0.05);color:var(--text-secondary);font-size:0.75rem;cursor:pointer;">${s}</button>`).join("")}</div>
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:0.75rem;">
          <div class="glass-card" style="padding:0.75rem;text-align:center;cursor:pointer;" onclick="switchScreen('screen-dashboard')"><i class="fa-solid fa-chart-pie" style="color:#818cf8;font-size:1.2rem;display:block;margin-bottom:0.3rem;"></i><span style="font-size:0.72rem;color:var(--text-secondary);">Dashboard</span></div>
          <div class="glass-card" style="padding:0.75rem;text-align:center;cursor:pointer;" onclick="switchScreen('screen-meetings')"><i class="fa-solid fa-folder-open" style="color:#34d399;font-size:1.2rem;display:block;margin-bottom:0.3rem;"></i><span style="font-size:0.72rem;color:var(--text-secondary);">Meetings Hub</span></div>
          <div class="glass-card" style="padding:0.75rem;text-align:center;cursor:pointer;" onclick="switchScreen('screen-tasks')"><i class="fa-solid fa-list-check" style="color:#fbbf24;font-size:1.2rem;display:block;margin-bottom:0.3rem;"></i><span style="font-size:0.72rem;color:var(--text-secondary);">Task Tracker</span></div>
          <div class="glass-card" style="padding:0.75rem;text-align:center;cursor:pointer;" onclick="switchScreen('screen-ai-chat')"><i class="fa-solid fa-robot" style="color:#f472b6;font-size:1.2rem;display:block;margin-bottom:0.3rem;"></i><span style="font-size:0.72rem;color:var(--text-secondary);">AI Chat</span></div>
          <div class="glass-card" style="padding:0.75rem;text-align:center;cursor:pointer;" onclick="switchScreen('screen-calendar')"><i class="fa-solid fa-calendar-days" style="color:#a78bfa;font-size:1.2rem;display:block;margin-bottom:0.3rem;"></i><span style="font-size:0.72rem;color:var(--text-secondary);">Calendar</span></div>
          <div class="glass-card" style="padding:0.75rem;text-align:center;cursor:pointer;" onclick="switchScreen('screen-mbrain')"><i class="fa-solid fa-brain" style="color:#f59e0b;font-size:1.2rem;display:block;margin-bottom:0.3rem;"></i><span style="font-size:0.72rem;color:var(--text-secondary);">Meeting Brain</span></div>
        </div>
      </div>`;
    setTimeout(() => {
      const inp = el("nf-command-input");
      const btn = el("nf-command-submit");
      const resp = el("nf-command-response");
      if (!inp || !btn || !resp) return;
      const doCommand = () => {
        const q = inp.value.trim();
        if (!q) return;
        resp.style.display = "block";
        const todayMs = (window.meetings||[]).filter(m => m.date === new Date().toISOString().slice(0,10));
        const allTasks = []; (window.meetings||[]).forEach(m => allTasks.push(...(m.actionItems||[])));
        let answer = "";
        const ql = q.toLowerCase();
        if (ql.includes("today") || ql.includes("meeting")) answer = "Found <strong>"+todayMs.length+"</strong> meetings today. "+(todayMs.length?todayMs.map(m=>m.title).join(", "):"No meetings scheduled.");
        else if (ql.includes("task") || ql.includes("delayed") || ql.includes("pending")) {
          const pending = allTasks.filter(t => t.status !== "Completed");
          answer = "You have <strong>"+pending.length+"</strong> pending tasks. "+(pending.length>0?"Top: "+pending.slice(0,3).map(t=>t.title).join(", "):"");
        } else if (ql.includes("report") || ql.includes("weekly")) answer = "Generating weekly report...<br>✅ Meetings attended: "+window.meetings.length+"<br>✅ Tasks completed: "+allTasks.filter(t=>t.status==="Completed").length+"<br>✅ Overall productivity: "+Math.floor(Math.random()*30+70)+"%";
        else answer = "I've processed your request: <strong>"+esc(q)+"</strong><br>✅ Action completed. Check the relevant section for details.";
        resp.innerHTML = '<div style="display:flex;gap:0.75rem;"><div style="width:32px;height:32px;border-radius:8px;background:rgba(99,102,241,0.15);display:flex;align-items:center;justify-content:center;flex-shrink:0;"><i class="fa-solid fa-robot" style="color:#818cf8;font-size:0.8rem;"></i></div><div style="font-size:0.82rem;color:#c8d0dc;line-height:1.6;">'+answer+'</div></div>';
      };
      btn.onclick = doCommand;
      inp.onkeydown = e => { if (e.key === "Enter") doCommand(); };
      document.querySelectorAll(".nf-command-suggestion").forEach(b => b.onclick = () => { inp.value = b.textContent; doCommand(); });
    }, 100);
  };

  // ============================
  // 3. AI Automation Studio
  // ============================
  window.__nf["screen-auto-studio"] = function() {
    const c = el("screen-auto-studio"); if (!c) return;
    const content = c.querySelector(".nf-screen-content") || c;
    content.innerHTML = `
      <div style="padding:1rem 1.5rem;">
        <h2 style="font-family:var(--font-display);font-size:1.1rem;color:#f3f4f6;margin-bottom:0.25rem;"><i class="fa-solid fa-gears" style="color:#818cf8;margin-right:0.5rem;"></i>AI Automation Studio</h2>
        <p style="font-size:0.8rem;color:var(--text-muted);margin-bottom:1.25rem;">Create automation workflows without coding. Drag, drop, and connect.</p>
        <div class="glass-card" style="padding:1rem;margin-bottom:1rem;">
          <div style="display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:0.75rem;">
            <div style="flex:1;min-width:200px;">
              <label style="font-size:0.72rem;color:var(--text-muted);display:block;margin-bottom:0.3rem;">Trigger</label>
              <select id="nf-auto-trigger" class="form-input" style="width:100%;padding:0.45rem 0.6rem;font-size:0.78rem;">
                <option>Meeting Ends</option>
                <option>Task Completed</option>
                <option>New User Created</option>
                <option>Schedule (Cron)</option>
                <option>Email Received</option>
                <option>File Uploaded</option>
              </select>
            </div>
            <div style="flex:2;min-width:300px;">
              <label style="font-size:0.72rem;color:var(--text-muted);display:block;margin-bottom:0.3rem;">Actions (select all that apply)</label>
              <div style="display:flex;gap:0.35rem;flex-wrap:wrap;">
                ${["Generate Summary","Create Tasks","Send Email","Notify Team","Create Calendar Event","Slack Message","Update Project","Generate Report"].map(a => `<label style="display:flex;align-items:center;gap:0.3rem;padding:0.3rem 0.5rem;background:rgba(99,102,241,0.05);border:1px solid var(--card-border);border-radius:6px;font-size:0.72rem;color:var(--text-secondary);cursor:pointer;"><input type="checkbox" class="nf-auto-action" value="${a}" checked style="width:12px;height:12px;">${a}</label>`).join("")}
              </div>
            </div>
          </div>
          <button id="nf-auto-create" class="btn btn-primary" style="padding:0.45rem 1rem;font-size:0.78rem;"><i class="fa-solid fa-plus"></i> Create Workflow</button>
        </div>
        <h4 style="font-size:0.82rem;color:#e8edf5;margin-bottom:0.5rem;">Active Workflows</h4>
        <div style="display:grid;gap:0.5rem;">${DATA.workflows.map(w => `<div class="glass-card" style="padding:0.75rem 1rem;display:flex;align-items:center;justify-content:space-between;">
          <div><div style="font-size:0.82rem;color:#e8edf5;font-weight:600;">${esc(w.name)}</div><div style="font-size:0.7rem;color:var(--text-muted);">Trigger: ${w.trigger} · ${w.runs} runs · Actions: ${w.actions.join(", ")}</div></div>
          <span style="font-size:0.65rem;padding:0.15rem 0.5rem;border-radius:10px;background:${w.active?"rgba(16,185,129,0.15)":"rgba(244,63,94,0.15)"};color:${w.active?"#6ee7b7":"#fca5a5"};">${w.active?"Active":"Inactive"}</span>
        </div>`).join("")}</div>
      </div>`;
  };

  // ============================
  // 4. AI Organization Digital Twin
  // ============================
  window.__nf["screen-digital-twin"] = function() {
    const c = el("screen-digital-twin"); if (!c) return;
    const content = c.querySelector(".nf-screen-content") || c;
    const depts = DATA.departments;
    content.innerHTML = `
      <div style="padding:1rem 1.5rem;">
        <h2 style="font-family:var(--font-display);font-size:1.1rem;color:#f3f4f6;margin-bottom:0.25rem;"><i class="fa-solid fa-cube" style="color:#818cf8;margin-right:0.5rem;"></i>AI Organization Digital Twin</h2>
        <p style="font-size:0.8rem;color:var(--text-muted);margin-bottom:1rem;">Real-time virtual representation of the entire organization.</p>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:0.75rem;margin-bottom:1rem;">
          ${depts.map(d => `<div class="glass-card" style="padding:1rem;border-left:3px solid ${d.color};">
            <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:0.5rem;">
              <div><div style="font-size:0.85rem;color:#e8edf5;font-weight:600;">${esc(d.name)}</div><div style="font-size:0.7rem;color:var(--text-muted);">Head: ${esc(d.head)}</div></div>
              <span style="font-size:0.65rem;padding:0.15rem 0.5rem;border-radius:10px;background:rgba(${d.health>85?'16,185,129':d.health>70?'245,158,11':'244,63,94'},0.15);color:${d.health>85?'#6ee7b7':d.health>70?'#fbbf24':'#fca5a5'};">${d.health}%</span>
            </div>
            <div style="display:flex;gap:1rem;font-size:0.72rem;color:var(--text-muted);"><span>👥 ${d.employees} employees</span><span>📋 ${d.projects} projects</span><span>📊 ${d.meetings} meetings</span></div>
          </div>`).join("")}
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;">
          <div class="glass-card" style="padding:1rem;">
            <h4 style="font-size:0.82rem;color:#e8edf5;margin-bottom:0.5rem;">Live Organization Status</h4>
            <div style="display:grid;gap:0.4rem;">${depts.map(d => `<div><div style="display:flex;justify-content:space-between;font-size:0.72rem;color:var(--text-muted);margin-bottom:0.15rem;"><span>${esc(d.name)}</span><span>${d.health}%</span></div><div style="height:4px;background:rgba(255,255,255,0.06);border-radius:2px;"><div style="height:100%;width:${d.health}%;background:${d.color};border-radius:2px;"></div></div></div>`).join("")}</div>
          </div>
          <div class="glass-card" style="padding:1rem;">
            <h4 style="font-size:0.82rem;color:#e8edf5;margin-bottom:0.5rem;">Employee Connections</h4>
            <div style="display:flex;flex-wrap:wrap;gap:0.4rem;">${DATA.employees.map(e => `<div style="padding:0.3rem 0.6rem;background:rgba(99,102,241,0.06);border:1px solid var(--card-border);border-radius:6px;font-size:0.72rem;color:#a5b4fc;"><i class="fa-solid fa-user" style="margin-right:0.3rem;"></i>${esc(e.name)}</div>`).join("")}</div>
            <p style="font-size:0.72rem;color:var(--text-muted);margin-top:0.5rem;">${depts.reduce((s,d)=>s+d.employees,0)} employees · ${depts.length} departments · ${DATA.projects.length} active projects</p>
          </div>
        </div>
      </div>`;
  };

  // ============================
  // 5. Company Knowledge Center
  // ============================
  window.__nf["screen-knowledge-center"] = function() {
    const c = el("screen-knowledge-center"); if (!c) return;
    const content = c.querySelector(".nf-screen-content") || c;
    const docs = DATA.knowledgeDocs;
    content.innerHTML = `
      <div style="padding:1rem 1.5rem;">
        <h2 style="font-family:var(--font-display);font-size:1.1rem;color:#f3f4f6;margin-bottom:0.25rem;"><i class="fa-solid fa-building-columns" style="color:#818cf8;margin-right:0.5rem;"></i>Company Knowledge Center</h2>
        <p style="font-size:0.8rem;color:var(--text-muted);margin-bottom:1rem;">AI answers questions only from company data. Policies, handbooks, and documentation.</p>
        <div class="glass-card" style="padding:1rem;margin-bottom:1rem;background:linear-gradient(135deg,rgba(99,102,241,0.06),rgba(15,22,42,0.4));">
          <div style="display:flex;gap:0.5rem;margin-bottom:0.75rem;">
            <input type="text" id="nf-kc-query" placeholder="Ask a question about company policies..." class="form-input" style="flex:1;padding:0.5rem 0.75rem;font-size:0.8rem;">
            <button id="nf-kc-ask" class="btn btn-primary" style="padding:0.5rem 1rem;font-size:0.78rem;"><i class="fa-solid fa-question"></i> Ask</button>
          </div>
          <div id="nf-kc-answer" style="font-size:0.78rem;color:var(--text-muted);">Ask about company policies, HR rules, project documentation, or employee handbook.</div>
        </div>
        <div style="display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:1rem;">
          ${["All","HR Policy","SOP","Technical","Handbook","Compliance"].map(cat => `<button class="nf-kc-filter" data-cat="${cat}" style="padding:0.3rem 0.75rem;border-radius:6px;border:1px solid var(--card-border);background:${cat==="All"?"rgba(99,102,241,0.15)":"transparent"};color:${cat==="All"?"#a5b4fc":"var(--text-secondary)"};font-size:0.72rem;cursor:pointer;">${cat}</button>`).join("")}
        </div>
        <div id="nf-kc-docs" style="display:grid;gap:0.5rem;">${docs.map(d => `<div class="glass-card" style="padding:0.65rem 0.75rem;display:flex;align-items:center;justify-content:space-between;">
          <div><div style="font-size:0.8rem;color:#e8edf5;">${esc(d.title)}</div><div style="font-size:0.68rem;color:var(--text-muted);">${esc(d.type)} · ${esc(d.dept)} · v${Math.floor(Math.random()*5)+1}.0</div></div>
          <i class="fa-solid fa-file-export" style="color:#818cf8;font-size:0.75rem;cursor:pointer;"></i>
        </div>`).join("")}</div>
      </div>`;
    setTimeout(() => {
      const inp = el("nf-kc-query"), btn = el("nf-kc-ask"), ans = el("nf-kc-answer");
      if (!inp||!btn||!ans) return;
      const doAsk = () => {
        const q = inp.value.trim().toLowerCase();
        if (!q) { ans.innerHTML = "Please enter a question."; return; }
        const matches = docs.filter(d => d.title.toLowerCase().includes(q)||d.type.toLowerCase().includes(q)||d.dept.toLowerCase().includes(q));
        if (matches.length) ans.innerHTML = '✅ Found <strong>'+matches.length+'</strong> relevant documents.<br>'+matches.map(m=>'📄 <strong>'+esc(m.title)+'</strong> ('+esc(m.type)+')').join('<br>');
        else ans.innerHTML = '📚 Based on company policies: <strong>"'+esc(q)+'"</strong><br>According to our documentation, this is handled under the '+(['HR Policy','SOP','Technical Documentation','Employee Handbook'][Math.floor(Math.random()*4)])+'. Please check with your department head for specific details.';
      };
      btn.onclick = doAsk;
      inp.onkeydown = e => { if (e.key === "Enter") doAsk(); };
      document.querySelectorAll(".nf-kc-filter").forEach(b => b.onclick = function() {
        document.querySelectorAll(".nf-kc-filter").forEach(f => { f.style.background="transparent";f.style.color="var(--text-secondary)"; });
        this.style.background="rgba(99,102,241,0.15)"; this.style.color="#a5b4fc";
        const cat = this.dataset.cat;
        const filtered = cat === "All" ? docs : docs.filter(d => d.type === cat);
        const container = el("nf-kc-docs");
        if (container) container.innerHTML = filtered.map(d => `<div class="glass-card" style="padding:0.65rem 0.75rem;display:flex;align-items:center;justify-content:space-between;"><div><div style="font-size:0.8rem;color:#e8edf5;">${esc(d.title)}</div><div style="font-size:0.68rem;color:var(--text-muted);">${esc(d.type)} · ${esc(d.dept)}</div></div><i class="fa-solid fa-file-export" style="color:#818cf8;font-size:0.75rem;cursor:pointer;"></i></div>`).join("");
      });
    }, 100);
  };

  // ============================
  // 6. AI Meeting Simulator
  // ============================
  window.__nf["screen-meeting-sim"] = function() {
    const c = el("screen-meeting-sim"); if (!c) return;
    const content = c.querySelector(".nf-screen-content") || c;
    const scenarios = [
      {name:"Sales Meeting Practice", icon:"fa-handshake", color:"#34d399", desc:"Practice client sales pitch with AI feedback"},
      {name:"HR Interview Practice", icon:"fa-user-tie", color:"#818cf8", desc:"Mock HR interview with evaluation"},
      {name:"Client Meeting Practice", icon:"fa-briefcase", color:"#fbbf24", desc:"Simulate client discussion scenarios"},
      {name:"Team Discussion", icon:"fa-people-group", color:"#f472b6", desc:"Practice team meeting facilitation"},
      {name:"Presentation Practice", icon:"fa-chart-simple", color:"#a78bfa", desc:"Present slides and get AI feedback"}
    ];
    content.innerHTML = `
      <div style="padding:1rem 1.5rem;">
        <h2 style="font-family:var(--font-display);font-size:1.1rem;color:#f3f4f6;margin-bottom:0.25rem;"><i class="fa-solid fa-robot" style="color:#818cf8;margin-right:0.5rem;"></i>AI Meeting Simulator</h2>
        <p style="font-size:0.8rem;color:var(--text-muted);margin-bottom:1.25rem;">Practice meetings with AI. Get scored on communication, confidence, and effectiveness.</p>
        <div id="nf-sim-scenarios" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:0.75rem;margin-bottom:1rem;">${scenarios.map(s => `<div class="glass-card nf-sim-card" style="padding:1rem;text-align:center;cursor:pointer;border:1px solid var(--card-border);" data-scenario="${esc(s.name)}">
          <div style="width:48px;height:48px;border-radius:12px;background:${s.color}15;display:flex;align-items:center;justify-content:center;margin:0 auto 0.5rem;"><i class="fa-solid ${s.icon}" style="color:${s.color};font-size:1.1rem;"></i></div>
          <div style="font-size:0.82rem;color:#e8edf5;font-weight:600;">${esc(s.name)}</div>
          <div style="font-size:0.7rem;color:var(--text-muted);margin-top:0.25rem;">${esc(s.desc)}</div>
        </div>`).join("")}</div>
        <div id="nf-sim-active" class="glass-card" style="padding:1.25rem;display:none;">
          <div id="nf-sim-status" style="text-align:center;padding:2rem;color:var(--text-muted);font-size:0.85rem;"><i class="fa-solid fa-spinner fa-spin" style="font-size:1.5rem;display:block;margin-bottom:0.5rem;color:#818cf8;"></i>Starting simulation...</div>
        </div>
        <div class="glass-card" style="padding:1rem;">
          <h4 style="font-size:0.82rem;color:#e8edf5;margin-bottom:0.5rem;">Your Practice History</h4>
          <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:0.5rem;">
            ${["Sales Pitch","HR Interview","Team Standup","Quarterly Review","One-on-One"].map((n,i) => `<div style="padding:0.5rem;background:rgba(99,102,241,0.04);border:1px solid var(--card-border);border-radius:6px;text-align:center;"><div style="font-size:0.72rem;color:var(--text-muted);">${n}</div><div style="font-size:0.9rem;font-weight:700;color:#a5b4fc;">${80+i*3}%</div><div style="font-size:0.65rem;color:var(--text-muted);">Score</div></div>`).join("")}
          </div>
        </div>
      </div>`;
    setTimeout(() => {
      document.querySelectorAll(".nf-sim-card").forEach(card => {
        card.onclick = function() {
          const name = this.dataset.scenario;
          const active = el("nf-sim-active");
          const status = el("nf-sim-status");
          active.style.display = "block";
          status.innerHTML = '<i class="fa-solid fa-spinner fa-spin" style="font-size:1.5rem;display:block;margin-bottom:0.5rem;color:#818cf8;"></i><div>Starting <strong>'+esc(name)+'</strong>...</div>';
          setTimeout(() => {
            const scores = {communication: Math.floor(Math.random()*30+65), confidence: Math.floor(Math.random()*30+60), clarity: Math.floor(Math.random()*30+70), pace: Math.floor(Math.random()*25+70)};
            status.innerHTML = `
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem;">
                <h4 style="font-size:0.9rem;color:#e8edf5;margin:0;"><i class="fa-solid fa-circle-check" style="color:#34d399;margin-right:0.4rem;"></i>${esc(name)} Complete</h4>
                <span style="font-size:1.2rem;font-weight:700;color:#818cf8;">${Math.floor((scores.communication+scores.confidence+scores.clarity+scores.pace)/4)}%</span>
              </div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;">${Object.entries(scores).map(([k,v]) => `<div><div style="display:flex;justify-content:space-between;font-size:0.72rem;color:var(--text-muted);margin-bottom:0.15rem;"><span>${k.charAt(0).toUpperCase()+k.slice(1)}</span><span>${v}%</span></div><div style="height:4px;background:rgba(255,255,255,0.06);border-radius:2px;"><div style="height:100%;width:${v}%;background:${v>80?"#34d399":v>70?"#fbbf24":"#f43f5e"};border-radius:2px;"></div></div></div>`).join("")}</div>
              <p style="font-size:0.78rem;color:var(--text-muted);margin-top:0.75rem;text-align:left;"><i class="fa-solid fa-lightbulb" style="color:#fbbf24;margin-right:0.3rem;"></i> AI Feedback: ${["Good pace and clarity. Try to reduce filler words.","Strong presentation. Work on confidence in Q&A.","Well structured. Improve engagement with examples."][Math.floor(Math.random()*3)]}</p>`;
          }, 2000);
        };
      });
    }, 100);
  };

  // ============================
  // 7. Executive Intelligence Center
  // ============================
  window.__nf["screen-exec-intel"] = function() {
    const c = el("screen-exec-intel"); if (!c) return;
    const content = c.querySelector(".nf-screen-content") || c;
    const depts = DATA.departments;
    const orgHealth = Math.floor(depts.reduce((s,d)=>s+d.health,0)/depts.length);
    const totalBudget = DATA.projects.reduce((s,p)=>s+p.budget,0);
    const totalSpent = DATA.projects.reduce((s,p)=>s+p.spent,0);
    content.innerHTML = `
      <div style="padding:1rem 1.5rem;">
        <h2 style="font-family:var(--font-display);font-size:1.1rem;color:#f3f4f6;margin-bottom:0.25rem;"><i class="fa-solid fa-chart-line" style="color:#818cf8;margin-right:0.5rem;"></i>Executive Intelligence Center</h2>
        <p style="font-size:0.8rem;color:var(--text-muted);margin-bottom:1rem;">CEO-level dashboard showing organization health, performance, and risks.</p>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:0.75rem;margin-bottom:1rem;">
          <div class="glass-card" style="padding:1rem;text-align:center;"><div style="font-size:1.8rem;font-weight:700;color:#34d399;">${orgHealth}%</div><div style="font-size:0.72rem;color:var(--text-muted);">Organization Health</div></div>
          <div class="glass-card" style="padding:1rem;text-align:center;"><div style="font-size:1.8rem;font-weight:700;color:#818cf8;">${DATA.projects.length}</div><div style="font-size:0.72rem;color:var(--text-muted);">Active Projects</div></div>
          <div class="glass-card" style="padding:1rem;text-align:center;"><div style="font-size:1.8rem;font-weight:700;color:#fbbf24;">${totalBudget.toLocaleString()}</div><div style="font-size:0.72rem;color:var(--text-muted);">Total Budget</div></div>
          <div class="glass-card" style="padding:1rem;text-align:center;"><div style="font-size:1.8rem;font-weight:700;color:#f472b6;">${Math.round((totalSpent/totalBudget)*100)}%</div><div style="font-size:0.72rem;color:var(--text-muted);">Budget Used</div></div>
        </div>
        <div style="display:grid;grid-template-columns:2fr 1fr;gap:0.75rem;">
          <div class="glass-card" style="padding:1rem;">
            <h4 style="font-size:0.82rem;color:#e8edf5;margin-bottom:0.5rem;">Project Status</h4>
            <div style="display:grid;gap:0.5rem;">${DATA.projects.map(p => `<div><div style="display:flex;justify-content:space-between;font-size:0.72rem;margin-bottom:0.15rem;"><span style="color:#e8edf5;">${esc(p.name)}</span><span style="color:${p.risk==="Low"?"#34d399":p.risk==="Medium"?"#fbbf24":"#f43f5e"};">${p.risk} Risk</span></div><div style="height:6px;background:rgba(255,255,255,0.06);border-radius:3px;"><div style="height:100%;width:${p.progress}%;background:${p.progress>80?"#34d399":p.progress>40?"#fbbf24":"#f43f5e"};border-radius:3px;"></div></div><div style="font-size:0.65rem;color:var(--text-muted);margin-top:0.1rem;">${p.progress}% · ${esc(p.lead)} · Due ${p.deadline}</div></div>`).join("")}</div>
          </div>
          <div class="glass-card" style="padding:1rem;">
            <h4 style="font-size:0.82rem;color:#e8edf5;margin-bottom:0.5rem;">Risk Alerts</h4>
            <div style="display:grid;gap:0.4rem;">
              <div style="padding:0.4rem 0.6rem;background:rgba(244,63,94,0.08);border:1px solid rgba(244,63,94,0.15);border-radius:6px;"><div style="font-size:0.72rem;color:#fca5a5;"><i class="fa-solid fa-triangle-exclamation" style="margin-right:0.3rem;"></i>Mobile App v2 behind schedule</div></div>
              <div style="padding:0.4rem 0.6rem;background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.15);border-radius:6px;"><div style="font-size:0.72rem;color:#fbbf24;"><i class="fa-solid fa-clock" style="margin-right:0.3rem;"></i>Q2 budget at 85% utilization</div></div>
              <div style="padding:0.4rem 0.6rem;background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.15);border-radius:6px;"><div style="font-size:0.72rem;color:#6ee7b7;"><i class="fa-solid fa-check" style="margin-right:0.3rem;"></i>Security Audit completed on time</div></div>
            </div>
          </div>
        </div>
      </div>`;
  };

  // ============================
  // 8. AI Project Intelligence Center
  // ============================
  window.__nf["screen-project-intel"] = function() {
    const c = el("screen-project-intel"); if (!c) return;
    const content = c.querySelector(".nf-screen-content") || c;
    content.innerHTML = `
      <div style="padding:1rem 1.5rem;">
        <h2 style="font-family:var(--font-display);font-size:1.1rem;color:#f3f4f6;margin-bottom:0.25rem;"><i class="fa-solid fa-heart-pulse" style="color:#818cf8;margin-right:0.5rem;"></i>AI Project Intelligence Center</h2>
        <p style="font-size:0.8rem;color:var(--text-muted);margin-bottom:1rem;">Complete AI-powered project monitoring with risk prediction and resource optimization.</p>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:0.75rem;margin-bottom:1rem;">
          ${DATA.projects.map(p => {
            const delayRisk = Math.floor(Math.random()*40+20);
            const costRisk = Math.floor((p.spent/p.budget)*100);
            return `<div class="glass-card" style="padding:1rem;border-left:3px solid ${delayRisk>60?'#f43f5e':delayRisk>40?'#fbbf24':'#34d399'};">
              <div style="display:flex;justify-content:space-between;margin-bottom:0.5rem;"><span style="font-size:0.85rem;color:#e8edf5;font-weight:600;">${esc(p.name)}</span><span style="font-size:0.65rem;padding:0.1rem 0.4rem;border-radius:4px;background:rgba(99,102,241,0.1);color:#a5b4fc;">${p.status}</span></div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.35rem;font-size:0.7rem;">
                <div style="padding:0.3rem;background:rgba(99,102,241,0.04);border-radius:4px;"><span style="color:var(--text-muted);">Progress</span><br><span style="color:#e8edf5;font-weight:600;">${p.progress}%</span></div>
                <div style="padding:0.3rem;background:rgba(99,102,241,0.04);border-radius:4px;"><span style="color:var(--text-muted);">Delay Risk</span><br><span style="color:${delayRisk>60?'#f43f5e':delayRisk>40?'#fbbf24':'#34d399'};font-weight:600;">${delayRisk}%</span></div>
                <div style="padding:0.3rem;background:rgba(99,102,241,0.04);border-radius:4px;"><span style="color:var(--text-muted);">Budget Used</span><br><span style="color:${costRisk>80?'#f43f5e':costRisk>60?'#fbbf24':'#34d399'};font-weight:600;">${costRisk}%</span></div>
                <div style="padding:0.3rem;background:rgba(99,102,241,0.04);border-radius:4px;"><span style="color:var(--text-muted);">Deadline</span><br><span style="color:#e8edf5;font-weight:600;">${p.deadline}</span></div>
              </div>
            </div>`;
          }).join("")}
        </div>
      </div>`;
  };

  // ============================
  // 9. AI Decision Intelligence
  // ============================
  window.__nf["screen-decision-intel"] = function() {
    const c = el("screen-decision-intel"); if (!c) return;
    const content = c.querySelector(".nf-screen-content") || c;
    const dc = DATA.decisions;
    content.innerHTML = `
      <div style="padding:1rem 1.5rem;">
        <h2 style="font-family:var(--font-display);font-size:1.1rem;color:#f3f4f6;margin-bottom:0.25rem;"><i class="fa-solid fa-scale-balanced" style="color:#818cf8;margin-right:0.5rem;"></i>AI Decision Intelligence</h2>
        <p style="font-size:0.8rem;color:var(--text-muted);margin-bottom:1rem;">Analyze, track, and improve organizational decisions.</p>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:0.75rem;margin-bottom:1rem;">
          <div class="glass-card" style="padding:1rem;text-align:center;"><div style="font-size:1.5rem;font-weight:700;color:#34d399;">${dc.filter(d=>d.success).length}/${dc.length}</div><div style="font-size:0.72rem;color:var(--text-muted);">Successful Decisions</div></div>
          <div class="glass-card" style="padding:1rem;text-align:center;"><div style="font-size:1.5rem;font-weight:700;color:#818cf8;">$${dc.reduce((s,d)=>s+d.cost,0).toLocaleString()}</div><div style="font-size:0.72rem;color:var(--text-muted);">Total Invested</div></div>
          <div class="glass-card" style="padding:1rem;text-align:center;"><div style="font-size:1.5rem;font-weight:700;color:#fbbf24;">${Math.round(dc.filter(d=>d.success).length/dc.length*100)}%</div><div style="font-size:0.72rem;color:var(--text-muted);">Success Rate</div></div>
        </div>
        <div class="glass-card" style="padding:1rem;">
          <h4 style="font-size:0.82rem;color:#e8edf5;margin-bottom:0.5rem;">Decision History & Impact Analysis</h4>
          <div style="display:grid;gap:0.5rem;">${dc.map(d => `<div style="padding:0.6rem;background:rgba(99,102,241,0.03);border:1px solid var(--card-border);border-radius:6px;">
            <div style="display:flex;justify-content:space-between;align-items:center;"><span style="font-size:0.8rem;color:#e8edf5;font-weight:600;">${esc(d.decision)}</span><span style="font-size:0.65rem;padding:0.1rem 0.4rem;border-radius:4px;background:${d.success?"rgba(16,185,129,0.15)":"rgba(244,63,94,0.15)"};color:${d.success?"#6ee7b7":"#fca5a5"};">${d.success?"Success":"Failed"}</span></div>
            <div style="font-size:0.72rem;color:var(--text-muted);margin-top:0.2rem;">${esc(d.impact)} · $${d.cost.toLocaleString()} · ${esc(d.dept)} · ${d.date}</div>
          </div>`).join("")}</div>
        </div>
      </div>`;
  };

  // ============================
  // 10. AI Report Studio
  // ============================
  window.__nf["screen-report-studio"] = function() {
    const c = el("screen-report-studio"); if (!c) return;
    const content = c.querySelector(".nf-screen-content") || c;
    content.innerHTML = `
      <div style="padding:1rem 1.5rem;">
        <h2 style="font-family:var(--font-display);font-size:1.1rem;color:#f3f4f6;margin-bottom:0.25rem;"><i class="fa-solid fa-file-pen" style="color:#818cf8;margin-right:0.5rem;"></i>AI Report Studio</h2>
        <p style="font-size:0.8rem;color:var(--text-muted);margin-bottom:1rem;">Generate professional reports using AI. Export as PDF, Word, Excel, or PowerPoint.</p>
        <div class="glass-card" style="padding:1rem;margin-bottom:1rem;">
          <label style="font-size:0.72rem;color:var(--text-muted);display:block;margin-bottom:0.3rem;">Report Type</label>
          <select id="nf-report-type" class="form-input" style="width:100%;padding:0.45rem 0.6rem;font-size:0.8rem;margin-bottom:0.5rem;">${DATA.reports.map(r => `<option value="${esc(r.name)}">${esc(r.name)}</option>`).join("")}</select>
          <label style="font-size:0.72rem;color:var(--text-muted);display:block;margin-bottom:0.3rem;">Format</label>
          <div style="display:flex;gap:0.5rem;margin-bottom:0.75rem;" id="nf-report-formats">${["PDF","Word","Excel","PowerPoint"].map(f => `<label style="display:flex;align-items:center;gap:0.3rem;font-size:0.75rem;color:var(--text-secondary);"><input type="radio" name="nf-format" value="${f}" ${f==="PDF"?"checked":""} style="width:12px;height:12px;">${f}</label>`).join("")}</div>
          <button id="nf-report-generate" class="btn btn-primary" style="padding:0.45rem 1rem;font-size:0.78rem;"><i class="fa-solid fa-wand-magic-sparkles"></i> Generate Report</button>
          <div id="nf-report-result" style="margin-top:0.75rem;display:none;"></div>
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:0.75rem;">
          ${DATA.reports.map(r => `<div class="glass-card" style="padding:0.75rem;">
            <div style="font-size:0.82rem;color:#e8edf5;font-weight:600;">${esc(r.name)}</div>
            <div style="font-size:0.7rem;color:var(--text-muted);margin:0.25rem 0 0.5rem;">${esc(r.desc)}</div>
            <div style="display:flex;gap:0.3rem;">${r.formats.map(f => `<span style="font-size:0.6rem;padding:0.1rem 0.3rem;border-radius:3px;background:rgba(99,102,241,0.1);color:#a5b4fc;">${f}</span>`).join("")}</div>
          </div>`).join("")}
        </div>
      </div>`;
    setTimeout(() => {
      const btn = el("nf-report-generate");
      const result = el("nf-report-result");
      if (!btn||!result) return;
      btn.onclick = () => {
        const type = el("nf-report-type")?.value || "Weekly Summary";
        const format = document.querySelector('input[name="nf-format"]:checked')?.value || "PDF";
        result.style.display = "block";
        result.innerHTML = '<p style="color:var(--text-muted);font-size:0.78rem;"><i class="fa-solid fa-spinner fa-spin"></i> Generating '+esc(type)+' report as '+format+'...</p>';
        setTimeout(() => {
          result.innerHTML = '<div style="padding:0.75rem;background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.15);border-radius:6px;"><p style="color:#6ee7b7;font-size:0.8rem;"><i class="fa-solid fa-circle-check"></i> <strong>'+esc(type)+'</strong> report generated successfully as <strong>'+format+'</strong>!</p><p style="font-size:0.72rem;color:var(--text-muted);margin-top:0.3rem;">📄 12 pages · 8 charts · 3 tables · Ready for download</p></div>';
        }, 2000);
      };
    }, 100);
  };

  // ============================
  // Dashboard AI Command Center Widget
  // ============================
  // Add AI Command Center widget to existing dashboard
  window._addDashboardAIWidget = function() {
    const dash = document.getElementById("screen-dashboard");
    if (!dash) return;
    // Check if already added
    if (document.getElementById("dash-ai-widget")) return;
    const container = dash.querySelector(".dashboard-stats");
    if (!container) return;
    const widget = document.createElement("div");
    widget.id = "dash-ai-widget";
    widget.style.cssText = "grid-column:span 2;";
    widget.innerHTML = `
      <div class="glass-card" style="padding:1rem;background:linear-gradient(135deg,rgba(99,102,241,0.08),rgba(16,185,129,0.04));border:1px solid rgba(99,102,241,0.15);">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.5rem;">
          <h4 style="font-size:0.85rem;color:#e8edf5;margin:0;"><i class="fa-solid fa-terminal" style="color:#818cf8;margin-right:0.4rem;"></i>AI Command Center</h4>
          <button class="btn btn-primary" style="padding:0.3rem 0.75rem;font-size:0.72rem;" onclick="switchScreen('screen-ai-command')">Open <i class="fa-solid fa-arrow-right"></i></button>
        </div>
        <div style="display:flex;gap:0.5rem;">
          <input type="text" id="dash-ai-input" placeholder="Ask AI to do anything..." class="form-input" style="flex:1;padding:0.4rem 0.6rem;font-size:0.78rem;">
          <button class="btn btn-primary" style="padding:0.4rem 0.75rem;font-size:0.72rem;" onclick="window._dashAICommand(document.getElementById('dash-ai-input')?.value)"><i class="fa-solid fa-arrow-right"></i></button>
        </div>
        <div id="dash-ai-response" style="margin-top:0.5rem;font-size:0.75rem;color:var(--text-muted);display:none;"></div>
        <div style="display:flex;gap:0.35rem;flex-wrap:wrap;margin-top:0.5rem;">
          ${["Today's Meetings","Delayed Tasks","Weekly Report","Productivity Score"].map(s => `<button class="btn btn-secondary" style="padding:0.2rem 0.5rem;font-size:0.65rem;" onclick="document.getElementById('dash-ai-input').value='${s}';window._dashAICommand('${s}')">${s}</button>`).join("")}
        </div>
      </div>`;
    container.parentNode.insertBefore(widget, container.nextSibling);
  };
  window._dashAICommand = function(q) {
    if (!q) return;
    const resp = document.getElementById("dash-ai-response");
    if (!resp) return;
    resp.style.display = "block";
    const ql = q.toLowerCase();
    const ms = window.meetings || [];
    const allTasks = []; ms.forEach(m => allTasks.push(...(m.actionItems||[])));
    let answer;
    if (ql.includes("today")||ql.includes("meeting")) answer = "📅 Found <strong>"+ms.length+"</strong> meetings. "+(ms.length?"Latest: "+ms.slice(0,2).map(m=>m.title).join(", "):"");
    else if (ql.includes("task")||ql.includes("delayed")) { const p = allTasks.filter(t=>t.status!=="Completed"); answer = "📋 <strong>"+p.length+"</strong> pending tasks. "+(p.length?"Top: "+p.slice(0,2).map(t=>t.title).join(", "):""); }
    else if (ql.includes("report")||ql.includes("weekly")) answer = "📊 Weekly report: "+ms.length+" meetings, "+allTasks.filter(t=>t.status==="Completed").length+" tasks done, Loading...";
    else if (ql.includes("productivity")) answer = "⭐ Your productivity score: <strong>"+Math.floor(Math.random()*20+75)+"%</strong><br>Meeting score: "+Math.floor(Math.random()*20+70)+"% · Task score: "+Math.floor(Math.random()*20+75)+"%";
    else answer = "✅ Processed: <strong>"+esc(q)+"</strong>. Check the relevant section.";
    resp.innerHTML = '<div style="display:flex;gap:0.5rem;"><i class="fa-solid fa-robot" style="color:#818cf8;"></i><div style="color:#c8d0dc;line-height:1.5;">'+answer+'</div></div>';
  };


})();
