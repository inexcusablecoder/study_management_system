// Live clock
function updateTime() {
  const now = new Date();
  const timeEl = document.getElementById('sidebarTime');
  const dateEl = document.getElementById('topbarDate');
  if (timeEl) timeEl.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  if (dateEl) dateEl.textContent = now.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
}
updateTime();
setInterval(updateTime, 1000);

// Sidebar toggle (mobile)
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar = document.getElementById('sidebar');
if (sidebarToggle && sidebar) {
  sidebarToggle.addEventListener('click', () => sidebar.classList.toggle('open'));
  document.addEventListener('click', (e) => {
    if (!sidebar.contains(e.target) && e.target !== sidebarToggle) {
      sidebar.classList.remove('open');
    }
  });
}

// Auto-dismiss flash messages
setTimeout(() => {
  document.querySelectorAll('.flash').forEach(el => {
    el.style.transition = 'opacity 0.4s';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 400);
  });
}, 4000);

// Set today's date as default for date inputs
document.querySelectorAll('input[type="date"]:not([value])').forEach(input => {
  const today = new Date().toISOString().split('T')[0];
  input.value = today;
});

// Chart.js global defaults for dark theme
if (typeof Chart !== 'undefined') {
  Chart.defaults.color = '#94a3b8';
  Chart.defaults.borderColor = 'rgba(255,255,255,0.05)';
  Chart.defaults.font.family = "'Inter', sans-serif";
  Chart.defaults.plugins.tooltip.backgroundColor = '#1e293b';
  Chart.defaults.plugins.tooltip.borderColor = 'rgba(255,255,255,0.1)';
  Chart.defaults.plugins.tooltip.borderWidth = 1;
  Chart.defaults.plugins.tooltip.padding = 10;
  Chart.defaults.plugins.tooltip.titleColor = '#f1f5f9';
  Chart.defaults.plugins.tooltip.bodyColor = '#94a3b8';
}
