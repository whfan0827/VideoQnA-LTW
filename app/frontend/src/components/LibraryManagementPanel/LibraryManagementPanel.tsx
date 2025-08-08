import { useState } from "react";
import { 
    TextField, 
    PrimaryButton, 
    DefaultButton, 
    Dropdown, 
    MessageBar, 
    MessageBarType, 
    Stack, 
    Separator, 
    IDropdownOption,
    Pivot,
    PivotItem
} from "@fluentui/react";
import styles from "./LibraryManagementPanel.module.css";
import { useTaskManager } from "../../hooks/useTaskManager";
import { TaskProgressCard } from "../TaskProgressCard";
import VideoList from "../VideoList/VideoList";

interface LibraryManagementPanelProps {
    indexes: IDropdownOption[];
    onLibrariesChanged: () => void;
}

export const LibraryManagementPanel = ({ indexes, onLibrariesChanged }: LibraryManagementPanelProps) => {
    const [activeTab, setActiveTab] = useState("upload");
    const [newLibraryName, setNewLibraryName] = useState("");
    const [selectedLibraryToDelete, setSelectedLibraryToDelete] = useState("");
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [selectedUploadLibrary, setSelectedUploadLibrary] = useState("");
    const [selectedManageLibrary, setSelectedManageLibrary] = useState("");
    const [isProcessing, setIsProcessing] = useState(false);
    const [message, setMessage] = useState<{ text: string; type: MessageBarType } | null>(null);
    
    // Task management
    const { tasks, addTask, removeTask, clearCompletedTasks, clearAllTasks, cancelTask, error: taskError } = useTaskManager();

    const showMessage = (text: string, type: MessageBarType) => {
        setMessage({ text, type });
        setTimeout(() => setMessage(null), 5000);
    };

    // Create new Library
    const handleCreateLibrary = async () => {
        if (!newLibraryName.trim()) return;
        
        setIsProcessing(true);
        try {
            const libraryName = `vi-${newLibraryName.toLowerCase().replace(/\s+/g, '-')}-index`;
            
            const response = await fetch("/libraries", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ name: libraryName })
            });
            
            if (!response.ok) {
                // Get detailed error message from response
                const errorData = await response.json().catch(() => ({ error: "Unknown error" }));
                throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            setNewLibraryName("");
            onLibrariesChanged();
            showMessage(`Library "${libraryName}" created successfully!`, MessageBarType.success);
        } catch (error) {
            console.error('Library creation error:', error);
            showMessage(`Failed to create library: ${error}`, MessageBarType.error);
        } finally {
            setIsProcessing(false);
        }
    };

    // Delete Library
    const handleDeleteLibrary = async () => {
        if (!selectedLibraryToDelete) return;
        
        if (!confirm(`Are you sure you want to delete "${selectedLibraryToDelete}"? This action cannot be undone.`)) {
            return;
        }

        setIsProcessing(true);
        try {
            const response = await fetch(`/libraries/${selectedLibraryToDelete}`, {
                method: "DELETE"
            });
            
            if (!response.ok) {
                throw new Error("Failed to delete library");
            }
            
            setSelectedLibraryToDelete("");
            onLibrariesChanged();
            showMessage(`Library "${selectedLibraryToDelete}" deleted successfully!`, MessageBarType.success);
        } catch (error) {
            showMessage(`Failed to delete library: ${error}`, MessageBarType.error);
        } finally {
            setIsProcessing(false);
        }
    };

    // Upload Videos - Now Async
    const handleUploadVideos = async () => {
        if (selectedFiles.length === 0 || !selectedUploadLibrary) return;

        setIsProcessing(true);
        try {
            let successCount = 0;
            let failCount = 0;

            for (let i = 0; i < selectedFiles.length; i++) {
                const file = selectedFiles[i];
                const formData = new FormData();
                formData.append('video', file);
                formData.append('library', selectedUploadLibrary);

                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData,
                    });

                    if (!response.ok) {
                        throw new Error(`Upload failed for ${file.name}`);
                    }

                    const result = await response.json();
                    
                    // Add task to tracking
                    addTask(result.task_id, file.name, selectedUploadLibrary);
                    successCount++;

                } catch (error) {
                    console.error(`Failed to upload ${file.name}:`, error);
                    failCount++;
                }
            }

            // Clear form
            setSelectedFiles([]);
            setSelectedUploadLibrary("");

            // Show summary message
            if (failCount === 0) {
                showMessage(`All ${successCount} videos queued for processing successfully!`, MessageBarType.success);
            } else if (successCount === 0) {
                showMessage(`Failed to queue ${failCount} videos`, MessageBarType.error);
            } else {
                showMessage(`${successCount} videos queued, ${failCount} failed to queue`, MessageBarType.warning);
            }

        } catch (error) {
            showMessage(`Error during upload: ${error}`, MessageBarType.error);
        } finally {
            setIsProcessing(false);
        }
    };

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const files = event.target.files;
        if (files && files.length > 0) {
            // Browser and practical limitations
            const MAX_FILES = 50; // Reasonable limit for browser memory
            const MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024; // 2GB per file
            const MAX_TOTAL_SIZE = 10 * 1024 * 1024 * 1024; // 10GB total
            
            if (files.length > MAX_FILES) {
                showMessage(`Too many files selected. Maximum ${MAX_FILES} files allowed at once.`, MessageBarType.warning);
                return;
            }
            
            const validFiles: File[] = [];
            let totalSize = 0;
            
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                
                // Check file format
                if (!(file.type.startsWith('video/') || file.name.match(/\.(mp4|mov|avi|mkv)$/i))) {
                    showMessage(`File "${file.name}" is not a supported video format.`, MessageBarType.warning);
                    continue;
                }
                
                // Check individual file size
                if (file.size > MAX_FILE_SIZE) {
                    showMessage(`File "${file.name}" exceeds 2GB limit (${(file.size / 1024 / 1024 / 1024).toFixed(2)}GB).`, MessageBarType.warning);
                    continue;
                }
                
                totalSize += file.size;
                validFiles.push(file);
            }
            
            // Check total size
            if (totalSize > MAX_TOTAL_SIZE) {
                showMessage(`Total file size exceeds 10GB limit (${(totalSize / 1024 / 1024 / 1024).toFixed(2)}GB). Please select fewer or smaller files.`, MessageBarType.warning);
                return;
            }
            
            if (validFiles.length > 0) {
                setSelectedFiles(validFiles);
                showMessage(`${validFiles.length} valid files selected (${(totalSize / 1024 / 1024).toFixed(2)} MB total).`, MessageBarType.success);
            } else {
                showMessage('No valid video files selected. Please choose .mp4, .mov, .avi, or .mkv files under 2GB each.', MessageBarType.warning);
            }
        }
    };

    return (
        <div className={styles.libraryManagementPanel}>
            {message && (
                <MessageBar 
                    messageBarType={message.type} 
                    onDismiss={() => setMessage(null)}
                    styles={{ root: { marginBottom: '16px' } }}
                >
                    {message.text}
                </MessageBar>
            )}
            
            {taskError && (
                <MessageBar 
                    messageBarType={MessageBarType.error} 
                    onDismiss={() => {/* Task error handling */}}
                    styles={{ root: { marginBottom: '16px' } }}
                >
                    Task Error: {taskError}
                </MessageBar>
            )}

            <Pivot
                selectedKey={activeTab}
                onLinkClick={(item) => item?.props.itemKey && setActiveTab(item.props.itemKey)}
                headersOnly={true}
                styles={{ root: { marginBottom: '20px' } }}
            >
                <PivotItem headerText="Upload Videos" itemKey="upload" itemIcon="Upload" />
                <PivotItem headerText="Manage Videos" itemKey="manage" itemIcon="Video" />
                <PivotItem headerText="Processing Status" itemKey="tasks" itemIcon="ProcessingRun" />
                <PivotItem headerText="Library Settings" itemKey="settings" itemIcon="Settings" />
            </Pivot>

            {activeTab === "upload" && (
                <div className={styles.tabContent}>
                    <Stack tokens={{ childrenGap: 20 }}>
                        {/* Create New Library Section */}
                        <div className={styles.actionCard}>
                            <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                                <h4>Create New Library</h4>
                            </Stack>
                            <Stack tokens={{ childrenGap: 12 }}>
                                <TextField
                                    placeholder="e.g., training-videos, product-demos"
                                    value={newLibraryName}
                                    onChange={(_, value) => setNewLibraryName(value || "")}
                                    description="Will be formatted as: vi-{name}-index"
                                />
                                <PrimaryButton
                                    text="Create Library"
                                    onClick={handleCreateLibrary}
                                    disabled={!newLibraryName.trim() || isProcessing}
                                    iconProps={{ iconName: "Add" }}
                                />
                            </Stack>
                        </div>

                        <Separator />

                        {/* Upload Video Section */}
                        <div className={styles.actionCard}>
                            <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                                <h4>Upload Video</h4>
                            </Stack>
                            <Stack tokens={{ childrenGap: 12 }}>
                                <div className={styles.fileUploadArea}>
                                    <input
                                        type="file"
                                        accept="video/*,.mp4,.mov,.avi,.mkv"
                                        onChange={handleFileChange}
                                        disabled={isProcessing}
                                        id="video-upload"
                                        className={styles.fileInput}
                                        multiple
                                    />
                                    <label htmlFor="video-upload" className={styles.fileLabel}>
                                        {selectedFiles.length > 0 ? (
                                            <div>
                                                <strong>Files selected: {selectedFiles.length}</strong>
                                                <br />
                                                <small>
                                                    {selectedFiles.map(f => f.name).join(', ')}
                                                </small>
                                                <br />
                                                <small>
                                                    Total: {(selectedFiles.reduce((sum, f) => sum + f.size, 0) / 1024 / 1024).toFixed(2)} MB
                                                </small>
                                            </div>
                                        ) : (
                                            <div>
                                                <strong>Click to select video files</strong>
                                                <br />
                                                <small>Supports: MP4, MOV, AVI, MKV (Multiple files allowed)</small>
                                            </div>
                                        )}
                                    </label>
                                </div>

                                <Dropdown
                                    placeholder="Select destination library"
                                    options={indexes}
                                    onChange={(_, item) => setSelectedUploadLibrary(item?.key as string || "")}
                                    disabled={isProcessing}
                                />

                                <PrimaryButton
                                    text={isProcessing ? "Queuing..." : `Queue ${selectedFiles.length} Video(s)`}
                                    onClick={handleUploadVideos}
                                    disabled={selectedFiles.length === 0 || !selectedUploadLibrary || isProcessing}
                                    iconProps={{ iconName: isProcessing ? "Clock" : "Upload" }}
                                />
                            </Stack>
                        </div>
                    </Stack>
                </div>
            )}

            {activeTab === "manage" && (
                <div className={styles.tabContent}>
                    <Stack tokens={{ childrenGap: 16 }}>
                        <div className={styles.actionCard}>
                            <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                                <h4>Video Management</h4>
                            </Stack>
                            <Stack tokens={{ childrenGap: 12 }}>
                                <Dropdown
                                    placeholder="Select library to manage"
                                    options={indexes}
                                    onChange={(_, item) => setSelectedManageLibrary(item?.key as string || "")}
                                />
                            </Stack>
                        </div>
                        
                        {selectedManageLibrary && (
                            <VideoList 
                                libraryName={selectedManageLibrary}
                                onVideoDeleted={(videoIds) => {
                                    showMessage(`${videoIds.length} video(s) deletion started`, MessageBarType.info);
                                }}
                            />
                        )}
                    </Stack>
                </div>
            )}

            {activeTab === "tasks" && (
                <div className={styles.tabContent}>
                    <div className={styles.taskStatusSection}>
                        <Stack horizontal horizontalAlign="space-between" verticalAlign="center" tokens={{ childrenGap: 8 }}>
                            <h4>Processing Status ({tasks.length})</h4>
                            <div>
                                <DefaultButton 
                                    text="Clear All" 
                                    onClick={clearAllTasks}
                                    iconProps={{ iconName: 'ClearSelection' }}
                                    styles={{ root: { minWidth: 'auto', marginRight: 8 } }}
                                />
                                <DefaultButton 
                                    text="Clear Completed" 
                                    onClick={clearCompletedTasks}
                                    iconProps={{ iconName: 'Clear' }}
                                    styles={{ root: { minWidth: 'auto' } }}
                                />
                            </div>
                        </Stack>
                        
                        <div className={styles.taskList}>
                            {tasks.map(task => (
                                <TaskProgressCard 
                                    key={task.task_id}
                                    task={task}
                                    onRemove={() => removeTask(task.task_id)}
                                    onCancel={() => cancelTask(task.task_id)}
                                />
                            ))}
                        </div>
                        
                        {tasks.length === 0 && (
                            <div style={{ padding: '40px 20px', textAlign: 'center', color: '#605e5c' }}>
                                No active tasks. Upload videos to see processing status here.
                            </div>
                        )}
                    </div>
                </div>
            )}

            {activeTab === "settings" && (
                <div className={styles.tabContent}>
                    <Stack tokens={{ childrenGap: 20 }}>
                        {/* Delete Library Section */}
                        <div className={styles.actionCard}>
                            <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                                <h4>Delete Library</h4>
                            </Stack>
                            <Stack tokens={{ childrenGap: 12 }}>
                                <Dropdown
                                    placeholder="Choose library to delete"
                                    options={indexes}
                                    onChange={(_, item) => setSelectedLibraryToDelete(item?.key as string || "")}
                                    disabled={isProcessing}
                                />
                                <DefaultButton
                                    text="Delete Library"
                                    onClick={handleDeleteLibrary}
                                    disabled={!selectedLibraryToDelete || isProcessing}
                                    iconProps={{ iconName: "Delete" }}
                                    styles={{ 
                                        root: { 
                                            borderColor: '#d13438',
                                            color: '#d13438'
                                        },
                                        rootHovered: {
                                            backgroundColor: '#d13438',
                                            color: 'white'
                                        }
                                    }}
                                />
                            </Stack>
                        </div>

                        <Separator />

                        {/* Current Libraries Overview */}
                        <div className={styles.actionCard}>
                            <h4>Current Libraries ({indexes.length})</h4>
                            <div className={styles.librariesGrid}>
                                {indexes.length === 0 ? (
                                    <div className={styles.emptyState}>
                                        <p>No libraries found. Create your first library above!</p>
                                    </div>
                                ) : (
                                    indexes.map(lib => (
                                        <div key={lib.key} className={styles.libraryCard}>
                                            <div className={styles.libraryIcon}>Library</div>
                                            <div className={styles.libraryInfo}>
                                                <strong title={lib.text}>{lib.text}</strong>
                                                <small title={lib.key as string}>{lib.key}</small>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    </Stack>
                </div>
            )}
        </div>
    );
};
