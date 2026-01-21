# Best Practices Rules
## Code Quality

### Naming Conventions
✅ **Follow language conventions**
- Sınıflar: `PascalCase`
- Fonksiyonlar, değişkenler: `snake_case`
- Sabitler: `UPPER_SNAKE_CASE`

### Method Length
⚠️ **Methods should be focused and concise**
```python
# Kötü: 200+ satırlık method her şeyi yapıyor

# İyi: Küçük, odaklanmış methodlar
def create_user(dto):
    validate_user_data(dto)
    user = map_to_user(dto)
    save_user(user)
    send_welcome_email(user)
    return user
```

### Single Responsibility Principle
✅ **Her sınıf/metod sadece bir sorumluluğa sahip olmalı**
```python
# Kötü: UserService her şeyi yapıyor
class UserService:
    def create_user(self): pass
    def send_email(self): pass      # EmailService olmalı
    def validate_address(self): pass # AddressValidator olmalı

# İyi: Ayrıntılı sorumluluklar
class UserService: 
    # Kullanıcı operasyonları
    pass
class EmailService: 
    # E-posta operasyonları
    pass
class AddressValidator: 
    # Adres doğrulama
    pass
```

## SOLID Principles

### Dependency Inversion
✅ **Soyutlamalara bağlı kalın, somut sınıflara değil**
```python
# Kötü: Somut sınıf bağımlılığı
class OrderService:
    def __init__(self):
        self.repo = SqlOrderRepository()

# İyi: Arayüze bağlılık
class OrderService:
    def __init__(self, repo: IOrderRepository):
        self.repo = repo
```

### Interface Segregation
✅ **Arayüzler istemciye özgü olmalı**
```python
# Kötü: Yağlı arayüz
from abc import ABC, abstractmethod

class IUserService(ABC):
    @abstractmethod
    def create_async(self): pass
    @abstractmethod
    def update_async(self): pass
    @abstractmethod
    def delete_async(self): pass
    @abstractmethod
    def send_email_async(self): pass    # Her istemci bunu gerektirmez
    @abstractmethod
    def validate_async(self): pass     # Veya bunu

# İyi: Ayrıntılı arayüzler
class IUserManager(ABC):
    @abstractmethod
    def create_async(self): pass
    @abstractmethod
    def update_async(self): pass
    @abstractmethod
    def delete_async(self): pass

class IUserNotifier(ABC):
    @abstractmethod
    def send_email_async(self): pass
```

## Error Handling

### Anlamlı Hata Mesajları
✅ **İstisnalar bağlam sağlayarak oluşturulmalı**
```python
# Kötü
raise Exception("Hata")

# İyi
raise ValueError(
    f"Sipariş {order_id} işlenemedi çünkü zaten gönderildi. "
    f"Durum: {order.status}, Gönderilme Tarihi: {order.shipped_date}"
)
```

### İstisnaları Yutma
❌ **Asla yakala ve görmezden gelme**
```python
# Kötü
try:
    process_data()
except:
    # Sessiz başarısızlık - hata ayıklama kabusu!
    pass

# İyi
try:
    process_data()
except Exception as e:
    logger.error(f"Kullanıcı {user_id} için veri işleme başarısız", exc_info=e)
    # İstisnayı yeniden at veya uygun şekilde işle
    raise
```

## Documentation

### Dokümantasyon
✅ **Kamuya açık API'leri belgeleyin**
```python
def get_user(user_id: int) -> User:
    """
    Bir kullanıcıyı benzersiz kimliğiyle alır.
    
    Args:
    user_id (int): Kullanıcının benzersiz kimliği.
    
    Returns:
    User: Kullanıcı bulunursa; aksi takdirde None.
    
    Raises:
    ValueError: user_id 1'den küçükse atılır.
    """
    if user_id < 1:
        raise ValueError("Kullanıcı Kimliği pozitif olmalıdır", user_id)
    
    return User.query.get(user_id)
```

### README Dosyaları
✅ **Her proje bir README dosyasına sahip olmalıdır**
- Projenin amacı
- Derleme/çalıştırma
- Yapılandırma gereksinimleri
- API belgeleri bağlantıları

## Testing

### Birim Test Kapsamı
✅ **İş mantığının yüksek kapsama hedefleyin**
```python
def test_create_user_with_valid_data():
    # Hazırlık
    dto = CreateUserDto(name="Test")
    service = UserService(mock_repo)
    
    # Eylem
    result = service.create_user(dto)
    
    # Doğrulama
    assert result is not None
    assert result.name == "Test"
    mock_repo.assert_called_once_with(result)
```

### Test İsimlendirmesi
✅ **Tanımlayıcı test isimleri kullanın**
```python
# İyi
def test_get_user_when_user_does_not_exist_returns_not_found():
    pass

# Kötü
def test1():
    pass
```

## Configuration

### Sihirli Sayılar
❌ **Sihirli sayıları veya dizeleri kaçın**
```python
# Kötü
if user.status == 2:
    if order.type == "premium"

# İyi
class UserStatus:
    AKTİF = 1
    PASİF = 2

PREMIUM_SİPARİŞ_TİPİ = "premium"

if user.status == UserStatus.PASİF:
    if order.type == PREMIUM_SİPARİŞ_TİPİ
```

### Yapılandırma Dosyaları
✅ **Yapılandırmayı, sabit değerleri kullanmayın**
```python
# Kötü
max_deneme = 3
zaman_aşımı = 30

# İyi
max_deneme = config["Retry"]["MaxAttempts"]
zaman_aşımı = config["Http"]["TimeoutSeconds"]
```

## Code Organization

### Dosya Yapısı
✅ **Özelliklere göre organize edin, tiplere göre değil**
```
# Kötü
/Controllerlar
  KullanıcıController.py
  SiparişController.py
/Hizmetler
  KullanıcıHizmeti.py
  SiparişHizmeti.py
/Modeller
  Kullanıcı.py
  Sipariş.py

# İyi
/Özellikler
  /Kullanıcılar
    KullanıcıController.py
    KullanıcıHizmeti.py
    Kullanıcı.py
    KullanıcıDto.py
  /Siparişler
    SiparişController.py
    SiparişHizmeti.py
    Sipariş.py
    SiparişDto.py
```

### Ad Alanı Organizasyonu
✅ **Klasör yapısına uyun**
```python
# Dosya: Özellikler/Kullanıcılar/KullanıcıHizmeti.py
from myapp.özellikler.kullanıcılar import KullanıcıHizmeti
```

## Güvenlik En İyi Uygulamaları

### Giriş Doğrulama
✅ **Girişleri her zaman doğrulayın**
```python
def get_user(kullanıcı_id: int) -> Kullanıcı:
    if kullanıcı_id <= 0:
        raise ValueError("Geçersiz kullanıcı kimliği", kullanıcı_id)
    
    return Kullanıcı.sorgu.get(kullanıcı_id)
```

### En Az Yetki İlkesi
✅ **Minimum gerekli izinleri verin**
```python
# Veritabanı bağlantı dizesi
# Sorgular için salt-okunur bağlantı kullanın
salt_okunur_baglantı = config["ReadOnly"]
```

## Performans En İyi Uygulamaları

### Lazy Loading vs Eager Loading
✅ **Uygunduğunu seçin**
```python
# Eager yükleme, ilgili verileri bilirseniz
kullanıcılar = Kullanıcı.query.options(joinedload(Kullanıcı.siparişler)).all()

# Koşullu açık yükleme
if need_orders:
    db.session.query(Kullanıcı).get(user_id).siparişler
```

## Logging

### Yapılandırılmış Günlüğe Kaydetme
✅ **Bağlamla yapılandırılmış günlüğe kaydetme kullanın**
```python
# İyi
logger.bilgi(
    "Kullanıcı {kullanıcı_id} sipariş {sipariş_id} için {tutar} oluşturdu",
    kullanıcı_id, sipariş_id, tutar
)

# Kötü
logger.bilgi(f"Kullanıcı {kullanıcı_id} sipariş {sipariş_id} için {tutar} oluşturdu")
```

### Günlüğe Kaydetme Düzeyleri
✅ **Uygun günlüğe kaydetme düzeylerini kullanın**
- **İzleme**: Çok ayrıntılı (nadiren kullanılır)
- **Hata Ayıklama**: Tanısal bilgiler
- **Bilgi**: Genel akış
- **Uyarı**: Beklenmedik ancak işlenen
- **Hata**: Yakalanan hata
- **Kritik**: Uygulama çökmesi

## API Tasarımı

### RESTful Kuralları
✅ **REST ilkelerine uyun**
```python
# İyi
GET    /api/kullanıcılar          # Kullanıcı listesi
GET    /api/kullanıcılar/{id}     # Kullanıcı al
POST   /api/kullanıcılar          # Kullanıcı oluştur
PUT    /api/kullanıcılar/{id}     # Kullanıcı güncelle
DELETE /api/kullanıcılar/{id}     # Kullanıcı sil

# Kötü
POST /api/GetKullanıcı
POST /api/CreateKullanıcı
POST /api/UpdateKullanıcı
```

### Sürümleme
✅ **API'lerinizi sürümleyin**
```python
[ApiController]
[Route("api/v1/[controller]")]
public class KullanıcıController : ControllerBase
{
    // v1 uygulaması
}

[ApiController]
[Route("api/v2/[controller]")]
public class KullanıcıController : ControllerBase
{
    // v2 uygulaması, kırıcı değişikliklerle
}
```

## Checklist

- [ ] Adlandırma kuralları izleniyor
- [ ] Yöntemler küçük ve odaklanmış
- [ ] Tek Sorumluluk Prensibi uygulanıyor
- [ ] ...