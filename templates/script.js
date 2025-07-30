// Gece/Gündüz modu değişimi
document.getElementById('themeToggle').addEventListener('change', function() {
  if (this.checked) {
      document.body.classList.add('night-mode');
  } else {
      document.body.classList.remove('night-mode');
  }
});

// Tablar arasında geçiş yapma
function showLogin() {
  document.getElementById('loginForm').classList.add('active');
  document.getElementById('registerForm').classList.remove('active');
  document.getElementById('loginTab').classList.add('active');
  document.getElementById('registerTab').classList.remove('active');
}

function showRegister() {
  document.getElementById('registerForm').classList.add('active');
  document.getElementById('loginForm').classList.remove('active');
  document.getElementById('registerTab').classList.add('active');
  document.getElementById('loginTab').classList.remove('active');
}

// İlk olarak Giriş yap formunu göster
window.onload = showLogin;

// Bildirim Paneli ve Sayaç (Tüm sayfalarda çalışır)
const API_BASE_URL = 'https://serotomasyon.tr';

function getCurrentUser() {
const storedUser = localStorage.getItem("currentUser");
if (!storedUser) return null;
try {
  return JSON.parse(storedUser);
} catch (e) { return null; }
}

// Bildirim panelini toggle et
function setupNotificationPanel() {
const notificationBtn = document.querySelector('.notification-btn');
const notificationPanel = document.getElementById('notificationPanel');
const closeNotificationPanel = document.getElementById('closeNotificationPanel');
if (!notificationBtn || !notificationPanel || !closeNotificationPanel) return;

notificationBtn.addEventListener('click', function(e) {
  e.stopPropagation();
  if (notificationPanel.style.display === 'none' || notificationPanel.style.display === '') {
    notificationPanel.style.display = 'flex';
    loadNotifications();
    markAllNotificationsRead();
  } else {
    notificationPanel.style.display = 'none';
  }
});
closeNotificationPanel.addEventListener('click', function(e) {
  e.stopPropagation();
  notificationPanel.style.display = 'none';
});
document.addEventListener('click', function(e) {
  if (notificationPanel.style.display === 'flex' && !notificationPanel.contains(e.target) && !notificationBtn.contains(e.target)) {
    notificationPanel.style.display = 'none';
  }
});
}

// Bildirimleri yükle (son 10 bildirim)
async function loadNotifications() {
const notifList = document.getElementById('notificationList');
const user = getCurrentUser();
if (!notifList || !user) return;
notifList.innerHTML = '<li>Yükleniyor...</li>';
try {
  const response = await fetch(`${API_BASE_URL}/api/notifications?user_id=${user.id}`);
  if (!response.ok) throw new Error('Bildirimler alınamadı');
  const data = await response.json();
  if (!Array.isArray(data) || data.length === 0) {
    notifList.innerHTML = '<li>Hiç bildirim yok.</li>';
    updateNotificationCount(0);
    return;
  }
  notifList.innerHTML = '';
  data.forEach(item => {
    notifList.innerHTML += `<li><span class='notif-icon'><i class='${getNotifIcon(item.type)}'></i></span><div><span class='notif-title'>${item.message}</span><div class='notif-time'>${formatTimeAgo(item.created_at)}</div></div></li>`;
  });
  // Okunmamışları güncelle
  updateNotificationCount(0);
} catch (err) {
  notifList.innerHTML = '<li>Bildirimler alınamadı.</li>';
}
}

// Zil üzerindeki okunmamış bildirim sayısını güncelle
async function updateNotificationCount(forceCount) {
const user = getCurrentUser();
const notifBtn = document.querySelector('.notification-btn');
let count = forceCount;
if (!user || !notifBtn) return;
if (typeof forceCount !== 'number') {
  try {
    const response = await fetch(`${API_BASE_URL}/api/notifications/count?user_id=${user.id}`);
    const data = await response.json();
    count = data.unread_count;
  } catch (e) { count = 0; }
}
let badge = notifBtn.querySelector('.notif-count');
if (!badge) {
  badge = document.createElement('span');
  badge.className = 'notif-count';
  notifBtn.appendChild(badge);
}
badge.textContent = count > 0 ? count : '';
}

// Bildirimleri okundu olarak işaretle
async function markAllNotificationsRead() {
const user = getCurrentUser();
if (!user) return;
try {
  await fetch(`${API_BASE_URL}/api/notifications/mark-read?user_id=${user.id}`, { method: 'POST' });
} catch (e) {}
}

// Bildirim tipi -> ikon eşleştirme
function getNotifIcon(type) {
switch(type) {
  case 'project_assign': return 'fas fa-user-plus';
  case 'project_update': return 'fas fa-pen-to-square';
  case 'project_delete': return 'fas fa-trash';
  case 'calendar_assign': return 'fas fa-calendar-check';
  default: return 'fas fa-info-circle';
}
}

// Zamanı "x dakika önce" formatında göster
function formatTimeAgo(dateStr) {
if (!dateStr) return '';
const now = new Date();
const date = new Date(dateStr);
const diffMs = now - date;
const diffSec = Math.floor(diffMs / 1000);
if (diffSec < 60) return `${diffSec} sn önce`;
const diffMin = Math.floor(diffSec / 60);
if (diffMin < 60) return `${diffMin} dk önce`;
const diffHour = Math.floor(diffMin / 60);
if (diffHour < 24) return `${diffHour} sa önce`;
const diffDay = Math.floor(diffHour / 24);
return `${diffDay} gün önce`;
}

// Sayfa yüklendiğinde otomatik başlat
window.addEventListener('DOMContentLoaded', function() {
setupNotificationPanel();
updateNotificationCount();
});
