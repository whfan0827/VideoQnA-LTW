import { useLocalStorage } from './useLocalStorage';

/**
 * Application configuration management
 * Centralized configuration with localStorage persistence
 */
export function useAppConfig() {
    const [topK, setTopK] = useLocalStorage('top_k', 3);
    const [targetLibrary, setTargetLibrary] = useLocalStorage('target_library', '');
    const [temperature, setTemperature] = useLocalStorage('temperature', 0.7);
    const [topP, setTopP] = useLocalStorage('top_p', 1.0);

    return {
        // Retrieval settings
        topK,
        setTopK,
        
        // Library settings
        targetLibrary,
        setTargetLibrary,
        
        // AI parameters
        temperature,
        setTemperature,
        topP,
        setTopP,
        
        // Reset all settings
        resetToDefaults: () => {
            setTopK(3);
            setTargetLibrary('');
            setTemperature(0.7);
            setTopP(1.0);
        }
    };
}