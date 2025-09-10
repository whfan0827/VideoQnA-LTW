import { useState } from 'react';

/**
 * Generic hook for API calls with loading and error states
 */
export function useApiCall<T, P = unknown>() {
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<unknown>();
    const [data, setData] = useState<T>();

    // Overload for functions with parameters
    async function execute(apiCall: (params: P) => Promise<T>, params: P): Promise<T>;
    // Overload for functions without parameters
    async function execute(apiCall: () => Promise<T>): Promise<T>;
    
    async function execute(apiCall: any, params?: any): Promise<T> {
        try {
            setIsLoading(true);
            setError(undefined);
            const result = params !== undefined ? await apiCall(params) : await apiCall();
            setData(result);
            return result;
        } catch (err) {
            setError(err);
            throw err;
        } finally {
            setIsLoading(false);
        }
    }

    const reset = () => {
        setIsLoading(false);
        setError(undefined);
        setData(undefined);
    };

    return {
        isLoading,
        error,
        data,
        execute,
        reset
    };
}