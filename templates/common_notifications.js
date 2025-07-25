// API Base URL'i buraya gelecek - Lütfen kendi Render Flask uygulamanızın URL'si ile değiştirin
const API_BASE_URL = "https://ser-proje.onrender.com";

// Genel Toast bildirim fonksiyonu
function showToast(message, isError = false) {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');

    if (!toast || !toastMessage) {
        console.error("Toast elementleri bulunamadı!");
        return;
    }

    toastMessage.textContent = message;
    toast.className = "toast show";
    if (isError) {
        toast.classList.add("error");
    } else {
        toast.classList.remove("error");
    }

    setTimeout(() => {
        toast.className = "toast";
    }, 3000);
}

// Kullanıcı bilgilerini localStorage'dan yükleyen fonksiyon
function loadUserInfo() {
    const user = JSON.parse(localStorage.getItem('user')) || JSON.parse(localStorage.getItem('currentUser'));
    if (user) {
        document.getElementById('userName').textContent = user.fullname || user.username || 'Kullanıcı';
        document.getElementById('userRole').textContent = user.role || 'Rol Yok';
        const userAvatarElement = document.getElementById('userAvatar');
        if (userAvatarElement) {
            const nameToUseForAvatar = user.fullname || user.username;
            if (nameToUseForAvatar) {
                const names = nameToUseForAvatar.split(' ');
                let initials = names[0][0];
                if (names.length > 1) {
                    initials += names[names.length-1][0];
                }
                userAvatarElement.textContent = initials.toUpperCase();
            } else {
                userAvatarElement.textContent = 'AD';
            }
        }
        fetchUnreadNotificationsCount(user.id); // Okunmamış bildirim sayısını çek
    } else {
        console.log("LocalStorage'da kullanıcı verisi bulunamadı. Giriş sayfasına yönlendiriliyor...");
        window.location.href = 'login.html';
    }
}

// Okunmamış bildirim sayısını çeken ve zil ikonunu güncelleyen fonksiyon
async function fetchUnreadNotificationsCount(userId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/notifications/unread-count?user_id=${userId}`);
        const data = await response.json();
        const notificationButton = document.querySelector('.notification-btn');
        if (notificationButton) {
            const unreadCount = data.unread_count || 0;
            if (unreadCount > 0) {
                notificationButton.setAttribute('data-count', unreadCount);
                notificationButton.classList.add('has-notifications');
            } else {
                notificationButton.setAttribute('data-count', '0');
                notificationButton.classList.remove('has-notifications');
            }
        }
    } catch (error) {
        console.error('Okunmamış bildirim sayısı çekilemedi:', error);
        const notificationButton = document.querySelector('.notification-btn');
        if (notificationButton) {
            notificationButton.setAttribute('data-count', '!'); // Hata durumunda ünlem işareti
            notificationButton.classList.add('has-notifications');
        }
    }
}

// Bildirimleri çeken ve listeye ekleyen fonksiyon (sadece bildirim.html için geçerli)
async function fetchAndDisplayNotifications() {
    const user = JSON.parse(localStorage.getItem('user')) || JSON.parse(localStorage.getItem('currentUser'));
    if (!user || !user.id) {
        console.error("Kullanıcı ID bulunamadı.");
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/notifications?user_id=${user.id}`);
        const notifications = await response.json();
        const notificationList = document.getElementById('notificationList');
        const emptyState = document.getElementById('emptyState');

        if (!notificationList || !emptyState) {
            // Bu fonksiyon sadece bildirim.html'de tam listeyi göstermek için kullanılır.
            // Diğer sayfalarda bu elementler olmadığı için hata vermesi normaldir.
            // Bu nedenle burada bir uyarı yerine, fonksiyonun sadece ilgili sayfada çalışmasını sağlayacağız.
            return;
        }

        notificationList.innerHTML = ''; // Listeyi temizle

        if (notifications.length === 0) {
            emptyState.style.display = 'block';
            notificationList.style.display = 'none';
        } else {
            emptyState.style.display = 'none';
            notificationList.style.display = 'block';
            notifications.forEach(notification => {
                const item = document.createElement('li');
                item.className = `notification-item ${notification.is_read === 0 ? 'unread' : ''}`;
                item.setAttribute('data-notification-id', notification.id);
                item.innerHTML = `
                    <i class="notification-item-icon ${notification.icon || 'fas fa-info-circle'}"></i>
                    <div class="notification-item-content">
                        <div class="notification-item-title">${notification.title}</div>
                        <div class="notification-item-message">${notification.message}</div>
                        <div class="notification-item-time">${formatTimeAgo(notification.created_at)}</div>
                    </div>
                    <div class="notification-actions">
                        ${notification.is_read === 0 ? `<button class="notification-action-btn mark-read-btn" title="Okundu İşaretle"><i class="fas fa-eye"></i></button>` : ''}
                    </div>
                `;
                notificationList.appendChild(item);
            });

            // "Okundu İşaretle" butonlarına olay dinleyicileri ekle
            document.querySelectorAll('.mark-read-btn').forEach(button => {
                button.addEventListener('click', async (event) => {
                    const notificationId = event.currentTarget.closest('.notification-item').dataset.notificationId;
                    await markNotificationAsRead(notificationId, user.id);
                });
            });
        }
    } catch (error) {
        console.error('Bildirimler çekilirken hata oluştu:', error);
        showToast('Bildirimler yüklenirken bir hata oluştu.', true);
    }
}

// Belirli bir bildirimi okundu olarak işaretle
async function markNotificationAsRead(notificationId, userId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/notifications/${notificationId}/read`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
        });
        const data = await response.json();
        if (response.ok) {
            showToast(data.message || 'Bildirim okundu olarak işaretlendi.');
            // Eğer bildirim sayfasındaysak listeyi yenile, değilsek sadece sayacı güncelle
            if (document.getElementById('notificationList')) {
                fetchAndDisplayNotifications();
            }
            fetchUnreadNotificationsCount(userId); // Sayıyı güncelle
        } else {
            showToast(data.message || 'Bildirim okundu olarak işaretlenemedi.', true);
        }
    } catch (error) {
        console.error('Bildirim okundu olarak işaretlenirken hata:', error);
        showToast('Bildirim okundu olarak işaretlenirken bir hata oluştu.', true);
    }
}

// Tüm bildirimleri okundu olarak işaretle
async function markAllNotificationsAsRead() {
    const user = JSON.parse(localStorage.getItem('user')) || JSON.parse(localStorage.getItem('currentUser'));
    if (!user || !user.id) {
        console.error("Kullanıcı ID bulunamadı.");
        showToast("Tüm bildirimler okundu olarak işaretlenemedi: Kullanıcı bilgisi eksik.", true);
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/notifications/mark_all_read`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: user.id })
        });
        const data = await response.json();
        if (response.ok) {
            showToast(data.message || 'Tüm bildirimler başarıyla okundu olarak işaretlendi!');
            // Eğer bildirim sayfasındaysak listeyi yenile, değilsek sadece sayacı güncelle
            if (document.getElementById('notificationList')) {
                fetchAndDisplayNotifications();
            }
            fetchUnreadNotificationsCount(user.id); // Sayıyı güncelle
        } else {
            showToast(data.message || 'Tüm bildirimler okundu olarak işaretlenemedi.', true);
        }
    } catch (error) {
        console.error('Tüm bildirimleri okundu olarak işaretlerken hata:', error);
        showToast('Tüm bildirimleri okundu olarak işaretlerken bir hata oluştu.', true);
    }
}

// Zamanı "x dakika önce" formatına dönüştüren yardımcı fonksiyon
function formatTimeAgo(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    let interval = seconds / 31536000;
    if (interval > 1) return Math.floor(interval) + " yıl önce";
    interval = seconds / 2592000;
    if (interval > 1) return Math.floor(interval) + " ay önce";
    interval = seconds / 86400;
    if (interval > 1) return Math.floor(interval) + " gün önce";
    interval = seconds / 3600;
    if (interval > 1) return Math.floor(interval) + " saat önce";
    interval = seconds / 60;
    if (interval > 1) return Math.floor(interval) + " dakika önce";
    return Math.floor(seconds) + " saniye önce";
}

// Tema değiştirme fonksiyonu
function toggleTheme() {
    const currentTheme = document.body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.body.setAttribute('data-theme', newTheme);
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.innerHTML = newTheme === 'dark'
            ? '<i class="fas fa-sun"></i>'
            : '<i class="fas fa-moon"></i>';
    }
    localStorage.setItem('theme', newTheme);
}

// Çıkış fonksiyonu
function logout() {
    localStorage.removeItem('currentUser');
    localStorage.removeItem('user');
    window.location.href = 'login.html';
}

// Ortak olay dinleyicilerini ve başlangıç fonksiyonlarını ayarlayan fonksiyon
function setupCommonListeners() {
    loadUserInfo();

    // Tema toggle butonuna event listener ekle
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            document.body.setAttribute('data-theme', savedTheme);
            themeToggle.innerHTML = savedTheme === 'dark'
                ? '<i class="fas fa-sun"></i>'
                : '<i class="fas fa-moon"></i>';
        } else {
            themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
        }
    }

    // Çıkış butonuna event listener ekle
    const logoutButton = document.getElementById('logoutButton');
    if (logoutButton) {
        logoutButton.addEventListener('click', logout);
    }

    // Hamburger menü işlevselliği
    const hamburgerMenu = document.getElementById('hamburgerMenu');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');

    if (hamburgerMenu && sidebar && mainContent) {
        hamburgerMenu.addEventListener('click', () => {
            sidebar.classList.toggle('show');
            mainContent.classList.toggle('expanded');
        });

        document.addEventListener('click', (event) => {
            if (sidebar.classList.contains('show') &&
                !sidebar.contains(event.target) &&
                !hamburgerMenu.contains(event.target)) {
                sidebar.classList.remove('show');
                mainContent.classList.remove('expanded');
            }
        });

        window.addEventListener('resize', () => {
            if (window.innerWidth > 992) {
                sidebar.classList.remove('show');
                mainContent.classList.remove('expanded');
            }
        });
    }

    // Bildirim butonuna tıklama olayı (bildirim sayfasına yönlendirme)
    const notificationButton = document.querySelector('.notification-btn');
    if (notificationButton) {
        notificationButton.addEventListener('click', () => {
            window.location.href = 'bildirim.html';
        });
    }

    // Eğer bildirim sayfasındaysak, bildirimleri yükle ve "Tümünü Okundu İşaretle" butonunu ayarla
    if (document.getElementById('notificationList')) {
        fetchAndDisplayNotifications();
        const markAllReadBtn = document.getElementById('markAllReadBtn');
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', markAllNotificationsAsRead);
        }
    }
}

// DOM içeriği tamamen yüklendiğinde ortak fonksiyonları çağır
document.addEventListener('DOMContentLoaded', setupCommonListeners);
