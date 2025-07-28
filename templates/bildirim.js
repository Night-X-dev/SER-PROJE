// bildirim.js

// API Base URL'i global bir değişkenden veya konfigürasyon dosyasından almak daha iyidir.
// Şimdilik ana script'teki `API_BASE_URL` değişkenini kullanacağını varsayıyoruz.
// Eğer bu script tek başına çalışacaksa, bu değişkenin burada tanımlanması gerekir.
// const API_BASE_URL = "https://ser-proje.onrender.com"; 

document.addEventListener('DOMContentLoaded', function() {
    // Bildirim panelini placeholder bir div'e yükle
    fetch('bildirim.html')
        .then(response => response.text())
        .then(data => {
            const placeholder = document.getElementById('notification-panel-placeholder');
            if (placeholder) {
                placeholder.innerHTML = data;
            }
            // HTML yüklendikten sonra event listener'ları ve diğer fonksiyonları etkinleştir
            initializeNotificationPanel();
            fetchUnreadNotificationCount();
        })
        .catch(error => console.error('Bildirim paneli yüklenirken hata oluştu:', error));
});


function initializeNotificationPanel() {
    const notificationButton = document.getElementById('notificationButton');
    const notificationPanel = document.getElementById('notificationPanel');
    const closeNotificationPanel = document.getElementById('closeNotificationPanel');
    const markAllReadBtn = document.getElementById('markAllReadBtn');
    const deleteAllNotificationsBtn = document.getElementById('deleteAllNotificationsBtn');

    if (!notificationButton || !notificationPanel || !closeNotificationPanel || !markAllReadBtn || !deleteAllNotificationsBtn) {
        console.error("Bildirim paneli bileşenlerinden bazıları eksik. ID'leri kontrol edin.");
        return;
    }

    notificationButton.addEventListener('click', (event) => {
        event.stopPropagation();
        notificationPanel.classList.toggle('show');
        if (notificationPanel.classList.contains('show')) {
            fetchNotifications();
        }
    });

    closeNotificationPanel.addEventListener('click', () => {
        notificationPanel.classList.remove('show');
    });

    document.addEventListener('click', (event) => {
        if (notificationPanel.classList.contains('show') &&
            !notificationPanel.contains(event.target) &&
            !notificationButton.contains(event.target)) {
            notificationPanel.classList.remove('show');
        }
    });

    markAllReadBtn.addEventListener('click', markAllNotificationsAsRead);
    deleteAllNotificationsBtn.addEventListener('click', () => {
         // Silme işlemi için onay al
        showConfirmModal('Tüm Bildirimleri Sil', 'Tüm bildirimleri kalıcı olarak silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.', () => {
            deleteAllNotifications();
        });
    });
}

// Sadece okunmamış bildirim sayısını çeken fonksiyon
async function fetchUnreadNotificationCount() {
    const notificationButton = document.getElementById('notificationButton');
    if (!notificationButton) return;

    try {
        const response = await fetch(`${API_BASE_URL}/api/notifications/unread-count`);
        if (!response.ok) {
            throw new Error(`HTTP hatası! Durum: ${response.status}`);
        }
        const data = await response.json();
        const unreadCount = data.unread_count || 0;

        notificationButton.setAttribute('data-count', unreadCount);
        if (unreadCount > 0) {
            notificationButton.classList.add('has-notifications');
        } else {
            notificationButton.classList.remove('has-notifications');
        }
    } catch (error) {
        console.error('Okunmamış bildirim sayısı çekilemedi:', error);
        notificationButton.setAttribute('data-count', '!');
        notificationButton.classList.add('has-notifications');
    }
}

// Bildirimleri çekme ve panele render etme
async function fetchNotifications() {
    const notificationListDiv = document.getElementById('notificationList');
    notificationListDiv.innerHTML = '<div class="no-notifications"><i class="fas fa-spinner fa-spin"></i> Bildirimler yükleniyor...</div>';

    try {
        const response = await fetch(`${API_BASE_URL}/api/notifications`);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ message: 'Sunucudan yanıt alınamadı.' }));
            throw new Error(errorData.message || `HTTP hatası! Durum: ${response.status}`);
        }
        const notifications = await response.json();
        renderNotifications(notifications);
        fetchUnreadNotificationCount(); // Sayacı senkronize et
    } catch (error) {
        console.error('Bildirimler çekilemedi:', error);
        notificationListDiv.innerHTML = '<div class="no-notifications" style="color: var(--danger);">Bildirimler yüklenemedi.</div>';
        showToast(`Bildirimler yüklenirken hata oluştu: ${error.message}`, true);
    }
}

// Bildirimleri panele render etme
function renderNotifications(notifications) {
    const notificationListDiv = document.getElementById('notificationList');
    notificationListDiv.innerHTML = '';

    if (notifications.length === 0) {
        notificationListDiv.innerHTML = '<div class="no-notifications">Henüz yeni bildiriminiz yok.</div>';
        updateNotificationCount(0);
        return;
    }

    let unreadCount = 0;
    notifications.forEach(notification => {
        const isRead = notification.is_read === true || notification.is_read === 1;
        if (!isRead) {
            unreadCount++;
        }

        const item = document.createElement('div');
        item.className = isRead ? 'notification-item' : 'notification-item unread';
        item.setAttribute('data-id', notification.id); // Silme işlemi için ID
        item.innerHTML = `
            <div class="notification-item-icon">
                <i class="${notification.icon || 'fas fa-info-circle'}"></i>
            </div>
            <div class="notification-item-content">
                <div class="notification-item-title">${notification.title}</div>
                <div class="notification-item-description">${notification.message}</div>
                <div class="notification-item-time">${formatTimeAgo(notification.created_at)}</div>
            </div>
            <div class="notification-item-actions">
                <button class="delete-notification-btn" title="Bu bildirimi sil">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        // Tıklama olayları
        item.querySelector('.notification-item-content').addEventListener('click', () => markNotificationAsRead(notification.id, item));
        item.querySelector('.delete-notification-btn').addEventListener('click', (e) => {
            e.stopPropagation(); // Üst elementin tıklama olayını tetiklemesini engelle
            deleteNotification(notification.id, item);
        });

        notificationListDiv.appendChild(item);
    });

    updateNotificationCount(unreadCount);
}

// Bildirim sayacını ve ikon durumunu güncelleyen merkezi fonksiyon
function updateNotificationCount(count) {
    const notificationButton = document.getElementById('notificationButton');
    if (!notificationButton) return;

    const currentCount = Math.max(0, count);
    notificationButton.setAttribute('data-count', currentCount);
    if (currentCount > 0) {
        notificationButton.classList.add('has-notifications');
    } else {
        notificationButton.classList.remove('has-notifications');
    }
}

// Tek bir bildirimi okunmuş olarak işaretle
async function markNotificationAsRead(notificationId, itemElement) {
    if (!itemElement.classList.contains('unread')) return;

    try {
        const response = await fetch(`${API_BASE_URL}/api/notifications/${notificationId}/read`, {
            method: 'PUT'
        });
        if (response.ok) {
            itemElement.classList.remove('unread');
            const notificationButton = document.getElementById('notificationButton');
            let currentCount = parseInt(notificationButton.getAttribute('data-count') || '0');
            updateNotificationCount(currentCount - 1);
        } else {
            const errorData = await response.json();
            throw new Error(errorData.message || 'İşlem Başarısız');
        }
    } catch (error) {
        showToast(`Hata: ${error.message}`, true);
        console.error('Bildirim okundu olarak işaretlenirken hata:', error);
    }
}

// Tüm bildirimleri okunmuş olarak işaretle
async function markAllNotificationsAsRead() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/notifications/mark_all_read`, {
            method: 'PUT'
        });
        const result = await response.json();
        if (response.ok) {
            showToast(result.message || 'Tüm bildirimler okundu.');
            document.querySelectorAll('.notification-item.unread').forEach(item => {
                item.classList.remove('unread');
            });
            updateNotificationCount(0);
        } else {
            throw new Error(result.message || 'İşlem başarısız');
        }
    } catch (error) {
        showToast(`Hata: ${error.message}`, true);
        console.error('Tüm bildirimler okunurken hata:', error);
    }
}

// Tek bir bildirimi sil
async function deleteNotification(notificationId, itemElement) {
     try {
        const response = await fetch(`${API_BASE_URL}/api/notifications/${notificationId}`, {
            method: 'DELETE'
        });
        const result = await response.json();
        if (response.ok) {
            showToast(result.message || 'Bildirim silindi.');
            // Eğer bildirim okunmamışsa sayacı güncelle
            if (itemElement.classList.contains('unread')) {
                const notificationButton = document.getElementById('notificationButton');
                let currentCount = parseInt(notificationButton.getAttribute('data-count') || '0');
                updateNotificationCount(currentCount - 1);
            }
            itemElement.remove(); // Elementi DOM'dan kaldır
            // Eğer hiç bildirim kalmadıysa "yok" mesajı göster
            const notificationListDiv = document.getElementById('notificationList');
            if (notificationListDiv.children.length === 0) {
                 notificationListDiv.innerHTML = '<div class="no-notifications">Henüz yeni bildiriminiz yok.</div>';
            }
        } else {
            throw new Error(result.message || 'Silme işlemi başarısız');
        }
    } catch (error) {
        showToast(`Hata: ${error.message}`, true);
        console.error('Bildirim silinirken hata:', error);
    }
}

// Tüm bildirimleri sil
async function deleteAllNotifications() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/notifications`, {
            method: 'DELETE'
        });
        const result = await response.json();
        if (response.ok) {
            showToast(result.message || 'Tüm bildirimler silindi.');
            const notificationListDiv = document.getElementById('notificationList');
            notificationListDiv.innerHTML = '<div class="no-notifications">Henüz yeni bildiriminiz yok.</div>';
            updateNotificationCount(0);
            document.getElementById('notificationPanel').classList.remove('show');
        } else {
            throw new Error(result.message || 'Silme işlemi başarısız');
        }
    } catch (error) {
        showToast(`Hata: ${error.message}`, true);
        console.error('Tüm bildirimler silinirken hata:', error);
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

// Gerekli olabilecek yardımcı fonksiyonlar (showToast, showConfirmModal vb.)
// Bu fonksiyonların ana script dosyanızda (index.html içindeki) global olarak tanımlandığını varsayıyoruz.
// Eğer tanımlı değilse, buraya da eklenmeleri gerekir.