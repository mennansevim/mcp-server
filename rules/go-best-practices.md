# Best Practices Rules
## Code Quality

### Naming Conventions
✅ **Follow language conventions**
- Paketler: `küçük_harf`
- Dosyalar: `küçük_harf`
- Struct ve class isimleri: `PascalCase`
- Fonksiyon ve method isimleri: `küçük_harf`
- Değişken isimleri: `küçük_harf`
- Sabitler: `BÜYÜK_HARF`

```go
// İyi
type Kullanıcı struct {
    adı string
}

func kullanıcıOluştur(adı string) {
    // ...
}
```

### Method Length
⚠️ **Methods should be focused and concise**
```go
// Kötü: 200+ satırlık method
func kullanıcıOluştur(adı string) {
    // ...
}

// İyi: Küçük ve odaklı methodlar
func kullanıcıOluştur(adı string) {
    validateKullanıcıVerileri(adı)
    kullanıcı := mapToKullanıcı(adı)
    saveKullanıcı(kullanıcı)
    sendHoşgeldinEmail(kullanıcı)
    return kullanıcı
}
```

### Single Responsibility Principle
✅ **Her sınıf/methodun bir sorumluluğu olmalıdır**
```go
// Kötü: KullanıcıServisi her şeyi yapıyor
type KullanıcıServisi struct {
    // ...
}

func (s *KullanıcıServisi) oluşturKullanıcı() {
    // ...
}

func (s *KullanıcıServisi) gönderEmail() {
    // ...
}

func (s *KullanıcıServisi) validateAdres() {
    // ...
}

// İyi: Sorumlulukları ayır
type KullanıcıServisi struct {
    // ...
}

func (s *KullanıcıServisi) oluşturKullanıcı() {
    // ...
}

type EmailServisi struct {
    // ...
}

func (s *EmailServisi) gönderEmail() {
    // ...
}

type AdresValidator struct {
    // ...
}

func (s *AdresValidator) validateAdres() {
    // ...
}
```

## SOLID Principles

### Dependency Inversion
✅ **Bağımlılıkları soyutlamalara bağlı kılın**
```go
// Kötü: Somut sınıfına bağlı
type SiparişServisi struct {
    repo *SqlSiparişRepo
}

func NewSiparişServisi() *SiparişServisi {
    return &SiparişServisi{repo: &SqlSiparişRepo{}}
}

// İyi: Arayüze bağlı
type SiparişServisi struct {
    repo SiparişRepo
}

func NewSiparişServisi(repo SiparişRepo) *SiparişServisi {
    return &SiparişServisi{repo: repo}
}
```

### Interface Segregation
✅ **Arayüzleri istemciye özgü kılın**
```go
// Kötü: Kalın arayüz
type KullanıcıServisiArayüzü interface {
    oluşturKullanıcı() error
    güncelleKullanıcı() error
    silKullanıcı() error
    gönderEmail() error
    validateKullanıcı() error
}

// İyi: Arayüzleri ayır
type KullanıcıYöneticisi interface {
    oluşturKullanıcı() error
    güncelleKullanıcı() error
    silKullanıcı() error
}

type KullanıcıBildiricisi interface {
    gönderEmail() error
}
```

## Error Handling

### Meaningful Error Messages
✅ **Hatalarda bağlam sağlayın**
```go
// Kötü
return errors.New("hata")

// İyi
return fmt.Errorf("kullanıcı %d için sipariş işlemini gerçekleştiremedim. Durum: %s, Sevk Tarihi: %s", siparişID, siparişDurumu, sevkTarihi)
```

### Don't Swallow Exceptions
❌ **İstisnaları yutmayın**
```go
// Kötü
defer func() {
    if r := recover(); r != nil {
        // ...
    }
}()

// İyi
if err != nil {
    log.Errorf("kullanıcı verilerini işlerken hata oluştu: %v", err)
    return err
}
```

## Documentation

### XML Comments
✅ **Herkese açık API'leri belgeleyin**
```go
// Kullanıcıyı benzersiz tanımlayıcı ile getirir.
// 
// Args:
//     kullanıcıID (int): Kullanıcı benzersiz tanımlayıcı
// 
// Returns:
//     Kullanıcı: Kullanıcı nesnesi
func GetKullanıcı(kullanıcıID int) (*Kullanıcı, error) {
    // ...
}
```

### README Files
✅ **Her proje için bir README dosyası oluşturun**
- Projenin amacı
- Derleme ve çalıştırma
- Yapılandırma gereksinimleri
- API belge bağlantıları

## Testing

### Unit Test Coverage
✅ **İş mantığının kapsamı yüksek olmalıdır**
```go
func TestKullanıcıOluştur_WithValidData_OluştururKullanıcı(t *testing.T) {
    // ...
}

func TestKullanıcıOluştur_WithInvalidData_DöndürürHata(t *testing.T) {
    // ...
}
```

### Test Naming
✅ **Test isimleri açıklamalı olmalıdır**
```go
// İyi
func TestGetKullanıcı_WhenKullanıcıDoesNotExist_ReturnsNotFound(t *testing.T) {
    // ...
}

// Kötü
func Test1(t *testing.T) {
    // ...
}
```

## Configuration

### Magic Numbers
❌ **Sihirli sayıları kullanmayın**
```go
// Kötü
if kullanıcıDurumu == 2 {
    // ...
}

// İyi
const (
    KullanıcıDurumuAktif = 1
    KullanıcıDurumuPasif = 2
)

if kullanıcıDurumu == KullanıcıDurumuPasif {
    // ...
}
```

### Configuration Files
✅ **Yapılandırma dosyalarını kullanın**
```go
// Kötü
const maxDeneme = 3
const zamanAşımı = 30

// İyi
config, err := config.LoadFile("config.yaml")
if err != nil {
    // ...
}

maxDeneme := config.GetInt("deneme.max")
zamanAşımı := config.GetInt("zaman.aşımı")
```

## Code Organization

### File Structure
✅ **Özelliklere göre düzenleyin**
```go
// Kötü
/controllers
    /kullanıcı
        kullanıcı_controller.go
    /sipariş
        sipariş_controller.go
/services
    /kullanıcı
        kullanıcı_service.go
    /sipariş
        sipariş_service.go
/models
    /kullanıcı
        kullanıcı.go
    /sipariş
        sipariş.go

// İyi
/özellikler
    /kullanıcı
        kullanıcı_controller.go
        kullanıcı_service.go
        kullanıcı.go
        kullanıcı_dto.go
    /sipariş
        sipariş_controller.go
        sipariş_service.go
        sipariş.go
        sipariş_dto.go
```

### Namespace Organization
✅ **Klasör yapısına uyun**
```go
// Dosya: özellikler/kullanıcı/kullanıcı_service.go
package özellikler

import (
    // ...
)

type KullanıcıServisi struct {
    // ...
}
```

## Security Best Practices

### Input Validation
✅ **Giriş verilerini her zaman doğrulayın**
```go
func GetKullanıcı(kullanıcıID int) (*Kullanıcı, error) {
    if kullanıcıID <= 0 {
        return nil, errors.New("geçersiz kullanıcı ID")
    }
    // ...
}
```

### Principle of Least Privilege
✅ **Gerekli izinleri verin**
```go
// Veritabanı bağlantısı
// Salt-okunur bağlantıyı kullan
readOnlyConnection := config.GetString("veritabanı.salt-okunur")
```

## Performance Best Practices

### Lazy Loading vs Eager Loading
✅ **Uygun yükleme stratejilerini seçin**
```go
// Aceleci yükleme
var kullanıcılar []Kullanıcı
db.Preload("Siparişler").Find(&kullanıcılar)

// Gerektiğinde yükleme
var kullanıcı Kullanıcı
db.First(&kullanıcı)
if needSiparişler {
    db.Model(&kullanıcı).Association("Siparişler").Find(&kullanıcı.Siparişler)
}
```

## Logging

### Structured Logging
✅ **Yapılandırılmış günlüğü kullanın**
```go
log.Infof("kullanıcı %d için sipariş %d oluşturuldu. Tutar: %v", kullanıcıID, siparişID, tutar)
```

### Log Levels
✅ **Uygun günlükleme seviyelerini kullanın**
- **İzleme**: Çok ayrıntılı (nadiren kullanılır)
- **Hata Ayıklama**: Tanısal bilgiler
- **Bilgi**: Genel akış
- **Uyarı**: Beklenmedik ancak ele alınan
- **Hata**: Yakalanan hata
- **Kritik**: Uygulama çökmesi

## API Design

### RESTful Conventions
✅ **REST ilkelerine uyun**
```go
// İyi
GET    /api/kullanıcılar          // Kullanıcı listesi
GET    /api/kullanıcılar/{id}     // Kullanıcı getir
POST   /api/kullanıcılar          // Kullanıcı oluştur
PUT    /api/kullanıcılar/{id}     // Kullanıcı güncelle
DELETE /api/kullanıcılar/{id}     // Kullanıcı sil

// Kötü
POST /api/GetKullanıcı
POST /api/CreateKullanıcı
POST /api/UpdateKullanıcı
```

### Versioning
✅ **API'lerinizi sürümleyin**
```go
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
    // v2 uygulaması
}
```

## Checklist

- [ ] Adlandırma kuralları takip edildi
- [ ] Methodlar küçük ve odaklı
- [ ] Tek sorumluluk ilkesi uygulandı
- [ ] ...