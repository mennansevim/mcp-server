# Performance Rules
## Shell Performance

### Komut Zincirleme
❌ **CRITICAL PERFORMANCE ISSUE**
```bash
# Bad: Zincirleme komutlar
komut1 && komut2 && komut3

# Good: Paralel komutlar
komut1 & komut2 & komut3
```

### Girdi/Çıktı İşlemleri
✅ **Girdi/çıktı işlemlerini optimize edin**
```bash
# Bad: Büyük dosyaları yükleyin
cat büyük_dosya.txt

# Good: Büyük dosyaları parça parça işleyin
split -l 1000 büyük_dosya.txt
```

### Döngüler
⚠️ **Döngülerin performansını düşünün**
```bash
# Bad: Büyük döngüler
for i in {1..1000000}; do
    işlemler
done

# Good: Büyük döngüleri parça parça işleyin
for i in {1..1000}; do
    işlemler
done
```

### Bellek Kullanımı
❌ **Bellek kullanımını optimize edin**
```bash
# Bad: Büyük veri yapıları
büyük_veri=(1 2 3 ... 1000000)

# Good: Büyük veri yapılarını parça parça işleyin
büyük_veri=()
for i in {1..1000}; do
    büyük_veri+=($i)
done
```

### Paralel İşlemler
✅ **Paralel işlemleri kullanın**
```bash
# Bad: Sıralı işlemler
işlem1
işlem2
işlem3

# Good: Paralel işlemler
işlem1 &
işlem2 &
işlem3 &
```

### Gereksiz İşlemler
⚠️ **Gereksiz işlemleri önleyin**
```bash
# Bad: Gereksiz işlemler
if [ -f dosya ]; then
    işlemler
fi

# Good: Gereksiz işlemleri önleyin
if [ ! -f dosya ]; then
    işlemler
fi
```

## Checklist

- [ ] Zincirleme komutlar kullanılmamalıdır
- [ ] Girdi/çıktı işlemleri optimize edilmiştir
- [ ] Döngülerin performansı düşünülmüştür
- [ ] Bellek kullanımı optimize edilmiştir
- [ ] Paralel işlemler kullanılmaktadır
- [ ] Gereksiz işlemler önlenmiştir

## Severity Guidelines

| Issue | Severity |
|-------|----------|
| Zincirleme komutlar | **HIGH** |
| Büyük girdi/çıktı işlemleri | **MEDIUM** |
| Büyük döngüler | **MEDIUM** |
| Yüksek bellek kullanımı | **MEDIUM** |
| Paralel işlemlerin kullanılmaması | **LOW** |
| Gereksiz işlemler | **LOW** |