"""
Rule dosyalarını dile göre revize eden servis.

Provider-agnostic AI routing is implemented via services/ai_providers/*.
"""
import structlog
from pathlib import Path
from typing import Optional, Dict, List
from services.ai_providers import AIProviderRouter

logger = structlog.get_logger()

# Rules directory
RULES_DIR = Path(__file__).parent.parent / "rules"

# Rule kategorileri
RULE_CATEGORIES = [
    "security",
    "performance",
    "fundamentals",
    "compilation",
    "best-practices",
    "linter"
]


class RuleGenerator:
    """Dile özel rule dosyaları oluşturur ve günceller"""
    
    RULE_GENERATION_PROMPT = """Sen bir programlama dili uzmanısın. Aşağıdaki dil için {category} kurallarını içeren detaylı bir markdown dosyası oluştur.

Dil: {language}
Kategori: {category}

Kurallar şu formatta olmalı:
- ❌ **SEVERITY:** Kötü örnekler
- ✅ İyi örnekler
- ⚠️ Dikkat edilmesi gerekenler

Her kategori için şunları içermeli:
1. Öncelik seviyesi (CRITICAL, HIGH, MEDIUM, LOW)
2. Somut kod örnekleri (Bad/Good formatında)
3. Severity guidelines tablosu
4. Checklist

{category} için özel kurallar:

{base_rules}

Şimdi bu kuralları {language} diline özel olarak revize et. Dilin syntax'ına, best practice'lerine ve yaygın hatalarına göre özelleştir.

Sadece markdown içeriğini döndür, başka açıklama ekleme."""

    def __init__(
        self,
        provider: str = "anthropic",
        model: Optional[str] = None,
        *,
        ai_config: Optional[dict] = None,
    ):
        # Backward compatible
        if ai_config is None:
            ai_config = {
                "provider": provider,
                "model": model,
                "temperature": 0.3,
                "max_tokens": 8000,
            }
        self.ai_config = ai_config
        self.router = AIProviderRouter(ai_config)
        self.last_provider_used: Optional[str] = None
        self.last_model_used: Optional[str] = None

        logger.info(
            "rule_generator_initialized",
            primary_provider=self.router.primary,
        )
    
    def _load_base_rule(self, category: str) -> str:
        """Temel rule dosyasını yükle"""
        rule_file_map = {
            "security": "security.md",
            "performance": "performance.md",
            "fundamentals": "dotnet-fundamentals.md",  # Genel fundamentals için
            "compilation": "compilation.md",
            "best-practices": "best-practices.md",
            "linter": "linter.md",  # Yeni oluşturulacak
        }
        
        rule_file = rule_file_map.get(category)
        if not rule_file:
            return ""
        
        rule_path = RULES_DIR / rule_file
        if rule_path.exists():
            try:
                with open(rule_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.warning("failed_to_load_base_rule", category=category, error=str(e))
        
        return ""
    
    async def generate_rule_for_language(
        self,
        language: str,
        category: str,
        force_regenerate: bool = False
    ) -> bool:
        """
        Belirli bir dil ve kategori için rule dosyası oluştur
        
        Args:
            language: Programlama dili (python, csharp, vb.)
            category: Rule kategorisi (security, performance, vb.)
            force_regenerate: Mevcut dosya varsa yeniden oluştur
            
        Returns:
            Başarılı olursa True
        """
        # Dosya adını oluştur: {language}-{category}.md
        rule_filename = f"{language}-{category}.md"
        rule_path = RULES_DIR / rule_filename
        
        # Dosya varsa ve force_regenerate False ise atla
        if rule_path.exists() and not force_regenerate:
            logger.info("rule_file_exists", file=rule_filename, language=language, category=category)
            return True
        
        try:
            # Temel rule'u yükle
            base_rules = self._load_base_rule(category)
            
            # Dil görünen adını al
            from services.language_detector import LanguageDetector
            language_display = LanguageDetector.get_language_display_name(language)
            
            # Prompt oluştur
            prompt = self.RULE_GENERATION_PROMPT.format(
                language=language_display,
                category=category,
                base_rules=base_rules[:8000]  # Token limiti için kısalt
            )
            
            logger.info("generating_rule", language=language, category=category)
            
            # AI'dan rule oluştur (simple single-provider routing)
            system_msg = "Sen bir programlama dili uzmanısın ve kod review kuralları oluşturuyorsun."
            provider_used, model_used, response = self.router.chat(system=system_msg, user=prompt)
            self.last_provider_used = provider_used
            self.last_model_used = model_used
            
            # Dosyayı kaydet
            rule_path.parent.mkdir(parents=True, exist_ok=True)
            with open(rule_path, 'w', encoding='utf-8') as f:
                f.write(response)
            
            logger.info("rule_generated", file=rule_filename, language=language, category=category)
            return True
            
        except Exception as e:
            logger.exception("rule_generation_failed", language=language, category=category, error=str(e))
            return False
    
    async def generate_all_rules_for_language(
        self,
        language: str,
        categories: Optional[List[str]] = None,
        force_regenerate: bool = False
    ) -> Dict[str, bool]:
        """
        Bir dil için tüm rule kategorilerini oluştur
        
        Args:
            language: Programlama dili
            categories: Oluşturulacak kategoriler (None ise tümü)
            force_regenerate: Mevcut dosyaları yeniden oluştur
            
        Returns:
            Kategori -> başarı durumu mapping'i
        """
        if categories is None:
            categories = RULE_CATEGORIES
        
        results = {}
        for category in categories:
            success = await self.generate_rule_for_language(
                language=language,
                category=category,
                force_regenerate=force_regenerate
            )
            results[category] = success
        
        return results
    
    # NOTE: SDK-specific implementations moved to services/ai_providers/*

