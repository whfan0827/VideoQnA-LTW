import { useState, useEffect, useCallback } from 'react';

export interface TaskStatus {
    task_id: string;
    status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
    progress: number;
    current_step: string;
    filename: string;
    library_name: string;
    created_at: string;
    started_at?: string;
    completed_at?: string;
    error_message?: string;
}

export const useTaskManager = () => {
    const [tasks, setTasks] = useState<TaskStatus[]>([]);
    const [isPolling, setIsPolling] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Load tasks from localStorage on mount
    useEffect(() => {
        const savedTasks = localStorage.getItem('uploadTasks');
        if (savedTasks) {
            try {
                const parsedTasks = JSON.parse(savedTasks);
                const activeTasks = parsedTasks.filter((task: TaskStatus) => 
                    task.status === 'pending' || task.status === 'processing'
                );
                setTasks(activeTasks);
                if (activeTasks.length > 0) {
                    setIsPolling(true);
                }
            } catch (error) {
                console.error('Error loading saved tasks:', error);
                localStorage.removeItem('uploadTasks');
            }
        }
    }, []);

    // Save tasks to localStorage whenever tasks change
    useEffect(() => {
        if (tasks.length > 0) {
            localStorage.setItem('uploadTasks', JSON.stringify(tasks));
        } else {
            localStorage.removeItem('uploadTasks');
        }
    }, [tasks]);

    const addTask = useCallback((taskId: string, filename: string, libraryName: string) => {
        const newTask: TaskStatus = {
            task_id: taskId,
            status: 'pending',
            progress: 0,
            current_step: 'Queued for processing',
            filename: filename,
            library_name: libraryName,
            created_at: new Date().toISOString()
        };

        setTasks(prev => [...prev, newTask]);
        
        if (!isPolling) {
            setIsPolling(true);
        }
    }, [isPolling]);

    const removeTask = useCallback(async (taskId: string) => {
        try {
            const response = await fetch(`/tasks/${taskId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                setTasks(prev => prev.filter(task => task.task_id !== taskId));
            } else {
                let errorMessage = 'Failed to remove task';
                try {
                    const text = await response.text();
                    if (text.trim()) {
                        const errorData = JSON.parse(text);
                        errorMessage = errorData.error || errorMessage;
                    }
                } catch (parseError) {
                    console.warn('Could not parse error response:', parseError);
                }
                throw new Error(errorMessage);
            }
        } catch (error) {
            console.error('Error removing task:', error);
            setError(error instanceof Error ? error.message : 'Failed to remove task');
            // Still remove from UI on client error
            setTasks(prev => prev.filter(task => task.task_id !== taskId));
        }
    }, []);

    const clearCompletedTasks = useCallback(() => {
        setTasks(prev => prev.filter(task => 
            task.status !== 'completed' && task.status !== 'failed' && task.status !== 'cancelled'
        ));
    }, []);

    const clearAllTasks = useCallback(() => {
        setTasks([]);
        setIsPolling(false);
        localStorage.removeItem('uploadTasks');
    }, []);

    const cancelTask = useCallback(async (taskId: string) => {
        try {
            const response = await fetch(`/tasks/${taskId}/cancel`, {
                method: 'POST'
            });

            if (response.ok) {
                setTasks(prev => prev.map(task => 
                    task.task_id === taskId 
                        ? { ...task, status: 'cancelled' as const, current_step: 'Cancelled by user' }
                        : task
                ));
            } else {
                let errorMessage = 'Failed to cancel task';
                try {
                    const text = await response.text();
                    if (text.trim()) {
                        const errorData = JSON.parse(text);
                        errorMessage = errorData.error || errorMessage;
                    }
                } catch (parseError) {
                    console.warn('Could not parse error response:', parseError);
                }
                throw new Error(errorMessage);
            }
        } catch (error) {
            console.error('Error cancelling task:', error);
            setError(error instanceof Error ? error.message : 'Failed to cancel task');
        }
    }, []);

    // Polling logic
    useEffect(() => {
        let interval: number;

        if (isPolling && tasks.length > 0) {
            interval = setInterval(async () => {
                try {
                    setError(null);
                    
                    // Only poll active tasks
                    const activeTasks = tasks.filter(task => 
                        task.status === 'pending' || task.status === 'processing'
                    );

                    if (activeTasks.length === 0) {
                        setIsPolling(false);
                        return;
                    }

                    // Batch query all active task statuses
                    const statusPromises = activeTasks.map(async (task) => {
                        try {
                            const response = await fetch(`/tasks/${task.task_id}`);
                            if (response.ok) {
                                const text = await response.text();
                                if (!text.trim()) {
                                    console.warn(`Empty response for task ${task.task_id}`);
                                    return { task_id: task.task_id, error: true };
                                }
                                try {
                                    return JSON.parse(text);
                                } catch (parseError) {
                                    console.warn(`Invalid JSON for task ${task.task_id}:`, text);
                                    return { task_id: task.task_id, error: true };
                                }
                            } else {
                                console.warn(`Failed to fetch status for task ${task.task_id}: ${response.status}`);
                                return { task_id: task.task_id, error: true };
                            }
                        } catch (error) {
                            console.warn(`Error fetching task ${task.task_id}:`, error);
                            return { task_id: task.task_id, error: true };
                        }
                    });

                    const statuses = await Promise.all(statusPromises);

                    // Update tasks with new statuses
                    setTasks(prevTasks => 
                        prevTasks.map(task => {
                            const updatedStatus = statuses.find(s => s.task_id === task.task_id);
                            return updatedStatus && !updatedStatus.error 
                                ? { ...task, ...updatedStatus }
                                : task;
                        })
                    );

                } catch (error) {
                    console.error('Error polling task statuses:', error);
                    setError('Failed to update task statuses');
                }
            }, 3000); // Poll every 3 seconds
        }

        return () => {
            if (interval) clearInterval(interval);
        };
    }, [isPolling, tasks]);

    // Auto-stop polling when no active tasks remain
    useEffect(() => {
        const activeTasks = tasks.filter(task => 
            task.status === 'pending' || task.status === 'processing'
        );
        
        if (activeTasks.length === 0 && isPolling) {
            setIsPolling(false);
        }
    }, [tasks, isPolling]);

    return {
        tasks,
        addTask,
        removeTask,
        clearCompletedTasks,
        clearAllTasks,
        cancelTask,
        isPolling,
        error
    };
};
