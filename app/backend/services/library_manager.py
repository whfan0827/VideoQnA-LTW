"""
統一Library數據管理服務
解決數據散布和不一致問題
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from database.init_db import get_connection
from vi_search.constants import DATA_DIR

logger = logging.getLogger(__name__)

@dataclass
class LibraryCleanupResult:
    """清理結果"""
    library_name: str
    success: bool
    cleaned_components: List[str]
    failed_components: List[str]
    errors: List[str]

class LibraryManager:
    """統一的Library數據管理服務"""
    
    def __init__(self, prompt_content_db, settings_service, db_manager):
        self.prompt_content_db = prompt_content_db
        self.settings_service = settings_service
        self.db_manager = db_manager
        self.cache_file = DATA_DIR / "file_hash_cache.json"
    
    def delete_library_completely(self, library_name: str) -> LibraryCleanupResult:
        """
        完全刪除library及其所有相關數據
        實現級聯刪除和錯誤恢復
        """
        result = LibraryCleanupResult(
            library_name=library_name,
            success=True,
            cleaned_components=[],
            failed_components=[],
            errors=[]
        )
        
        logger.info(f"Starting complete deletion of library: {library_name}")
        
        # 1. 刪除Azure Search Index
        try:
            self.prompt_content_db.remove_db(library_name)
            result.cleaned_components.append("azure_search_index")
            logger.info(f"✅ Deleted Azure Search Index: {library_name}")
        except Exception as e:
            error_msg = f"Failed to delete Azure Search Index: {str(e)}"
            result.errors.append(error_msg)
            result.failed_components.append("azure_search_index")
            logger.error(error_msg)
        
        # 2. 刪除SQLite數據庫設定
        try:
            with get_connection() as conn:
                cursor = conn.execute("DELETE FROM library_settings WHERE library_name = ?", (library_name,))
                deleted_settings = cursor.rowcount
                conn.commit()
            result.cleaned_components.append(f"library_settings({deleted_settings})")
            logger.info(f"✅ Deleted {deleted_settings} library settings")
        except Exception as e:
            error_msg = f"Failed to delete library settings: {str(e)}"
            result.errors.append(error_msg)
            result.failed_components.append("library_settings")
            logger.error(error_msg)
        
        # 3. 刪除video記錄
        try:
            deleted_videos = self.db_manager.delete_library_videos(library_name)
            result.cleaned_components.append(f"video_records({deleted_videos})")
            logger.info(f"✅ Deleted {deleted_videos} video records")
        except Exception as e:
            error_msg = f"Failed to delete video records: {str(e)}"
            result.errors.append(error_msg)
            result.failed_components.append("video_records")
            logger.error(error_msg)
        
        # 4. 清理文件hash緩存
        try:
            cleaned_cache = self._clean_file_hash_cache(library_name)
            result.cleaned_components.append(f"file_hash_cache({cleaned_cache})")
            logger.info(f"✅ Cleaned {cleaned_cache} hash cache entries")
        except Exception as e:
            error_msg = f"Failed to clean file hash cache: {str(e)}"
            result.errors.append(error_msg)
            result.failed_components.append("file_hash_cache")
            logger.error(error_msg)
        
        # 5. 清理任務記錄
        try:
            deleted_tasks = self._clean_library_tasks(library_name)
            result.cleaned_components.append(f"tasks({deleted_tasks})")
            logger.info(f"✅ Cleaned {deleted_tasks} task records")
        except Exception as e:
            error_msg = f"Failed to clean task records: {str(e)}"
            result.errors.append(error_msg)
            result.failed_components.append("tasks")
            logger.error(error_msg)
        
        # 判斷整體成功與否
        result.success = len(result.failed_components) == 0
        
        if result.success:
            logger.info(f"🎉 Complete deletion SUCCESS for library: {library_name}")
        else:
            logger.error(f"❌ Complete deletion PARTIAL FAILURE for library: {library_name}")
            logger.error(f"Failed components: {result.failed_components}")
        
        return result
    
    def _clean_file_hash_cache(self, library_name: str) -> int:
        """清理文件hash緩存中的library相關條目"""
        if not self.cache_file.exists():
            return 0
        
        # 讀取緩存文件
        with open(self.cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # 找出要刪除的條目
        keys_to_delete = []
        for key, value in cache_data.items():
            if isinstance(value, dict) and value.get('library_name') == library_name:
                keys_to_delete.append(key)
        
        # 刪除條目
        for key in keys_to_delete:
            del cache_data[key]
        
        # 寫回文件
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        
        return len(keys_to_delete)
    
    def _clean_library_tasks(self, library_name: str) -> int:
        """清理與library相關的任務記錄"""
        try:
            with get_connection() as conn:
                cursor = conn.execute("""
                    DELETE FROM tasks 
                    WHERE library_name = ? OR task_data LIKE ?
                """, (library_name, f'%{library_name}%'))
                deleted_count = cursor.rowcount
                conn.commit()
                return deleted_count
        except Exception:
            # 如果tasks表不存在，返回0
            return 0
    
    def verify_library_consistency(self, library_name: str) -> Dict[str, Any]:
        """驗證library數據一致性"""
        result = {
            'library_name': library_name,
            'consistent': True,
            'issues': [],
            'components': {}
        }
        
        # 檢查各組件是否存在
        components = {
            'azure_search_index': self._check_azure_index_exists(library_name),
            'library_settings': self._check_library_settings_exists(library_name),
            'video_records': self._check_video_records_exist(library_name),
            'file_hash_cache': self._check_file_hash_cache_exists(library_name)
        }
        
        result['components'] = components
        
        # 檢查不一致
        existing_components = [k for k, v in components.items() if v]
        if len(existing_components) > 0 and len(existing_components) < len(components):
            result['consistent'] = False
            result['issues'].append(f"Partial data found in: {existing_components}")
        
        return result
    
    def _check_azure_index_exists(self, library_name: str) -> bool:
        """檢查Azure Search Index是否存在"""
        try:
            available_dbs = self.prompt_content_db.get_available_dbs()
            return library_name in available_dbs
        except Exception:
            return False
    
    def _check_library_settings_exists(self, library_name: str) -> bool:
        """檢查library設定是否存在"""
        try:
            with get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM library_settings WHERE library_name = ?", (library_name,))
                return cursor.fetchone()[0] > 0
        except Exception:
            return False
    
    def _check_video_records_exist(self, library_name: str) -> bool:
        """檢查video記錄是否存在"""
        try:
            videos = self.db_manager.get_library_videos(library_name)
            return len(videos) > 0
        except Exception:
            return False
    
    def _check_file_hash_cache_exists(self, library_name: str) -> bool:
        """檢查文件hash緩存中是否有相關條目"""
        try:
            if not self.cache_file.exists():
                return False
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            for value in cache_data.values():
                if isinstance(value, dict) and value.get('library_name') == library_name:
                    return True
            return False
        except Exception:
            return False
    
    def list_all_libraries_with_status(self) -> List[Dict[str, Any]]:
        """列出所有library及其狀態"""
        libraries = []
        
        # 從Azure Search獲取所有index
        try:
            azure_indexes = self.prompt_content_db.get_available_dbs()
        except Exception:
            azure_indexes = []
        
        # 從數據庫獲取所有library設定
        try:
            with get_connection() as conn:
                cursor = conn.execute("SELECT DISTINCT library_name FROM library_settings")
                db_libraries = [row[0] for row in cursor.fetchall()]
        except Exception:
            db_libraries = []
        
        # 合併所有library名稱
        all_library_names = set(azure_indexes + db_libraries)
        
        for lib_name in all_library_names:
            status = self.verify_library_consistency(lib_name)
            libraries.append({
                'name': lib_name,
                'consistent': status['consistent'],
                'issues': status['issues'],
                'components': status['components']
            })
        
        return libraries
    
    def cleanup_inconsistent_libraries(self) -> List[LibraryCleanupResult]:
        """自動清理所有不一致的libraries"""
        libraries = self.list_all_libraries_with_status()
        results = []
        
        for lib in libraries:
            if not lib['consistent']:
                logger.info(f"Cleaning up inconsistent library: {lib['name']}")
                result = self.delete_library_completely(lib['name'])
                results.append(result)
        
        return results