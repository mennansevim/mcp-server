# Performance Rules
## Goroutine ve Channel Performansı

### Goroutine Oluşturma
✅ **Goroutine'leri dikkatli kullanın**
```go
// İyi: Goroutine'ler için uygun kullanım
go func() {
    // İşlem
}()

// Kötü: Fazla goroutine oluşturma
for i := 0; i < 10000; i++ {
    go func() {
        // İşlem
    }()
}
```

### Channel Kullanımı
✅ **Channel'leri doğru kullanın**
```go
// İyi: Channel'ler için uygun kullanım
ch := make(chan int)
go func() {
    // İşlem
    ch <- 1
}()
<-ch

// Kötü: Channel'leri bloke etme
ch := make(chan int)
ch <- 1
```

## Veritabanı Performansı

### Veritabanı Sorguları
✅ **Veritabanı sorgularını optimize edin**
```go
// İyi: Veritabanı sorgularını optimize etme
db.Query("SELECT * FROM users WHERE id = $1", 1)

// Kötü: Veritabanı sorgularını optimize etmeme
db.Query("SELECT * FROM users")
```

### İndeksleme
⚠️ **İndekslemeyi unutmayın**
```go
// İyi: İndeksleme
type User struct {
    ID   int `gorm:"primary_key"`
    Name string
}

// Kötü: İndekslemeyi unutma
type User struct {
    ID   int
    Name string
}
```

## Bellek Verimliliği

### Büyük Veri Yapıları
❌ **Büyük veri yapılarını bellekte tutmayın**
```go
// Kötü: Büyük veri yapılarını bellekte tutma
users := make([]User, 1000000)

// İyi: Büyük veri yapılarını diskte tutma
users := make([]User, 0, 1000000)
```

### Bellek Sızıntıları
⚠️ **Bellek sızıntılarına dikkat edin**
```go
// Kötü: Bellek sızıntısı
func main() {
    ch := make(chan int)
    go func() {
        for {
            ch <- 1
        }
    }()
    select {}
}

// İyi: Bellek sızıntısı önleme
func main() {
    ch := make(chan int)
    go func() {
        for {
            select {
            case ch <- 1:
            }
        }
    }()
    select {}
}
```

## Checklist

- [ ] Goroutine'ler dikkatli kullanılıyor mu?
- [ ] Channel'ler doğru kullanılıyor mu?
- [ ] Veritabanı sorguları optimize ediliyor mu?
- [ ] İndeksleme yapılıyor mu?
- [ ] Büyük veri yapıları bellekte tutulmuyor mu?
- [ ] Bellek sızıntılarına dikkat ediliyor mu?

## Severity Guidelines

| Issue | Severity |
|-------|----------|
| Fazla goroutine oluşturma | **HIGH** |
| Channel'leri bloke etme | **HIGH** |
| Veritabanı sorgularını optimize etmeme | **MEDIUM** |
| İndekslemeyi unutma | **MEDIUM** |
| Büyük veri yapılarını bellekte tutma | **MEDIUM** |
| Bellek sızıntılarına dikkat etmeme | **LOW** |