$content = Get-Content 'c:\Users\godav\Downloads\project\static\app.js' -Raw

$old = @'
    // Auto-navigate based on portal
    const landingScreens = { employee: "screen-dashboard", student: "screen-student-dashboard", staff: "screen-staff-dashboard", admin: "screen-admin" };
    setTimeout(() => switchScreen(landingScreens[portal] || "screen-dashboard"), 50);


    // Load general database and components

    initDatabase();

    renderDashboardStats();
    renderDashboardFeed();

    renderDemoPicker();

    renderDashboardCalendar();

    renderDashboardTaskCategories();

    initDashQuickActions();
    initContactRating();
  }
'@

$new = @'
    // Auto-navigate based on portal
    const landingScreens = { employee: "screen-dashboard", student: "screen-student-dashboard", staff: "screen-staff-dashboard", admin: "screen-admin" };
    const targetScreen = landingScreens[portal] || "screen-dashboard";
    switchScreen(targetScreen);

    // Load general database and components
    try { initDatabase(); } catch(e) { console.warn("initDatabase:", e); }
    try { renderDashboardStats(); } catch(e) { console.warn("renderDashboardStats:", e); }
    try { renderDashboardFeed(); } catch(e) { console.warn("renderDashboardFeed:", e); }
    try { renderDemoPicker(); } catch(e) { console.warn("renderDemoPicker:", e); }
    try { renderDashboardCalendar(); } catch(e) { console.warn("renderDashboardCalendar:", e); }
    try { renderDashboardTaskCategories(); } catch(e) { console.warn("renderDashboardTaskCategories:", e); }
    try { initDashQuickActions(); } catch(e) { console.warn("initDashQuickActions:", e); }
    try { initContactRating(); } catch(e) { console.warn("initContactRating:", e); }
  }
'@

$content = $content.Replace($old, $new)
Set-Content 'c:\Users\godav\Downloads\project\static\app.js' $content -NoNewline
Write-Host "Done"
