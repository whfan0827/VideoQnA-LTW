/**
 * Library數據同步Hook
 * 自動檢測和修復前後端數據不一致問題
 */
import { useState, useEffect, useCallback } from 'react';
import { useAppConfig } from './useAppConfig';

interface LibraryStatus {
    name: string;
    consistent: boolean;
    issues: string[];
    components: {
        azure_search_index: boolean;
        library_settings: boolean;
        video_records: boolean;
        file_hash_cache: boolean;
    };
}

interface SyncStatus {
    isLoading: boolean;
    lastSync: Date | null;
    inconsistentCount: number;
    libraries: LibraryStatus[];
    error: string | null;
}

export function useLibrarySync() {
    const { targetLibrary, setTargetLibrary } = useAppConfig();
    const [syncStatus, setSyncStatus] = useState<SyncStatus>({
        isLoading: false,
        lastSync: null,
        inconsistentCount: 0,
        libraries: [],
        error: null
    });

    // 檢查library狀態
    const checkLibraryStatus = useCallback(async () => {
        try {
            setSyncStatus(prev => ({ ...prev, isLoading: true, error: null }));

            const response = await fetch('/libraries/status');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            
            setSyncStatus(prev => ({
                ...prev,
                isLoading: false,
                lastSync: new Date(),
                inconsistentCount: data.summary.inconsistent,
                libraries: data.libraries
            }));

            return data;

        } catch (error) {
            console.error('Failed to check library status:', error);
            setSyncStatus(prev => ({
                ...prev,
                isLoading: false,
                error: error instanceof Error ? error.message : 'Unknown error'
            }));
            return null;
        }
    }, []);

    // 自動修復不一致
    const autoFixInconsistencies = useCallback(async () => {
        try {
            setSyncStatus(prev => ({ ...prev, isLoading: true, error: null }));

            const response = await fetch('/libraries/cleanup-inconsistent', {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const result = await response.json();
            
            // 修復後重新檢查狀態
            await checkLibraryStatus();
            
            return result;

        } catch (error) {
            console.error('Failed to auto-fix inconsistencies:', error);
            setSyncStatus(prev => ({
                ...prev,
                isLoading: false,
                error: error instanceof Error ? error.message : 'Auto-fix failed'
            }));
            return null;
        }
    }, [checkLibraryStatus]);

    // 驗證當前選中的library是否有效
    const validateCurrentLibrary = useCallback(() => {
        if (!targetLibrary) return true;

        const currentLib = syncStatus.libraries.find(lib => lib.name === targetLibrary);
        
        // 如果library不存在或不一致，清空選擇
        if (!currentLib || !currentLib.consistent) {
            console.warn(`Current library "${targetLibrary}" is invalid or inconsistent, clearing selection`);
            setTargetLibrary('');
            
            // 清空localStorage中的相關數據
            localStorage.removeItem('target_library');
            
            return false;
        }

        return true;
    }, [targetLibrary, setTargetLibrary, syncStatus.libraries]);

    // 自動同步機制
    useEffect(() => {
        // 首次加載時檢查狀態
        checkLibraryStatus();
        
        // 設定定期檢查（每5分鐘）
        const interval = setInterval(checkLibraryStatus, 5 * 60 * 1000);
        
        return () => clearInterval(interval);
    }, [checkLibraryStatus]);

    // 當library狀態更新時，驗證當前選擇
    useEffect(() => {
        if (syncStatus.libraries.length > 0) {
            validateCurrentLibrary();
        }
    }, [syncStatus.libraries, validateCurrentLibrary]);

    // 監聽storage事件，同步不同標籤頁的狀態
    useEffect(() => {
        const handleStorageChange = (e: StorageEvent) => {
            if (e.key === 'target_library' && e.newValue !== targetLibrary) {
                // 其他標籤頁更改了library選擇，同步到當前頁面
                setTargetLibrary(e.newValue || '');
            }
        };

        window.addEventListener('storage', handleStorageChange);
        return () => window.removeEventListener('storage', handleStorageChange);
    }, [targetLibrary, setTargetLibrary]);

    return {
        syncStatus,
        checkLibraryStatus,
        autoFixInconsistencies,
        validateCurrentLibrary,
        
        // 便捷方法
        hasInconsistencies: syncStatus.inconsistentCount > 0,
        isCurrentLibraryValid: targetLibrary ? 
            syncStatus.libraries.some(lib => lib.name === targetLibrary && lib.consistent) : 
            true
    };
}