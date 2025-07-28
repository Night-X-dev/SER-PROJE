// bildirim.js

// API Base URL'i: Eğer ana script'te (index.html) tanımlı değilse, burada tanımlanır.
// Bu, bildirim.js'in bağımsız çalışabilmesini sağlar.
// 'var' kullanarak veya global window objesine atayarak çakışmayı önleyebiliriz.
// En güvenli yol, global kapsamda zaten tanımlı olup olmadığını kontrol etmektir.
if (typeof API_BASE_URL === 'undefined') {
    var API_BASE_URL = "https://ser-proje.onrender.com"; 
}

document.addEventListener('DOMContentLoaded', function() {
    // Bildirim panelini placeholder bir div'e yükle
    // fetch yolu, bildirim.html'in static klasöründe olduğunu varsayar.
    fetch('static/bildirim.html') // Düzeltme: static klasöründen yükle
        .then(response => {
            if (!response.ok) {
                throw new Error(`bildirim.html yüklenirken HTTP hatası! Durum: ${response.status}`);
            }
            return response.text();
        })
        .then(data => {
            const placeholder = document.getElementById('notification-panel-placeholder');
            if (placeholder) {
                placeholder.innerHTML = data;
                // HTML yüklendikten sonra event listener'ları ve diğer fonksiyonları etkinleştir
                initializeNotificationPanel();
                fetchUnreadNotificationCount();
            } else {
                console.error('HATA: "notification-panel-placeholder" elementi bulunamadı.');
            }
        })
        .catch(error => console.error('Bildirim paneli yüklenirken hata oluştu:', error));
});


function initializeNotificationPanel() {
    const notificationButton = document.getElementById('notificationButton');
    const notificationPanel = document.getElementById('notificationPanel');
    const closeNotificationPanel = document.getElementById('closeNotificationPanel');
    const markAllReadBtn = document.getElementById('markAllReadBtn');
    const deleteAllNotificationsBtn = document.getElementById('deleteAllNotificationsBtn');

    // Elementlerin gerçekten var olup olmadığını kontrol edin
    if (!notificationButton) {
        console.error("HATA: 'notificationButton' elementi bulunamadı. Bildirim butonu çalışmayacak.");
        return; // Fonksiyonu burada sonlandır
    }
    if (!notificationPanel || !closeNotificationPanel || !markAllReadBtn || !deleteAllNotificationsBtn) {
        console.error("HATA: Bildirim paneli bileşenlerinden bazıları (panel, kapatma, okundu, silme butonları) eksik. ID'leri kontrol edin.");
        // Bu durumda yine de notificationButton'a tıklama olayını ekleyebiliriz,
        // ancak panelin kendisi düzgün çalışmayabilir.
    }

    notificationButton.addEventListener('click', (event) => {
        event.stopPropagation(); // Olayın body'ye yayılmasını engelle
        if (notificationPanel) { // Panel elementinin var olduğunu kontrol et
            notificationPanel.classList.toggle('show');
            if (notificationPanel.classList.contains('show')) {
                fetchNotifications();
            }
        }
    });

    if (closeNotificationPanel) {
        closeNotificationPanel.addEventListener('click', () => {
            if (notificationPanel) {
                notificationPanel.classList.remove('show');
            }
        });
    }

    // Panel dışına tıklayınca kapatma
    document.addEventListener('click', (event) => {
        if (notificationPanel && notificationButton && notificationPanel.classList.contains('show') &&
            !notificationPanel.contains(event.target) &&
            !notificationButton.contains(event.target)) {
            notificationPanel.classList.remove('show');
        }
    });

    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', markAllNotificationsAsRead);
    }
    
    if (deleteAllNotificationsBtn) {
        deleteAllNotificationsBtn.addEventListener('click', () => {
            // Silme işlemi için onay al (showConfirmModal'ın global olarak tanımlı olduğunu varsayar)
            if (typeof showConfirmModal === 'function') {
                showConfirmModal('Tüm Bildirimleri Sil', 'Tüm bildirimleri kalıcı olarak silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.', () => {
                    deleteAllNotifications();
                });
            } else {
                console.warn("showConfirmModal fonksiyonu bulunamadı. Onay almadan silme işlemi yapılacak.");
                deleteAllNotifications();
            }
        });
    }
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

        updateNotificationCount(unreadCount); // Merkezi fonksiyonu kullan
    } catch (error) {
        console.error('Okunmamış bildirim sayısı çekilemedi:', error);
        // Hata durumunda bile sayacı bir uyarı ile göster
        notificationButton.setAttribute('data-count', '!');
        notificationButton.classList.add('has-notifications');
        // showToast(`Okunmamış bildirim sayısı yüklenirken hata oluştu: ${error.message}`, true); // Eğer toast göstermek isterseniz
    }
}

// Bildirimleri çekme ve panele render etme
async function fetchNotifications() {
    const notificationListDiv = document.getElementById('notificationList');
    if (!notificationListDiv) {
        console.error("HATA: 'notificationList' elementi bulunamadı.");
        return;
    }
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
        if (typeof showToast === 'function') {
            showToast(`Bildirimler yüklenirken hata oluştu: ${error.message}`, true);
        }
    }
}

// Bildirimleri panele render etme
function renderNotifications(notifications) {
    const notificationListDiv = document.getElementById('notificationList');
    if (!notificationListDiv) return;

    notificationListDiv.innerHTML = '';

    if (notifications.length === 0) {
        notificationListDiv.innerHTML = '<div class="no-notifications">Henüz yeni bildiriminiz yok.</div>';
        updateNotificationCount(0); // Hiç bildirim yoksa sayacı sıfırla
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

    updateNotificationCount(unreadCount); // Render sonrası sayacı güncelle
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
    if (!itemElement || !itemElement.classList.contains('unread')) return;

    try {
        const response = await fetch(`${API_BASE_URL}/api/notifications/${notificationId}/read`, {
            method: 'PUT'
        });
        if (response.ok) {
            itemElement.classList.remove('unread');
            const notificationButton = document.getElementById('notificationButton');
            let currentCount = parseInt(notificationButton.getAttribute('data-count') || '0');
            updateNotificationCount(currentCount - 1);
            if (typeof showToast === 'function') {
                showToast('Bildirim okundu olarak işaretlendi.');
            }
        } else {
            const errorData = await response.json();
            throw new Error(errorData.message || 'İşlem Başarısız');
        }
    } catch (error) {
        if (typeof showToast === 'function') {
            showToast(`Hata: ${error.message}`, true);
        }
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
            if (typeof showToast === 'function') {
                showToast(result.message || 'Tüm bildirimler okundu.');
            }
            document.querySelectorAll('.notification-item.unread').forEach(item => {
                item.classList.remove('unread');
            });
            updateNotificationCount(0);
        } else {
            throw new Error(result.message || 'İşlem başarısız');
        }
    } catch (error) {
        if (typeof showToast === 'function') {
            showToast(`Hata: ${error.message}`, true);
        }
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
            if (typeof showToast === 'function') {
                showToast(result.message || 'Bildirim silindi.');
            }
            // Eğer bildirim okunmamışsa sayacı güncelle
            if (itemElement.classList.contains('unread')) {
                const notificationButton = document.getElementById('notificationButton');
                let currentCount = parseInt(notificationButton.getAttribute('data-count') || '0');
                updateNotificationCount(currentCount - 1);
            }
            itemElement.remove(); // Elementi DOM'dan kaldır
            // Eğer hiç bildirim kalmadıysa "yok" mesajı göster
            const notificationListDiv = document.getElementById('notificationList');
            if (notificationListDiv && notificationListDiv.children.length === 0) {
                 notificationListDiv.innerHTML = '<div class="no-notifications">Henüz yeni bildiriminiz yok.</div>';
            }
        } else {
            throw new Error(result.message || 'Silme işlemi başarısız');
        }
    } catch (error) {
        if (typeof showToast === 'function') {
            showToast(`Hata: ${error.message}`, true);
        }
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
            if (typeof showToast === 'function') {
                showToast(result.message || 'Tüm bildirimler silindi.');
            }
            const notificationListDiv = document.getElementById('notificationList');
            if (notificationListDiv) {
                notificationListDiv.innerHTML = '<div class="no-notifications">Henüz yeni bildiriminiz yok.</div>';
            }
            updateNotificationCount(0);
            const notificationPanel = document.getElementById('notificationPanel');
            if (notificationPanel) {
                notificationPanel.classList.remove('show');
            }
        } else {
            throw new Error(result.message || 'Silme işlemi başarısız');
        }
    } catch (error) {
        if (typeof showToast === 'function') {
            showToast(`Hata: ${error.message}`, true);
        }
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

// bildirim.js

// API Base URL'i: index.html dosyasında zaten tanımlanmış olduğu varsayılıyor.
// Bu dosya içinde tekrar tanımlanmasına gerek yoktur.
// Eğer index.html'de tanımlı değilse, bu script hata verecektir.

document.addEventListener('DOMContentLoaded', function() {
    // Bildirim panelini placeholder bir div'e yükle
    // fetch yolu, bildirim.html'in static klasöründe olduğunu varsayar.
    fetch('static/bildirim.html') // Düzeltme: static klasöründen yükle
        .then(response => {
            if (!response.ok) {
                throw new Error(`bildirim.html yüklenirken HTTP hatası! Durum: ${response.status}`);
            }
            return response.text();
        })
        .then(data => {
            const placeholder = document.getElementById('notification-panel-placeholder');
            if (placeholder) {
                placeholder.innerHTML = data;
                // HTML yüklendikten sonra event listener'ları ve diğer fonksiyonları etkinleştir
                initializeNotificationPanel();
                fetchUnreadNotificationCount();
            } else {
                console.error('HATA: "notification-panel-placeholder" elementi bulunamadı.');
            }
        })
        .catch(error => console.error('Bildirim paneli yüklenirken hata oluştu:', error));
});


function initializeNotificationPanel() {
    const notificationButton = document.getElementById('notificationButton');
    const notificationPanel = document.getElementById('notificationPanel');
    const closeNotificationPanel = document.getElementById('closeNotificationPanel');
    const markAllReadBtn = document.getElementById('markAllReadBtn');
    const deleteAllNotificationsBtn = document.getElementById('deleteAllNotificationsBtn');

    // Elementlerin gerçekten var olup olmadığını kontrol edin
    if (!notificationButton) {
        console.error("HATA: 'notificationButton' elementi bulunamadı. Bildirim butonu çalışmayacak.");
        return; // Fonksiyonu burada sonlandır
    }
    if (!notificationPanel || !closeNotificationPanel || !markAllReadBtn || !deleteAllNotificationsBtn) {
        console.error("HATA: Bildirim paneli bileşenlerinden bazıları (panel, kapatma, okundu, silme butonları) eksik. ID'leri kontrol edin.");
        // Bu durumda yine de notificationButton'a tıklama olayını ekleyebiliriz,
        // ancak panelin kendisi düzgün çalışmayabilir.
    }

    notificationButton.addEventListener('click', (event) => {
        event.stopPropagation(); // Olayın body'ye yayılmasını engelle
        if (notificationPanel) { // Panel elementinin var olduğunu kontrol et
            notificationPanel.classList.toggle('show');
            if (notificationPanel.classList.contains('show')) {
                fetchNotifications();
            }
        }
    });

    if (closeNotificationPanel) {
        closeNotificationPanel.addEventListener('click', () => {
            if (notificationPanel) {
                notificationPanel.classList.remove('show');
            }
        });
    }

    // Panel dışına tıklayınca kapatma
    document.addEventListener('click', (event) => {
        if (notificationPanel && notificationButton && notificationPanel.classList.contains('show') &&
            !notificationPanel.contains(event.target) &&
            !notificationButton.contains(event.target)) {
            notificationPanel.classList.remove('show');
        }
    });

    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', markAllNotificationsAsRead);
    }
    
    if (deleteAllNotificationsBtn) {
        deleteAllNotificationsBtn.addEventListener('click', () => {
            // Silme işlemi için onay al (showConfirmModal'ın global olarak tanımlı olduğunu varsayar)
            if (typeof showConfirmModal === 'function') {
                showConfirmModal('Tüm Bildirimleri Sil', 'Tüm bildirimleri kalıcı olarak silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.', () => {
                    deleteAllNotifications();
                });
            } else {
                console.warn("showConfirmModal fonksiyonu bulunamadı. Onay almadan silme işlemi yapılacak.");
                deleteAllNotifications();
            }
        });
    }
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

        updateNotificationCount(unreadCount); // Merkezi fonksiyonu kullan
    } catch (error) {
        console.error('Okunmamış bildirim sayısı çekilemedi:', error);
        // Hata durumunda bile sayacı bir uyarı ile göster
        notificationButton.setAttribute('data-count', '!');
        notificationButton.classList.add('has-notifications');
        // showToast(`Okunmamış bildirim sayısı yüklenirken hata oluştu: ${error.message}`, true); // Eğer toast göstermek isterseniz
    }
}

// Bildirimleri çekme ve panele render etme
async function fetchNotifications() {
    const notificationListDiv = document.getElementById('notificationList');
    if (!notificationListDiv) {
        console.error("HATA: 'notificationList' elementi bulunamadı.");
        return;
    }
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
        if (typeof showToast === 'function') {
            showToast(`Bildirimler yüklenirken hata oluştu: ${error.message}`, true);
        }
    }
}

// Bildirimleri panele render etme
function renderNotifications(notifications) {
    const notificationListDiv = document.getElementById('notificationList');
    if (!notificationListDiv) return;

    notificationListDiv.innerHTML = '';

    if (notifications.length === 0) {
        notificationListDiv.innerHTML = '<div class="no-notifications">Henüz yeni bildiriminiz yok.</div>';
        updateNotificationCount(0); // Hiç bildirim yoksa sayacı sıfırla
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

    updateNotificationCount(unreadCount); // Render sonrası sayacı güncelle
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
    if (!itemElement || !itemElement.classList.contains('unread')) return;

    try {
        const response = await fetch(`${API_BASE_URL}/api/notifications/${notificationId}/read`, {
            method: 'PUT'
        });
        if (response.ok) {
            itemElement.classList.remove('unread');
            const notificationButton = document.getElementById('notificationButton');
            let currentCount = parseInt(notificationButton.getAttribute('data-count') || '0');
            updateNotificationCount(currentCount - 1);
            if (typeof showToast === 'function') {
                showToast('Bildirim okundu olarak işaretlendi.');
            }
        } else {
            const errorData = await response.json();
            throw new Error(errorData.message || 'İşlem Başarısız');
        }
    } catch (error) {
        if (typeof showToast === 'function') {
            showToast(`Hata: ${error.message}`, true);
        }
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
            if (typeof showToast === 'function') {
                showToast(result.message || 'Tüm bildirimler okundu.');
            }
            document.querySelectorAll('.notification-item.unread').forEach(item => {
                item.classList.remove('unread');
            });
            updateNotificationCount(0);
        } else {
            throw new Error(result.message || 'İşlem başarısız');
        }
    } catch (error) {
        if (typeof showToast === 'function') {
            showToast(`Hata: ${error.message}`, true);
        }
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
            if (typeof showToast === 'function') {
                showToast(result.message || 'Bildirim silindi.');
            }
            // Eğer bildirim okunmamışsa sayacı güncelle
            if (itemElement.classList.contains('unread')) {
                const notificationButton = document.getElementById('notificationButton');
                let currentCount = parseInt(notificationButton.getAttribute('data-count') || '0');
                updateNotificationCount(currentCount - 1);
            }
            itemElement.remove(); // Elementi DOM'dan kaldır
            // Eğer hiç bildirim kalmadıysa "yok" mesajı göster
            const notificationListDiv = document.getElementById('notificationList');
            if (notificationListDiv && notificationListDiv.children.length === 0) {
                 notificationListDiv.innerHTML = '<div class="no-notifications">Henüz yeni bildiriminiz yok.</div>';
            }
        } else {
            throw new Error(result.message || 'Silme işlemi başarısız');
        }
    } catch (error) {
        if (typeof showToast === 'function') {
            showToast(`Hata: ${error.message}`, true);
        }
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
            if (typeof showToast === 'function') {
                showToast(result.message || 'Tüm bildirimler silindi.');
            }
            const notificationListDiv = document.getElementById('notificationList');
            if (notificationListDiv) {
                notificationListDiv.innerHTML = '<div class="no-notifications">Henüz yeni bildiriminiz yok.</div>';
            }
            updateNotificationCount(0);
            const notificationPanel = document.getElementById('notificationPanel');
            if (notificationPanel) {
                notificationPanel.classList.remove('show');
            }
        } else {
            throw new Error(result.message || 'Silme işlemi başarısız');
        }
    } catch (error) {
        if (typeof showToast === 'function') {
            showToast(`Hata: ${error.message}`, true);
        }
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
