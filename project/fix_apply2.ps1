$lines = Get-Content 'c:\Users\godav\Downloads\project\static\app.js'
$total = $lines.Count

$newLines = @(
    '    // Auto-navigate based on portal',
    '    const landingScreens = { employee: "screen-dashboard", student: "screen-student-dashboard", staff: "screen-staff-dashboard", admin: "screen-admin" };',
    '    const _targetScreen = landingScreens[portal] || "screen-dashboard";',
    '    switchScreen(_targetScreen);',
    '',
    '    // Load general database and components',
    '    try { initDatabase(); } catch(e) { console.warn("initDatabase:", e); }',
    '    try { renderDashboardStats(); } catch(e) { console.warn("renderDashboardStats:", e); }',
    '    try { renderDashboardFeed(); } catch(e) { console.warn("renderDashboardFeed:", e); }',
    '    try { renderDemoPicker(); } catch(e) { console.warn("renderDemoPicker:", e); }',
    '    try { renderDashboardCalendar(); } catch(e) { console.warn("renderDashboardCalendar:", e); }',
    '    try { renderDashboardTaskCategories(); } catch(e) { console.warn("renderDashboardTaskCategories:", e); }',
    '    try { initDashQuickActions(); } catch(e) { console.warn("initDashQuickActions:", e); }',
    '    try { initContactRating(); } catch(e) { console.warn("initContactRating:", e); }'
)

# Lines are 1-indexed, array is 0-indexed
# Replace lines 732-744 (indices 731-743)
$before = $lines[0..730]
$after  = $lines[744..($total-1)]

$result = $before + $newLines + $after
Set-Content 'c:\Users\godav\Downloads\project\static\app.js' $result -NoNewline
Write-Host "Done. Total lines: $($result.Count)"
