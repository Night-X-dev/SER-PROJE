// common_notifications.js

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

// Custom Confirm Modal (alert yerine kullanılacak)
function showConfirmModal(title, message, onConfirm) {
    const modalHtml = `
        <div class="modal fade" id="customConfirmModal" tabindex="-1" aria-labelledby="customConfirmModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="customConfirmModalLabel">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p>${message}</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">İptal</button>
                        <button type="button" class="btn btn-danger" id="confirmActionBtn">Onayla</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Eğer modal zaten varsa kaldırma (çoklu açılmasını engeller)
    const existingModal = document.getElementById('customConfirmModal');
    if (existingModal) {
        existingModal.remove();
    }

    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const confirmModalElement = document.getElementById('customConfirmModal');
    const confirmModal = new bootstrap.Modal(confirmModalElement);
    confirmModal.show();

    document.getElementById('confirmActionBtn').onclick = () => {
        onConfirm();
        confirmModal.hide();
    };

    confirmModalElement.addEventListener('hidden.bs.modal', () => {
        confirmModalElement.remove(); // Modal kapandığında DOM'dan kaldır
    });
}

// Kullanıcı bilgilerini localStorage'dan yükleyen fonksiyon
let currentUser = null; // Global olarak tanımla

function loadUserInfo() {
    const user = JSON.parse(localStorage.getItem('user')) || JSON.parse(localStorage.getItem('currentUser'));
    if (user) {
        currentUser = user; // Global currentUser'ı ayarla
        const userNameElement = document.getElementById('userName');
        const userRoleElement = document.getElementById('userRole');
        const userAvatarElement = document.getElementById('userAvatar');

        if (userNameElement) userNameElement.textContent = user.fullname || user.username || 'Kullanıcı';
        if (userRoleElement) userRoleElement.textContent = user.role || 'Rol Yok';
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
        showToast("Oturum süreniz doldu veya giriş yapmadınız. Lütfen giriş yapın.", true);
        setTimeout(() => {
            window.location.href = 'login.html';
        }, 2000);
    }
}

// Okunmamış bildirim sayısını çeken ve zil ikonunu güncelleyen fonksiyon
async function fetchUnreadNotificationsCount(userId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/notifications/unread-count?user_id=${userId}`);
        const data = await response.json();
        const notificationButton = document.getElementById('notificationButton'); // ID ile al

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
        const notificationButton = document.getElementById('notificationButton'); // ID ile al
        if (notificationButton) {
            notificationButton.setAttribute('data-count', '!'); // Hata durumunda ünlem işareti
            notificationButton.classList.add('has-notifications');
        }
    }
}

// Bildirimleri çeken ve panele render etme fonksiyonu (panel açıldığında çağrılır)
async function fetchNotificationsForPanel(userId) {
    const notificationList = document.getElementById('notificationList');
    if (!notificationList) return;

    notificationList.innerHTML = '<div class="no-notifications"><i class="fas fa-spinner fa-spin"></i> Bildirimler yükleniyor...</div>';

    try {
        const response = await fetch(`${API_BASE_URL}/api/notifications?user_id=${userId}`);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ message: 'Sunucudan yanıt alınamadı.' }));
            throw new Error(errorData.message || `HTTP hatası! Durum: ${response.status}`);
        }
        const notifications = await response.json();

        notificationList.innerHTML = ''; // Yükleniyor mesajını temizle

        if (notifications.length === 0) {
            notificationList.innerHTML = '<div class="no-notifications"><i class="fas fa-bell-slash"></i> Henüz bildirim yok.</div>';
        } else {
            notifications.forEach(notification => {
                const item = document.createElement('div');
                item.classList.add('notification-item');
                if (notification.is_read === 0) {
                    item.classList.add('unread');
                }
                item.setAttribute('data-notification-id', notification.id);
                item.innerHTML = `
                    <div class="notification-item-icon">
                        <i class="${notification.icon || 'fas fa-info-circle'}"></i>
                    </div>
                    <div class="notification-item-content">
                        <div class="notification-item-title">${notification.title}</div>
                        <div class="notification-item-description">${notification.message}</div>
                        <div class="notification-item-time">${formatTimeAgo(notification.created_at)}</div>
                    </div>
                `;
                notificationList.appendChild(item);

                item.addEventListener('click', async () => {
                    // Bildirime tıklandığında okunmuş olarak işaretle
                    await markNotificationAsReadForPanel(notification.id, userId);
                    // İsteğe bağlı: Bildirime tıklandığında ilgili sayfaya yönlendir
                    // if (notification.link) { window.location.href = notification.link; }
                });
            });
        }
    } catch (error) {
        console.error('Bildirimler panel için çekilirken hata oluştu:', error);
        notificationList.innerHTML = '<div class="no-notifications" style="color: var(--danger);">Bildirimler yüklenemedi.</div>';
    }
}

// Bildirim panelindeki tek bir bildirimi okundu olarak işaretleme
async function markNotificationAsReadForPanel(notificationId, userId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/notifications/${notificationId}/read`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
        });
        const data = await response.json();
        if (response.ok) {
            showToast(data.message || 'Bildirim okundu olarak işaretlendi.');
            fetchNotificationsForPanel(userId); // Paneli yenile
            fetchUnreadNotificationsCount(userId); // Zil sayacını güncelle
        } else {
            showToast(data.message || 'Bildirim okundu olarak işaretlenemedi.', true);
        }
    } catch (error) {
        console.error('Bildirim okundu olarak işaretlenirken hata:', error);
        showToast('Bildirim okundu olarak işaretlenirken bir hata oluştu.', true);
    }
}

// Bildirim panelindeki tüm bildirimleri okundu olarak işaretleme
async function markAllNotificationsAsReadForPanel(userId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/notifications/mark_all_read`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
        });
        const data = await response.json();
        if (response.ok) {
            showToast(data.message || 'Tüm bildirimler başarıyla okundu olarak işaretlendi!');
            fetchNotificationsForPanel(userId); // Paneli yenile
            fetchUnreadNotificationsCount(userId); // Zil sayacını güncelle
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

    // Eğer Chart.js grafiği varsa, temayı değiştirdiğinde yeniden çiz
    // Bu kısım, Chart.js'in bulunduğu sayfalarda elle güncellenmelidir.
    // Örneğin: if (typeof projectChartInstance !== 'undefined' && projectChartInstance) { ... }
}

// Çıkış fonksiyonu
function logout() {
    localStorage.removeItem('currentUser');
    localStorage.removeItem('user'); // Hem 'user' hem de 'currentUser' temizle
    window.location.href = 'login.html';
}

// Ortak event listener'ları ve başlatma fonksiyonu
function setupCommonListeners() {
    loadUserInfo(); // Kullanıcı bilgilerini yükle ve bildirim sayısını çek

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

    // Bildirim Paneli İşlevselliği
    const notificationButton = document.getElementById('notificationButton');
    const notificationPanel = document.getElementById('notificationPanel');
    const closeNotificationPanelBtn = document.getElementById('closeNotificationPanel');
    const markAllReadBtn = document.getElementById('markAllReadBtn');

    if (notificationButton && notificationPanel && closeNotificationPanelBtn && markAllReadBtn) {
        notificationButton.addEventListener('click', (event) => {
            event.stopPropagation(); // Olayın body'ye yayılmasını engelle
            notificationPanel.classList.toggle('show');
            if (notificationPanel.classList.contains('show')) {
                // Paneli açtığımızda bildirimleri yükle
                const user = JSON.parse(localStorage.getItem('user')) || JSON.parse(localStorage.getItem('currentUser'));
                if (user && user.id) {
                    fetchNotificationsForPanel(user.id);
                }
            }
        });

        closeNotificationPanelBtn.addEventListener('click', () => {
            notificationPanel.classList.remove('show');
        });

        // Bildirim paneli dışına tıklayınca kapat
        document.body.addEventListener('click', (event) => {
            if (notificationPanel.classList.contains('show') &&
                !notificationPanel.contains(event.target) &&
                !notificationButton.contains(event.target)) {
                notificationPanel.classList.remove('show');
            }
        });

        markAllReadBtn.addEventListener('click', async () => {
            const user = JSON.parse(localStorage.getItem('user')) || JSON.parse(localStorage.getItem('currentUser'));
            if (user && user.id) {
                await markAllNotificationsAsReadForPanel(user.id);
            }
        });
    }
}

// Global scope'a taşı
window.API_BASE_URL = API_BASE_URL;
window.showToast = showToast;
window.showConfirmModal = showConfirmModal;
window.formatTimeAgo = formatTimeAgo;
window.fetchUnreadNotificationsCount = fetchUnreadNotificationsCount; // Diğer sayfalardan çağrılabilir olması için
window.currentUser = currentUser; // Başlangıçta null, loadUserInfo ile güncellenecek

// DOMContentLoaded'da ortak dinleyicileri başlat
document.addEventListener('DOMContentLoaded', setupCommonListeners);

// CSS'i doğrudan JavaScript'ten ekle
const commonStyles = `
    /* Bildirim Paneli Stilleri */
    .notification-panel {
        position: fixed;
        top: 60px;
        right: 20px;
        width: 350px;
        max-height: 450px;
        background-color: var(--card-bg);
        border-radius: 12px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        border: 1px solid var(--border-color);
        z-index: 1000;
        display: none;
        flex-direction: column;
        overflow: hidden;
        opacity: 0;
        transform: translateY(-10px);
        transition: opacity 0.3s ease, transform 0.3s ease;
    }

    .notification-panel.show {
        display: flex;
        opacity: 1;
        transform: translateY(0);
    }

    .notification-panel-header {
        padding: 15px 20px;
        border-bottom: 1px solid var(--border-color);
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-weight: 600;
        color: var(--text-color);
    }

    .notification-panel-header .close-btn {
        background: none;
        border: none;
        font-size: 20px;
        color: var(--light-gray);
        cursor: pointer;
        transition: color 0.2s;
    }

    .notification-panel-header .close-btn:hover {
        color: var(--primary);
    }

    .notification-list {
        flex-grow: 1;
        overflow-y: auto;
        padding: 10px 0;
    }

    .notification-item {
        display: flex;
        align-items: flex-start;
        padding: 12px 20px;
        border-bottom: 1px solid var(--border-color);
        cursor: pointer;
        transition: background-color 0.2s;
    }

    .notification-item:last-child {
        border-bottom: none;
    }

    .notification-item:hover {
        background-color: rgba(9, 128, 211, 0.05);
    }

    /* Okunmamış bildirimler için arkaplan rengi ve sol kenarlık */
    .notification-item.unread {
        background-color: var(--primary-light-bg);
        border-left: 4px solid var(--primary);
    }
    .notification-item.unread:hover {
        background-color: rgba(9, 128, 211, 0.2);
    }

    .notification-item-icon {
        width: 35px;
        height: 35px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: rgba(9, 128, 211, 0.1);
        color: var(--primary-light);
        font-size: 16px;
        margin-right: 12px;
        flex-shrink: 0;
    }
    /* Okunmamış bildirim ikonunun arka planı ve rengi */
    .notification-item.unread .notification-item-icon {
        background-color: var(--primary-light);
        color: var(--white);
    }

    .notification-item-content {
        flex-grow: 1;
    }

    .notification-item-title {
        font-weight: 600;
        font-size: 15px;
        margin-bottom: 4px;
        color: var(--text-color);
    }

    .notification-item-description {
        font-size: 13px;
        color: var(--light-gray);
        line-height: 1.4;
    }

    .notification-item-time {
        font-size: 11px;
        color: var(--light-gray);
        margin-top: 5px;
        text-align: right;
    }

    .notification-panel-footer {
        padding: 10px 20px;
        border-top: 1px solid var(--border-color);
        text-align: center;
        font-size: 14px;
        color: var(--light-gray);
        display: flex;
        justify-content: center;
        align-items: center;
    }
    /* "Tümünü Okundu Olarak İşaretle" butonu için minimalist stil */
    .notification-panel-footer button {
        width: auto;
        padding: 5px 10px;
        border-radius: 8px;
        border: 1px solid var(--primary-light);
        background: transparent;
        color: var(--primary-light);
        font-weight: 500;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 5px;
        transition: all 0.2s;
    }
    .notification-panel-footer button:hover {
        background-color: rgba(9, 128, 211, 0.1);
        color: var(--primary);
        transform: none;
        box-shadow: none;
    }

    /* Boş bildirim durumu */
    .no-notifications {
        text-align: center;
        padding: 20px;
        color: var(--light-gray);
        font-size: 14px;
    }

    /* Mobil uyumluluk için bildirim paneli */
    @media (max-width: 576px) {
        .notification-panel {
            width: calc(100% - 40px);
            right: 20px;
            left: 20px;
            top: 70px;
        }
    }

    /* Notification button badge styles (from index.html) */
    .notification-btn::after {
        content: attr(data-count);
        position: absolute;
        top: 5px;
        right: 5px;
        background-color: #ff4757;
        color: white;
        font-size: 10px;
        width: 16px;
        height: 16px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0;
        transform: scale(0);
        transition: all 0.2s ease-out;
    }
    .notification-btn.has-notifications::after {
        opacity: 1;
        transform: scale(1);
    }

    /* Toast bildirimi styles (from index.html) */
    .toast {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: var(--success);
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        display: flex;
        align-items: center;
        gap: 10px;
        z-index: 10000;
        opacity: 0;
        transform: translateY(20px);
        transition: all 0.3s ease;
    }
    
    .toast.show {
        opacity: 1;
        transform: translateY(0);
    }
    
    .toast.error {
        background-color: var(--danger);
    }
`;

const styleElement = document.createElement('style');
styleElement.textContent = commonStyles;
document.head.appendChild(styleElement);
