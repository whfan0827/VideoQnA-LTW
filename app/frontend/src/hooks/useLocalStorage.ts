import { useState, useEffect } from 'react';

/**
 * Custom hook for localStorage management
 * Provides a clean API for localStorage access with automatic synchronization
 */
export function useLocalStorage<T>(key: string, defaultValue: T) {
    const [value, setValue] = useState<T>(() => {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error(`Error reading localStorage key "${key}":`, error);
            return defaultValue;
        }
    });

    const setStorageValue = (newValue: T) => {
        try {
            setValue(newValue);
            localStorage.setItem(key, JSON.stringify(newValue));
            
            // Trigger storage event for cross-tab synchronization
            window.dispatchEvent(new StorageEvent('storage', {
                key,
                newValue: JSON.stringify(newValue),
                oldValue: localStorage.getItem(key),
                url: window.location.href,
                storageArea: localStorage
            }));
        } catch (error) {
            console.error(`Error setting localStorage key "${key}":`, error);
        }
    };

    // Listen for storage changes
    useEffect(() => {
        const handleStorageChange = (e: StorageEvent) => {
            if (e.key === key && e.newValue !== null) {
                try {
                    setValue(JSON.parse(e.newValue));
                } catch (error) {
                    console.error(`Error parsing storage event for key "${key}":`, error);
                }
            }
        };

        // Listen for custom storage events (same tab)
        const handleCustomStorageChange = () => {
            try {
                const item = localStorage.getItem(key);
                if (item !== null) {
                    setValue(JSON.parse(item));
                }
            } catch (error) {
                console.error(`Error reading localStorage key "${key}" on custom event:`, error);
            }
        };

        window.addEventListener('storage', handleStorageChange);
        window.addEventListener('localStorageChange', handleCustomStorageChange);

        return () => {
            window.removeEventListener('storage', handleStorageChange);
            window.removeEventListener('localStorageChange', handleCustomStorageChange);
        };
    }, [key]);

    return [value, setStorageValue] as const;
}