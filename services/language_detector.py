"""
Dil tespiti servisi - diff'ten hangi programlama dilinin kullanıldığını tespit eder
"""
import structlog
from typing import List, Dict, Optional, Set
from collections import Counter
from pathlib import Path

logger = structlog.get_logger()


class LanguageDetector:
    """Diff'ten programlama dilini tespit eder"""
    
    # Dosya uzantısından dile mapping
    EXTENSION_TO_LANGUAGE = {
        # Python
        'py': 'python',
        'pyi': 'python',
        'pyx': 'python',
        'pyw': 'python',
        
        # C# / .NET
        'cs': 'csharp',
        'csx': 'csharp',
        
        # JavaScript / TypeScript
        'js': 'javascript',
        'jsx': 'javascript',
        'mjs': 'javascript',
        'ts': 'typescript',
        'tsx': 'typescript',
        
        # Java
        'java': 'java',
        'kt': 'kotlin',
        'scala': 'scala',
        
        # Go
        'go': 'go',
        
        # Rust
        'rs': 'rust',
        
        # C/C++
        'c': 'c',
        'cpp': 'cpp',
        'cc': 'cpp',
        'cxx': 'cpp',
        'h': 'c',
        'hpp': 'cpp',
        'hxx': 'cpp',
        
        # PHP
        'php': 'php',
        'phtml': 'php',
        
        # Ruby
        'rb': 'ruby',
        'rake': 'ruby',
        
        # Swift
        'swift': 'swift',
        
        # Dart
        'dart': 'dart',
        
        # Shell
        'sh': 'shell',
        'bash': 'shell',
        'zsh': 'shell',
        'fish': 'shell',
        
        # PowerShell
        'ps1': 'powershell',
        'psm1': 'powershell',
        
        # SQL
        'sql': 'sql',
        
        # HTML/CSS
        'html': 'html',
        'htm': 'html',
        'css': 'css',
        'scss': 'css',
        'sass': 'css',
        
        # YAML/JSON
        'yaml': 'yaml',
        'yml': 'yaml',
        'json': 'json',
        
        # XML
        'xml': 'xml',
        
        # Markdown
        'md': 'markdown',
        'markdown': 'markdown',
    }
    
    # Önemli dosyalar (config, build files vb.) - bunlar dil tespitinde sayılmaz
    CONFIG_FILES = {
        'dockerfile', 'makefile', 'cmakelists.txt', 'package.json', 
        'requirements.txt', 'pom.xml', 'build.gradle', 'cargo.toml',
        'go.mod', 'composer.json', 'gemfile', 'package-lock.json',
        'yarn.lock', 'tsconfig.json', 'webpack.config.js', '.gitignore',
        '.dockerignore', '.env', '.env.example'
    }
    
    @staticmethod
    def detect_from_files(files: List[str]) -> Optional[str]:
        """
        Dosya listesinden ana dili tespit et
        
        Args:
            files: Değişen dosya yolları listesi
            
        Returns:
            Tespit edilen dil (python, csharp, javascript, vb.) veya None
        """
        if not files:
            return None
        
        language_counts = Counter()
        
        for file_path in files:
            # Config dosyalarını atla
            file_name = Path(file_path).name.lower()
            if file_name in LanguageDetector.CONFIG_FILES:
                continue
            
            # Uzantıyı al
            ext = Path(file_path).suffix.lstrip('.').lower()
            
            if ext in LanguageDetector.EXTENSION_TO_LANGUAGE:
                language = LanguageDetector.EXTENSION_TO_LANGUAGE[ext]
                language_counts[language] += 1
        
        if not language_counts:
            return None
        
        # En çok kullanılan dili döndür
        most_common = language_counts.most_common(1)[0]
        detected_language = most_common[0]
        
        logger.info(
            "language_detected",
            language=detected_language,
            count=most_common[1],
            total_files=len(files),
            all_counts=dict(language_counts)
        )
        
        return detected_language
    
    @staticmethod
    def detect_from_diff(diff_text: str) -> Optional[str]:
        """
        Diff metninden dil tespiti yap
        
        Args:
            diff_text: Git diff metni
            
        Returns:
            Tespit edilen dil veya None
        """
        from services.diff_analyzer import DiffAnalyzer
        
        files = DiffAnalyzer.get_changed_files(diff_text)
        return LanguageDetector.detect_from_files(files)
    
    @staticmethod
    def get_supported_languages() -> List[str]:
        """Desteklenen dillerin listesini döndür"""
        return sorted(set(LanguageDetector.EXTENSION_TO_LANGUAGE.values()))
    
    @staticmethod
    def get_language_display_name(language: str) -> str:
        """Dil kodunu görünen isme çevir"""
        display_names = {
            'python': 'Python',
            'csharp': 'C#',
            'javascript': 'JavaScript',
            'typescript': 'TypeScript',
            'java': 'Java',
            'kotlin': 'Kotlin',
            'scala': 'Scala',
            'go': 'Go',
            'rust': 'Rust',
            'c': 'C',
            'cpp': 'C++',
            'php': 'PHP',
            'ruby': 'Ruby',
            'swift': 'Swift',
            'dart': 'Dart',
            'shell': 'Shell',
            'powershell': 'PowerShell',
            'sql': 'SQL',
            'html': 'HTML',
            'css': 'CSS',
            'yaml': 'YAML',
            'json': 'JSON',
            'xml': 'XML',
            'markdown': 'Markdown',
        }
        return display_names.get(language, language.capitalize())

