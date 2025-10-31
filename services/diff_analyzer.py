"""
Diff parsing and analysis utilities
"""
import structlog
from typing import List, Dict, Any
from unidiff import PatchSet

logger = structlog.get_logger()


class DiffAnalyzer:
    """Analyze and parse git diffs"""
    
    @staticmethod
    def parse_diff(diff_text: str) -> Dict[str, Any]:
        """
        Parse unified diff format
        
        Args:
            diff_text: Unified diff text
            
        Returns:
            Parsed diff information
        """
        try:
            patch_set = PatchSet(diff_text)
            
            files_changed = []
            total_additions = 0
            total_deletions = 0
            
            for patched_file in patch_set:
                file_info = {
                    'path': patched_file.path,
                    'additions': patched_file.added,
                    'deletions': patched_file.removed,
                    'is_new': patched_file.is_added_file,
                    'is_deleted': patched_file.is_removed_file,
                    'hunks': []
                }
                
                for hunk in patched_file:
                    hunk_info = {
                        'source_start': hunk.source_start,
                        'source_length': hunk.source_length,
                        'target_start': hunk.target_start,
                        'target_length': hunk.target_length,
                        'changes': []
                    }
                    
                    for line in hunk:
                        hunk_info['changes'].append({
                            'type': 'added' if line.is_added else 'removed' if line.is_removed else 'context',
                            'line_number': line.target_line_no if line.is_added else line.source_line_no,
                            'content': line.value
                        })
                    
                    file_info['hunks'].append(hunk_info)
                
                files_changed.append(file_info)
                total_additions += patched_file.added
                total_deletions += patched_file.removed
            
            return {
                'files': files_changed,
                'total_additions': total_additions,
                'total_deletions': total_deletions,
                'files_count': len(files_changed)
            }
            
        except Exception as e:
            logger.exception("diff_parse_failed", error=str(e))
            return {
                'files': [],
                'total_additions': 0,
                'total_deletions': 0,
                'files_count': 0,
                'error': str(e)
            }
    
    @staticmethod
    def get_changed_files(diff_text: str) -> List[str]:
        """Extract list of changed file paths"""
        try:
            patch_set = PatchSet(diff_text)
            return [f.path for f in patch_set]
        except:
            return []
    
    @staticmethod
    def get_file_extension_stats(files: List[str]) -> Dict[str, int]:
        """Get statistics about file extensions"""
        stats = {}
        for file in files:
            ext = file.split('.')[-1] if '.' in file else 'no_extension'
            stats[ext] = stats.get(ext, 0) + 1
        return stats

