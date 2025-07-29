// user-avatar.js

/**
 * Kullanıcı avatarını günceller.
 * Eğer kullanıcı resmi varsa resmi gösterir, yoksa isim ve soyisimden baş harfleri oluşturur.
 * Gerekli CSS stillerini de dinamik olarak sayfaya ekler.
 * @param {object} currentUser - Mevcut kullanıcı bilgileri objesi.
 * @param {string} currentUser.fullname - Kullanıcının tam adı (örn: "John Doe").
 * @param {string} [currentUser.profilePicture] - Kullanıcının profil resmi URL'si (isteğe bağlı).
 */
function updateUserAvatar(currentUser) {
    const avatarContainer = document.getElementById('userAvatarContainer');
    let avatarImg = document.getElementById('userAvatarImg');
    let avatarInitials = document.getElementById('userAvatarInitials');

    // Avatar elementlerinin sayfada mevcut olup olmadığını kontrol et
    if (!avatarContainer) {
        console.error('Avatar kapsayıcı elementi bulunamadı. Lütfen HTML yapısını kontrol edin (ID: userAvatarContainer).');
        return;
    }

    // Eğer img veya span elementleri yoksa, onları dinamik olarak oluştur
    if (!avatarImg) {
        avatarImg = document.createElement('img');
        avatarImg.id = 'userAvatarImg';
        avatarImg.className = 'avatar-img';
        avatarImg.style.display = 'none'; // Başlangıçta gizle
        avatarContainer.appendChild(avatarImg);
    }
    if (!avatarInitials) {
        avatarInitials = document.createElement('span');
        avatarInitials.id = 'userAvatarInitials';
        avatarInitials.className = 'avatar-initials';
        avatarInitials.style.display = 'none'; // Başlangıçta gizle
        avatarContainer.appendChild(avatarInitials);
    }

    // Başlangıçta tüm avatar gösterimlerini gizle ve container içeriğini temizle
    avatarImg.style.display = 'none';
    avatarInitials.style.display = 'none';
    avatarContainer.innerHTML = ''; // İçeriği temizle

    if (currentUser && currentUser.profilePicture && currentUser.profilePicture !== 'null' && currentUser.profilePicture !== '') {
        // Eğer profil resmi URL'si varsa ve geçerliyse, resmi göster
        avatarImg.src = currentUser.profilePicture;
        avatarImg.alt = currentUser.fullname ? `${currentUser.fullname} Avatarı` : 'Kullanıcı Avatarı';
        avatarImg.style.display = 'block';
        avatarContainer.appendChild(avatarImg);
    } else if (currentUser && currentUser.fullname) {
        // Profil resmi yoksa ama tam adı varsa, baş harfleri oluştur
        const nameParts = currentUser.fullname.split(' ').filter(part => part.length > 0);
        let initials = '';
        if (nameParts.length > 0) {
            initials += nameParts[0][0]; // İlk kelimenin ilk harfi
            if (nameParts.length > 1) {
                initials += nameParts[nameParts.length - 1][0]; // Son kelimenin ilk harfi
            }
        }
        avatarInitials.textContent = initials.toUpperCase();
        avatarInitials.style.display = 'flex'; // Baş harfleri ortalamak için flex kullan
        avatarContainer.appendChild(avatarInitials);
    } else {
        // Kullanıcı bilgisi yoksa veya eksikse varsayılan bir ikon göster
        console.warn('Kullanıcı bilgisi eksik veya avatar gösterilemiyor. Varsayılan avatar gösterilecek.');
        const defaultIcon = document.createElement('i');
        defaultIcon.className = 'fas fa-user-circle'; // Font Awesome kullanıcı ikonu
        defaultIcon.style.fontSize = '2rem';
        defaultIcon.style.color = 'var(--white)';
        avatarContainer.style.backgroundColor = 'var(--light-gray)'; // Varsayılan için farklı arka plan rengi
        avatarContainer.appendChild(defaultIcon);
    }
}

/**
 * Avatar için gerekli CSS stillerini dinamik olarak sayfaya ekler.
 * Bu fonksiyon, script yüklendiğinde bir kez çalışır.
 */
function injectAvatarStyles() {
    const styleId = 'user-avatar-styles';
    if (document.getElementById(styleId)) {
        return; // Stiller zaten eklenmişse tekrar ekleme
    }

    const style = document.createElement('style');
    style.id = styleId;
    style.textContent = `
        /* Kullanıcı Avatarı Stilleri */
        .avatar-container {
            width: 40px; /* Avatarın genişliği */
            height: 40px; /* Avatarın yüksekliği */
            border-radius: 50%; /* Dairesel şekil */
            background-color: #0980d3; /* Varsayılan arka plan rengi (var(--primary-light) yerine sabit değer) */
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden; /* Taşmayı engelle */
            flex-shrink: 0; /* Flex konteynerlerde küçülmeyi engelle */
            cursor: pointer; /* Tıklanabilir olduğunu belirtmek için */
            box-shadow: 0 2px 5px rgba(0,0,0,0.2); /* Hafif gölge */
            transition: transform 0.2s ease-in-out; /* Hover efekti için geçiş */
        }

        .avatar-container:hover {
            transform: scale(1.05); /* Üzerine gelince hafif büyüme */
        }

        .avatar-img {
            width: 100%;
            height: 100%;
            object-fit: cover; /* Resmin container'ı doldurmasını sağla */
            border-radius: 50%; /* Resmin dairesel olmasını sağla */
        }

        .avatar-initials {
            color: #ffffff; /* Baş harflerin rengi (var(--white) yerine sabit değer) */
            font-size: 1.2rem; /* Baş harflerin boyutu */
            font-weight: bold;
            text-transform: uppercase; /* Baş harfleri büyük harf yap */
            user-select: none; /* Metin seçimini engelle */
        }
    `;
    document.head.appendChild(style);
}

// Sayfa tamamen yüklendiğinde CSS stillerini ekle ve avatarı güncelle
document.addEventListener('DOMContentLoaded', () => {
    injectAvatarStyles(); // Stilleri sayfaya ekle

    // `currentUser` objesinin tanımlı olup olmadığını kontrol et
    // Eğer `currentUser` objesi başka bir yerden (örn: localStorage, API) geliyorsa,
    // burada onu yüklemeniz gerekebilir.
    if (typeof currentUser !== 'undefined' && currentUser) {
        updateUserAvatar(currentUser);
    } else {
        // `currentUser` objesi yoksa veya null ise varsayılan avatarı göster
        updateUserAvatar(null);
    }
});

// Not: Kullanıcı oturum açtığında veya profil bilgisi güncellendiğinde
// `updateUserAvatar(yeniCurrentUserObjesi)` fonksiyonunu tekrar çağırarak
// avatarı dinamik olarak güncelleyebilirsiniz.
