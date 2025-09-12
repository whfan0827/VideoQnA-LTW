"""
數據一致性監控服務
定期檢查和修復數據不一致問題
"""
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DataConsistencyMonitor:
    """數據一致性監控器"""
    
    def __init__(self, library_manager):
        self.library_manager = library_manager
        self.is_running = False
        self.monitor_thread = None
        self.last_check_time = None
        self.last_check_results = {}
        self.check_interval_seconds = 3600  # Default 1 hour
        self.timer = None
    
    def start_monitoring(self, check_interval_minutes: int = 60):
        """開始監控數據一致性"""
        if self.is_running:
            logger.warning("Data consistency monitor is already running")
            return
        
        logger.info(f"Starting data consistency monitor with {check_interval_minutes} minute intervals")
        
        self.check_interval_seconds = check_interval_minutes * 60
        
        # 立即執行一次檢查
        self._perform_consistency_check()
        
        # 啟動監控線程
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止監控"""
        logger.info("Stopping data consistency monitor")
        self.is_running = False
        
        if self.timer:
            self.timer.cancel()
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
    
    def _monitor_loop(self):
        """監控循環"""
        while self.is_running:
            try:
                # 設定下次檢查的定時器
                self.timer = threading.Timer(self.check_interval_seconds, self._perform_consistency_check)
                self.timer.start()
                self.timer.join()  # 等待定時器完成
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # 出錯時等待1分鐘再繼續
    
    def _perform_consistency_check(self):
        """執行一致性檢查"""
        try:
            logger.info("Performing data consistency check")
            self.last_check_time = datetime.now()
            
            # 獲取所有library狀態
            libraries = self.library_manager.list_all_libraries_with_status()
            
            # 分析結果
            total_libraries = len(libraries)
            consistent_libraries = [lib for lib in libraries if lib['consistent']]
            inconsistent_libraries = [lib for lib in libraries if not lib['consistent']]
            
            self.last_check_results = {
                'check_time': self.last_check_time.isoformat(),
                'total_libraries': total_libraries,
                'consistent_count': len(consistent_libraries),
                'inconsistent_count': len(inconsistent_libraries),
                'inconsistent_libraries': [lib['name'] for lib in inconsistent_libraries],
                'issues_found': []
            }
            
            # 記錄問題
            for lib in inconsistent_libraries:
                issues = f"Library '{lib['name']}': {', '.join(lib['issues'])}"
                self.last_check_results['issues_found'].append(issues)
                logger.warning(issues)
            
            # 如果有不一致的library，記錄警告
            if inconsistent_libraries:
                logger.warning(f"Found {len(inconsistent_libraries)} inconsistent libraries: {[lib['name'] for lib in inconsistent_libraries]}")
            else:
                logger.info(f"All {total_libraries} libraries are consistent")
        
        except Exception as e:
            logger.error(f"Error during consistency check: {e}")
            self.last_check_results = {
                'check_time': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def get_last_check_results(self) -> Dict[str, Any]:
        """獲取最後一次檢查結果"""
        return self.last_check_results
    
    def force_consistency_check(self) -> Dict[str, Any]:
        """強制執行一致性檢查並返回結果"""
        self._perform_consistency_check()
        return self.last_check_results
    
    def auto_fix_inconsistencies(self) -> Dict[str, Any]:
        """自動修復不一致問題"""
        try:
            logger.info("Starting automatic inconsistency fix")
            
            # 執行清理
            cleanup_results = self.library_manager.cleanup_inconsistent_libraries()
            
            # 再次檢查
            self._perform_consistency_check()
            
            return {
                'auto_fix_time': datetime.now().isoformat(),
                'cleanup_results': [
                    {
                        'library': result.library_name,
                        'success': result.success,
                        'cleaned_components': result.cleaned_components,
                        'errors': result.errors
                    }
                    for result in cleanup_results
                ],
                'post_fix_status': self.last_check_results
            }
        
        except Exception as e:
            logger.error(f"Error during auto-fix: {e}")
            return {'error': str(e)}
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """獲取監控狀態"""
        return {
            'is_running': self.is_running,
            'last_check_time': self.last_check_time.isoformat() if self.last_check_time else None,
            'monitor_thread_alive': self.monitor_thread.is_alive() if self.monitor_thread else False,
            'check_interval_minutes': self.check_interval_seconds // 60
        }