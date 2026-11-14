content = open('templates/index.html', encoding='utf-8').read()

# Fix 1: Sidebar collapse button visible styling
old1 = '      <button class="sidebar-collapse-btn" id="sidebar-collapse-btn" title="Toggle sidebar">\n        <i class="fa-solid fa-angles-left" id="sidebar-collapse-icon"></i>\n\n        <span class="sidebar-collapse-label">Collapse</span>\n      </button>'
new1 = '      <button class="sidebar-collapse-btn" id="sidebar-collapse-btn" title="Toggle sidebar" style="display:flex;align-items:center;gap:0.4rem;width:100%;padding:0.55rem 0.8rem;margin-top:0.5rem;background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.2);border-radius:8px;color:var(--text-secondary);cursor:pointer;font-size:0.78rem;font-weight:600;transition:all 0.2s;">\n        <i class="fa-solid fa-angles-left" id="sidebar-collapse-icon"></i>\n        <span class="sidebar-collapse-label">Collapse Sidebar</span>\n      </button>'
if old1 in content:
    content = content.replace(old1, new1)
    print('Fix 1 sidebar: OK')
else:
    print('Fix 1 sidebar: PARTIAL - trying loose match')
    content = content.replace('fa-solid fa-angles-left" id="sidebar-collapse-icon', 'fa-solid fa-chevron-left" id="sidebar-collapse-icon')
    print('Fix 1 sidebar icon: replaced')

# Fix 2: Project filter dropdown dark background
old2 = 'background: var(--bg-secondary); color: var(--text-primary); font-size: 0.8rem;">\n              <option value="">All Projects</option>'
new2 = 'background: #0c1020; color: var(--text-primary); font-size: 0.8rem; color-scheme: dark; min-width: 160px;">\n              <option value="">All Projects</option>'
if old2 in content:
    content = content.replace(old2, new2)
    print('Fix 2 proj filter: OK')
else:
    print('Fix 2 proj filter: searching...')
    idx = content.find('analytics-project-filter')
    print('analytics-project-filter at char:', idx)

# Fix 3: Add project analysis detail section inside breakdown card
old3 = '<div id="analytics-project-table" style="overflow-x: auto;"></div>\n        </div>'
new3 = '''<div id="analytics-project-table" style="overflow-x: auto;"></div>
          <div id="analytics-project-detail" style="margin-top:1rem;display:none;">
            <div style="border-top:1px solid var(--card-border);padding-top:1rem;">
              <h4 id="analytics-project-detail-title" style="font-family:var(--font-display);font-size:0.95rem;margin-bottom:0.75rem;color:var(--accent-primary);"></h4>
              <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.75rem;margin-bottom:1rem;">
                <div style="background:rgba(99,102,241,0.06);border:1px solid var(--card-border);border-radius:8px;padding:0.75rem;text-align:center;">
                  <div style="font-size:1.3rem;font-weight:700;font-family:var(--font-display);color:var(--accent-primary);" id="apd-total-tasks">0</div>
                  <div style="font-size:0.7rem;color:var(--text-muted);margin-top:0.25rem;">Total Tasks</div>
                </div>
                <div style="background:rgba(16,185,129,0.06);border:1px solid var(--card-border);border-radius:8px;padding:0.75rem;text-align:center;">
                  <div style="font-size:1.3rem;font-weight:700;font-family:var(--font-display);color:var(--success);" id="apd-completed">0</div>
                  <div style="font-size:0.7rem;color:var(--text-muted);margin-top:0.25rem;">Completed</div>
                </div>
                <div style="background:rgba(245,158,11,0.06);border:1px solid var(--card-border);border-radius:8px;padding:0.75rem;text-align:center;">
                  <div style="font-size:1.3rem;font-weight:700;font-family:var(--font-display);color:var(--warning);" id="apd-pending">0</div>
                  <div style="font-size:0.7rem;color:var(--text-muted);margin-top:0.25rem;">Pending</div>
                </div>
              </div>
              <div id="apd-task-list" style="display:flex;flex-direction:column;gap:0.4rem;max-height:220px;overflow-y:auto;"></div>
            </div>
          </div>
        </div>'''
if old3 in content:
    content = content.replace(old3, new3)
    print('Fix 3 breakdown detail: OK')
else:
    print('Fix 3: trying alternate...')
    old3b = '<div id="analytics-project-table" style="overflow-x: auto;"></div>\n\n        </div>'
    if old3b in content:
        content = content.replace(old3b, new3)
        print('Fix 3 alt: OK')
    else:
        print('Fix 3: NOT FOUND')

# Fix 4: Add sub-header page title bar below header before screens
old4 = '      <!-- SCREEN: DASHBOARD -->'
new4 = '''      <!-- Page Sub-Header Title Bar -->
      <div id="page-subheader" style="padding:0.55rem 2rem;border-bottom:1px solid var(--card-border);background:rgba(12,16,32,0.7);display:flex;align-items:center;gap:0.6rem;">
        <h1 id="page-header-title" style="font-family:var(--font-display);font-size:1.05rem;font-weight:700;background:linear-gradient(135deg,#fff,#9ca3af);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;color:transparent;margin:0;">Dashboard</h1>
        <span style="font-size:0.75rem;color:var(--text-muted);" id="page-header-subtitle"></span>
      </div>

      <!-- SCREEN: DASHBOARD -->'''
if old4 in content:
    content = content.replace(old4, new4)
    print('Fix 4 sub-header: OK')
else:
    print('Fix 4: NOT FOUND')

open('templates/index.html', 'w', encoding='utf-8').write(content)
print('SAVED')
