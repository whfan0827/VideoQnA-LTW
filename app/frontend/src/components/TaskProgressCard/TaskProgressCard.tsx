import { IconButton, ProgressIndicator, MessageBar, MessageBarType } from "@fluentui/react";
import { TaskStatus } from "../../hooks/useTaskManager";
import styles from "./TaskProgressCard.module.css";

interface TaskProgressCardProps {
    task: TaskStatus;
    onRemove?: () => void;
    onCancel?: () => void;
}

export const TaskProgressCard = ({ task, onRemove, onCancel }: TaskProgressCardProps) => {
    const getStatusColor = (status: string) => {
        switch (status) {
            case 'completed': return '#107c10';
            case 'failed': return '#d13438';
            case 'processing': return '#0078d4';
            case 'cancelled': return '#605e5c';
            default: return '#605e5c';
        }
    };


    const isActive = task.status === 'pending' || task.status === 'processing';
    const isCompleted = task.status === 'completed';
    const isFailed = task.status === 'failed';
    const isCancelled = task.status === 'cancelled';

    return (
        <div className={`${styles.taskCard} ${styles[task.status]}`}>
            <div className={styles.taskHeader}>
                <div className={styles.taskInfo}>
                    <div className={styles.taskTitle}>
                        <strong>{task.filename}</strong>
                        <small>→ {task.library_name}</small>
                    </div>
                    <div className={styles.taskStatus} style={{ color: getStatusColor(task.status) }}>
                        <span className={styles.statusIcon}>
                            {/* We can add actual icons here if needed */}
                            {task.status.charAt(0).toUpperCase() + task.status.slice(1)}
                        </span>
                    </div>
                </div>
                
                <div className={styles.taskActions}>
                    {isActive && onCancel && (
                        <IconButton 
                            iconProps={{ iconName: 'Cancel' }}
                            onClick={onCancel}
                            title="Cancel task"
                            className={styles.cancelButton}
                        />
                    )}
                    {(isCompleted || isFailed || isCancelled) && onRemove && (
                        <IconButton 
                            iconProps={{ iconName: 'Clear' }}
                            onClick={onRemove}
                            title="Remove from list"
                            className={styles.removeButton}
                        />
                    )}
                </div>
            </div>
            
            <div className={styles.taskDetails}>
                <div className={styles.currentStep}>
                    {task.current_step}
                </div>
                
                {isActive && (
                    <div className={styles.progressSection}>
                        <ProgressIndicator 
                            percentComplete={task.progress / 100}
                            description={`${task.progress}%`}
                        />
                    </div>
                )}
                
                {task.created_at && (
                    <div className={styles.timestamp}>
                        Started: {new Date(task.created_at).toLocaleString()}
                    </div>
                )}
                
                {task.completed_at && (
                    <div className={styles.timestamp}>
                        Completed: {new Date(task.completed_at).toLocaleString()}
                    </div>
                )}
            </div>
            
            {task.error_message && (
                <div className={styles.errorSection}>
                    <MessageBar messageBarType={MessageBarType.error} isMultiline>
                        {task.error_message}
                    </MessageBar>
                </div>
            )}
        </div>
    );
};
