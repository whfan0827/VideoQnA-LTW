import { useState, useEffect } from "react";
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
import { LibraryList } from "../LibraryList";
import { UploadModeSelector } from "../UploadModeSelector";
import { BlobStorageBrowser } from "../BlobStorageBrowser";

interface LibraryManagementPanelProps {
    indexes: IDropdownOption[];
    onLibrariesChanged: () => void;
}

export const LibraryManagementPanel = ({ indexes, onLibrariesChanged }: LibraryManagementPanelProps) => {
    const [activeTab, setActiveTab] = useState(() => {
        return localStorage.getItem('libraryManagement_activeTab') || "upload";
    });
    const [newLibraryName, setNewLibraryName] = useState("");
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [selectedUploadLibrary, setSelectedUploadLibrary] = useState(() => {
        return localStorage.getItem('libraryManagement_selectedUploadLibrary') || "";
    });
    const [uploadMode, setUploadMode] = useState<'file' | 'url'>('file');
    const [sourceType, setSourceType] = useState<'local' | 'blob'>('local');
    const [videoUrls, setVideoUrls] = useState<string>('');
    const [uploadLanguage, setUploadLanguage] = useState<string>('auto');
    const [selectedBlobs, setSelectedBlobs] = useState<any[]>([]);
    const [selectedManageLibrary, setSelectedManageLibrary] = useState(() => {
        return localStorage.getItem('libraryManagement_selectedManageLibrary') || "";
    });
    const [isProcessing, setIsProcessing] = useState(false);
    const [message, setMessage] = useState<{ text: string; type: MessageBarType } | null>(null);
    
    // Logs state
    const [logs, setLogs] = useState<string[]>([]);
    const [tasksHistory, setTasksHistory] = useState<any[]>([]);
    const [logsLoading, setLogsLoading] = useState(false);
    const [logFilter, setLogFilter] = useState({
        type: 'app',
        lines: 100,
        statusFilter: '',
        days: 7
    });
    
    // Task management
    const { tasks, addTask, removeTask, clearCompletedTasks, clearAllTasks, cancelTask, forceRefresh, isPolling, isManualRefreshing, error: taskError } = useTaskManager();

    // Persist state to localStorage
    useEffect(() => {
        localStorage.setItem('libraryManagement_activeTab', activeTab);
    }, [activeTab]);


    useEffect(() => {
        if (selectedUploadLibrary) {
            localStorage.setItem('libraryManagement_selectedUploadLibrary', selectedUploadLibrary);
        } else {
            localStorage.removeItem('libraryManagement_selectedUploadLibrary');
        }
    }, [selectedUploadLibrary]);

    useEffect(() => {
        if (selectedManageLibrary) {
            localStorage.setItem('libraryManagement_selectedManageLibrary', selectedManageLibrary);
        } else {
            localStorage.removeItem('libraryManagement_selectedManageLibrary');
        }
    }, [selectedManageLibrary]);

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


    // Upload Videos - Now supports both file and URL upload
    const handleUploadVideos = async () => {
        // Check if we have items to process based on source type and upload mode
        let hasItems = false;
        if (sourceType === 'local') {
            hasItems = uploadMode === 'file' ? selectedFiles.length > 0 : videoUrls.trim().length > 0;
        } else if (sourceType === 'blob') {
            hasItems = selectedBlobs.length > 0;
        }
        
        if (!hasItems || !selectedUploadLibrary) return;

        // Debug: show current language state before upload
        console.log(`[DEBUG] Starting upload with language: ${uploadLanguage}`);

        setIsProcessing(true);
        try {
            let successCount = 0;
            let failCount = 0;

            if (sourceType === 'local') {
                if (uploadMode === 'file') {
                    // Handle local file uploads
                    for (let i = 0; i < selectedFiles.length; i++) {
                        const file = selectedFiles[i];
                        
                        // Check file size before upload
                        if (file.size > 2 * 1024 * 1024 * 1024) {
                            showMessage(`File ${file.name} is too large (${(file.size / 1024 / 1024 / 1024).toFixed(1)}GB). Use URL upload for files > 2GB.`, MessageBarType.error);
                            failCount++;
                            continue;
                        }
                        
                        const formData = new FormData();
                        formData.append('video', file);
                        formData.append('library', selectedUploadLibrary);
                        formData.append('source_language', uploadLanguage);
                        
                        // Debug logging
                        console.log(`[DEBUG] Uploading ${file.name} with language: ${uploadLanguage}`);

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
                    
                    // Clear selected files after processing
                    setSelectedFiles([]);
                } else {
                    // Handle URL uploads
                    const urls = videoUrls.split('\n').filter(url => url.trim());
                    
                    for (let i = 0; i < urls.length; i++) {
                        const url = urls[i].trim();
                        const videoName = url.split('/').pop() || `video_${i + 1}`;
                        
                        try {
                            // Debug logging
                            console.log(`[DEBUG] Uploading URL ${url} with language: ${uploadLanguage}`);
                            
                            const response = await fetch('/upload', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({
                                    video_url: url,
                                    library: selectedUploadLibrary,
                                    video_name: videoName,
                                    source_language: uploadLanguage
                                }),
                            });

                            if (!response.ok) {
                                throw new Error(`URL upload failed for ${url}`);
                            }

                            const result = await response.json();
                            
                            // Add task to tracking
                            addTask(result.task_id, videoName, selectedUploadLibrary);
                            successCount++;

                        } catch (error) {
                            console.error(`Failed to upload URL ${url}:`, error);
                            failCount++;
                        }
                    }
                    
                    // Clear URLs after processing
                    setVideoUrls('');
                }
            } else if (sourceType === 'blob') {
                // Handle blob storage imports
                try {
                    // Generate SAS URLs for selected blobs and import them
                    const sasUrls = [];
                    for (const blob of selectedBlobs) {
                        try {
                            const response = await fetch('/blob-storage/generate-sas', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({
                                    container_name: blob.container,
                                    blob_name: blob.name,
                                    expiry_hours: 24
                                }),
                            });

                            if (response.ok) {
                                const result = await response.json();
                                sasUrls.push(result.sas_url);
                            } else {
                                console.error(`Failed to generate SAS URL for ${blob.name}`);
                                failCount++;
                            }
                        } catch (error) {
                            console.error(`Error generating SAS URL for ${blob.name}:`, error);
                            failCount++;
                        }
                    }

                    // Import blobs using the import API endpoint
                    if (sasUrls.length > 0) {
                        for (let i = 0; i < sasUrls.length; i++) {
                            const sasUrl = sasUrls[i];
                            const blob = selectedBlobs[i];
                            const filename = blob.name.split('/').pop() || blob.name;

                            try {
                                // Debug logging
                                console.log(`[DEBUG] Importing blob ${filename} with language: ${uploadLanguage}`);
                                
                                const response = await fetch(`/libraries/${selectedUploadLibrary}/import-from-blob`, {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json',
                                    },
                                    body: JSON.stringify({
                                        blob_url: sasUrl,
                                        source_language: uploadLanguage
                                    }),
                                });

                                if (!response.ok) {
                                    throw new Error(`Import failed for ${filename}`);
                                }

                                const result = await response.json();
                                
                                // Add tasks to tracking
                                for (const taskId of result.task_ids) {
                                    addTask(taskId, filename, selectedUploadLibrary);
                                }
                                successCount++;

                            } catch (error) {
                                console.error(`Failed to import ${filename}:`, error);
                                failCount++;
                            }
                        }
                    }
                    
                    // Clear selected blobs after processing
                    setSelectedBlobs([]);
                } catch (error) {
                    console.error('Error during blob import:', error);
                    showMessage(`Error during blob import: ${error}`, MessageBarType.error);
                    failCount = selectedBlobs.length;
                }
            }

            // Clear library selection if desired
            // setSelectedUploadLibrary("");

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

    // Logs functions
    const fetchLogs = async () => {
        setLogsLoading(true);
        try {
            const response = await fetch(`/api/system/logs?type=${logFilter.type}&lines=${logFilter.lines}`);
            if (response.ok) {
                const data = await response.json();
                setLogs(data.logs || []);
                showMessage(`Loaded ${data.showing} log lines (${data.total_lines} total)`, MessageBarType.success);
            } else {
                throw new Error('Failed to fetch logs');
            }
        } catch (error) {
            showMessage(`Failed to load logs: ${error}`, MessageBarType.error);
        } finally {
            setLogsLoading(false);
        }
    };

    const fetchTasksHistory = async () => {
        setLogsLoading(true);
        try {
            const params = new URLSearchParams({
                days: logFilter.days.toString(),
                limit: '50'
            });
            if (logFilter.statusFilter) {
                params.append('status', logFilter.statusFilter);
            }

            const response = await fetch(`/api/system/tasks-history?${params}`);
            if (response.ok) {
                const data = await response.json();
                setTasksHistory(data.tasks || []);
                showMessage(`Loaded ${data.showing} task records (${data.total_found} total)`, MessageBarType.success);
            } else {
                throw new Error('Failed to fetch tasks history');
            }
        } catch (error) {
            showMessage(`Failed to load task history: ${error}`, MessageBarType.error);
        } finally {
            setLogsLoading(false);
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
                <PivotItem headerText="System Logs" itemKey="logs" itemIcon="FileCode" />
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
                            <UploadModeSelector
                                selectedMode={sourceType}
                                onModeChange={setSourceType}
                            />
                            
                            {sourceType === 'local' && (
                                <Stack tokens={{ childrenGap: 12 }} style={{ marginTop: 20 }}>
                                    {/* Upload Method Selection for Local Files */}
                                    <Dropdown
                                        label="Upload Method"
                                        options={[
                                            { key: 'file', text: 'File Upload (<2GB each)' },
                                            { key: 'url', text: 'URL Upload (<30GB each)' }
                                        ]}
                                        selectedKey={uploadMode}
                                        onChange={(_, item) => setUploadMode(item?.key as 'file' | 'url')}
                                        disabled={isProcessing}
                                    />
                                    
                                    <Dropdown
                                        label="Video Language (for subtitle generation)"
                                        options={[
                                            { key: 'auto', text: '🌐 Auto-detect' },
                                            { key: 'de-DE', text: '🇩🇪 Deutsch (German)' },
                                            { key: 'en-US', text: '🇺🇸 English (US)' },
                                            { key: 'es-ES', text: '🇪🇸 Español (Spanish)' },
                                            { key: 'fr-FR', text: '🇫🇷 Français (French)' },
                                            { key: 'it-IT', text: '🇮🇹 Italiano (Italian)' },
                                            { key: 'ja-JP', text: '🇯🇵 日本語 (Japanese)' },
                                            { key: 'zh-Hans', text: '🇨🇳 简体中文 (Simplified Chinese)' },
                                            { key: 'zh-Hant', text: '🇹🇼 繁體中文 (Traditional Chinese - Mandarin)' },
                                            { key: 'zh-HK', text: '🇭🇰 廣東話 (Cantonese)' },
                                            { key: 'vi-VN', text: '🇻🇳 Tiếng Việt (Vietnamese)' }
                                        ]}
                                        selectedKey={uploadLanguage}
                                        onChange={(_, item) => {
                                            const newLanguage = item?.key as string || 'auto';
                                            console.log(`[DEBUG] Language changed to: ${newLanguage}`);
                                            setUploadLanguage(newLanguage);
                                        }}
                                        disabled={isProcessing}
                                        styles={{ root: { marginTop: 8 } }}
                                    />
                                    
                                    {uploadMode === 'file' ? (
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
                                                            {selectedFiles.some(f => f.size > 2 * 1024 * 1024 * 1024) && (
                                                                <span style={{ color: 'red' }}> (Some files &gt; 2GB - use URL upload)</span>
                                                            )}
                                                        </small>
                                                    </div>
                                                ) : (
                                                    <div>
                                                        <strong>Click to select video files</strong>
                                                        <br />
                                                        <small>Supports: MP4, MOV, AVI, MKV (Max 2GB each, Multiple files allowed)</small>
                                                    </div>
                                                )}
                                            </label>
                                        </div>
                                    ) : (
                                        <TextField
                                            label="Video URLs"
                                            placeholder="Enter video URLs, one per line"
                                            multiline
                                            rows={4}
                                            value={videoUrls}
                                            onChange={(_, value) => setVideoUrls(value || '')}
                                            disabled={isProcessing}
                                            description="Enter direct video file URLs (up to 30GB each). One URL per line."
                                        />
                                    )}
                                </Stack>
                            )}
                            
                            {sourceType === 'blob' && (
                                <Stack tokens={{ childrenGap: 12 }} style={{ marginTop: 20 }}>
                                    <Dropdown
                                        label="Video Language (for subtitle generation)"
                                        options={[
                                            { key: 'auto', text: '🌐 Auto-detect' },
                                            { key: 'de-DE', text: '🇩🇪 Deutsch (German)' },
                                            { key: 'en-US', text: '🇺🇸 English (US)' },
                                            { key: 'es-ES', text: '🇪🇸 Español (Spanish)' },
                                            { key: 'fr-FR', text: '🇫🇷 Français (French)' },
                                            { key: 'it-IT', text: '🇮🇹 Italiano (Italian)' },
                                            { key: 'ja-JP', text: '🇯🇵 日本語 (Japanese)' },
                                            { key: 'zh-Hans', text: '🇨🇳 简体中文 (Simplified Chinese)' },
                                            { key: 'zh-Hant', text: '🇹🇼 繁體中文 (Traditional Chinese - Mandarin)' },
                                            { key: 'zh-HK', text: '🇭🇰 廣東話 (Cantonese)' },
                                            { key: 'vi-VN', text: '🇻🇳 Tiếng Việt (Vietnamese)' }
                                        ]}
                                        selectedKey={uploadLanguage}
                                        onChange={(_, item) => {
                                            const newLanguage = item?.key as string || 'auto';
                                            console.log(`[DEBUG] Blob import language changed to: ${newLanguage}`);
                                            setUploadLanguage(newLanguage);
                                        }}
                                        disabled={isProcessing}
                                        styles={{ root: { marginTop: 8 } }}
                                    />
                                    <BlobStorageBrowser
                                        onSelectionChange={setSelectedBlobs}
                                        multiSelect={true}
                                    />
                                </Stack>
                            )}

                            <Stack tokens={{ childrenGap: 12 }} style={{ marginTop: 20 }}>
                                <Dropdown
                                    placeholder="Select destination library"
                                    options={indexes}
                                    selectedKey={selectedUploadLibrary}
                                    onChange={(_, item) => setSelectedUploadLibrary(item?.key as string || "")}
                                    disabled={isProcessing}
                                />

                                <PrimaryButton
                                    text={
                                        isProcessing 
                                            ? "Processing..." 
                                            : sourceType === 'local'
                                                ? (uploadMode === 'file' 
                                                    ? `Queue ${selectedFiles.length} Video(s)` 
                                                    : `Queue ${videoUrls.split('\n').filter(url => url.trim()).length} URL(s)`)
                                                : `Import ${selectedBlobs.length} Video(s) from Blob Storage`
                                    }
                                    onClick={handleUploadVideos}
                                    disabled={
                                        isProcessing || 
                                        !selectedUploadLibrary || 
                                        (sourceType === 'local' 
                                            ? (uploadMode === 'file' ? selectedFiles.length === 0 : !videoUrls.trim())
                                            : selectedBlobs.length === 0)
                                    }
                                    iconProps={{ iconName: isProcessing ? "Clock" : (sourceType === 'blob' ? "CloudUpload" : "Upload") }}
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
                                    selectedKey={selectedManageLibrary}
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
                            <div>
                                <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                                    <h4>Processing Status ({tasks.length})</h4>
                                    {(isPolling || isManualRefreshing) && (
                                        <div style={{ display: 'flex', alignItems: 'center', fontSize: '12px', color: '#0078d4' }}>
                                            <i 
                                                className="ms-Icon ms-Icon--Sync" 
                                                style={{ 
                                                    fontSize: '12px', 
                                                    marginRight: '4px',
                                                    animation: 'spin 1s linear infinite'
                                                }}
                                            />
                                            {isManualRefreshing ? 'Refreshing...' : 'Auto-updating'}
                                        </div>
                                    )}
                                </Stack>
                                <small style={{ color: '#605e5c' }}>
                                    {(() => {
                                        const pending = tasks.filter(t => t.status === 'pending').length;
                                        const processing = tasks.filter(t => t.status === 'processing').length;
                                        const completed = tasks.filter(t => t.status === 'completed').length;
                                        const failed = tasks.filter(t => t.status === 'failed').length;
                                        const cancelled = tasks.filter(t => t.status === 'cancelled').length;
                                        const activeTasks = pending + processing;
                                        const statusText = `Active: ${activeTasks}, Completed: ${completed}, Failed: ${failed}, Cancelled: ${cancelled}`;
                                        const pollText = activeTasks > 0 ? ' • Auto-refresh every 10s' : '';
                                        return statusText + pollText;
                                    })()}
                                </small>
                            </div>
                            <div>
                                <DefaultButton 
                                    text={isManualRefreshing ? "Refreshing..." : "Refresh Status"} 
                                    onClick={forceRefresh}
                                    disabled={isManualRefreshing}
                                    iconProps={{ iconName: isManualRefreshing ? 'Sync' : 'Refresh' }}
                                    styles={{ root: { minWidth: 'auto', marginRight: 8 } }}
                                />
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

            {activeTab === "logs" && (
                <div className={styles.tabContent}>
                    <Stack tokens={{ childrenGap: 16 }}>
                        <div className={styles.actionCard}>
                            <h4>System Logs and Task History</h4>
                            <Stack tokens={{ childrenGap: 12 }}>
                                <Stack horizontal tokens={{ childrenGap: 12 }} verticalAlign="end">
                                    <Dropdown
                                        label="Log Type"
                                        options={[
                                            { key: 'app', text: 'Application Logs' },
                                            { key: 'tasks', text: 'Task History' }
                                        ]}
                                        selectedKey={logFilter.type}
                                        onChange={(_, item) => setLogFilter({...logFilter, type: item?.key as string})}
                                        styles={{ root: { width: 150 } }}
                                    />
                                    
                                    {logFilter.type === 'app' ? (
                                        <TextField
                                            label="Number of Lines"
                                            type="number"
                                            value={logFilter.lines.toString()}
                                            onChange={(_, value) => setLogFilter({...logFilter, lines: parseInt(value || '100')})}
                                            styles={{ root: { width: 120 } }}
                                        />
                                    ) : (
                                        <>
                                            <TextField
                                                label="Days to Show"
                                                type="number"
                                                value={logFilter.days.toString()}
                                                onChange={(_, value) => setLogFilter({...logFilter, days: parseInt(value || '7')})}
                                                styles={{ root: { width: 100 } }}
                                            />
                                            <Dropdown
                                                label="Status Filter"
                                                options={[
                                                    { key: '', text: 'All' },
                                                    { key: 'completed', text: 'Completed' },
                                                    { key: 'failed', text: 'Failed' },
                                                    { key: 'cancelled', text: 'Cancelled' },
                                                    { key: 'pending', text: 'Pending' },
                                                    { key: 'processing', text: 'Processing' }
                                                ]}
                                                selectedKey={logFilter.statusFilter}
                                                onChange={(_, item) => setLogFilter({...logFilter, statusFilter: item?.key as string})}
                                                styles={{ root: { width: 130 } }}
                                            />
                                        </>
                                    )}
                                    
                                    <PrimaryButton
                                        text={logsLoading ? "Loading..." : logFilter.type === 'app' ? "Load Logs" : "Load Task History"}
                                        onClick={logFilter.type === 'app' ? fetchLogs : fetchTasksHistory}
                                        disabled={logsLoading}
                                        iconProps={{ iconName: logsLoading ? "Clock" : "Refresh" }}
                                        styles={{ root: { minWidth: 120 } }}
                                    />
                                </Stack>
                            </Stack>
                        </div>

                        {logFilter.type === 'app' && logs.length > 0 && (
                            <div className={styles.actionCard}>
                                <h5>Application Logs</h5>
                                <div style={{ 
                                    maxHeight: '400px', 
                                    overflow: 'auto', 
                                    backgroundColor: '#f8f9fa', 
                                    padding: '12px', 
                                    borderRadius: '4px',
                                    fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                                    fontSize: '12px'
                                }}>
                                    {logs.map((line, index) => (
                                        <div key={index} style={{ 
                                            marginBottom: '2px',
                                            color: line.includes('ERROR') ? '#d32f2f' : 
                                                   line.includes('WARNING') ? '#f57c00' : 
                                                   line.includes('INFO') ? '#1976d2' : '#666'
                                        }}>
                                            {line}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {logFilter.type === 'tasks' && tasksHistory.length > 0 && (
                            <div className={styles.actionCard}>
                                <h5>Task History</h5>
                                <div style={{ maxHeight: '400px', overflow: 'auto' }}>
                                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                                        <thead>
                                            <tr style={{ backgroundColor: '#f1f3f4' }}>
                                                <th style={{ padding: '8px', textAlign: 'left', border: '1px solid #e1e5e9' }}>Task ID</th>
                                                <th style={{ padding: '8px', textAlign: 'left', border: '1px solid #e1e5e9' }}>Filename</th>
                                                <th style={{ padding: '8px', textAlign: 'left', border: '1px solid #e1e5e9' }}>Status</th>
                                                <th style={{ padding: '8px', textAlign: 'left', border: '1px solid #e1e5e9' }}>Progress</th>
                                                <th style={{ padding: '8px', textAlign: 'left', border: '1px solid #e1e5e9' }}>Created</th>
                                                <th style={{ padding: '8px', textAlign: 'left', border: '1px solid #e1e5e9' }}>Completed</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {tasksHistory.map((task, index) => (
                                                <tr key={index} style={{ 
                                                    backgroundColor: index % 2 === 0 ? '#fff' : '#f8f9fa',
                                                    color: task.status === 'completed' ? '#2e7d32' :
                                                           task.status === 'failed' ? '#d32f2f' :
                                                           task.status === 'cancelled' ? '#f57c00' : '#1976d2'
                                                }}>
                                                    <td style={{ padding: '8px', border: '1px solid #e1e5e9' }}>
                                                        <small>{task.task_id?.substring(0, 8)}...</small>
                                                    </td>
                                                    <td style={{ padding: '8px', border: '1px solid #e1e5e9' }}>
                                                        {task.filename}
                                                    </td>
                                                    <td style={{ padding: '8px', border: '1px solid #e1e5e9' }}>
                                                        <strong>{task.status}</strong>
                                                    </td>
                                                    <td style={{ padding: '8px', border: '1px solid #e1e5e9' }}>
                                                        {task.progress}%
                                                    </td>
                                                    <td style={{ padding: '8px', border: '1px solid #e1e5e9' }}>
                                                        <small>{new Date(task.created_at).toLocaleString()}</small>
                                                    </td>
                                                    <td style={{ padding: '8px', border: '1px solid #e1e5e9' }}>
                                                        <small>{task.completed_at ? new Date(task.completed_at).toLocaleString() : '-'}</small>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}

                        {((logFilter.type === 'app' && logs.length === 0) || 
                          (logFilter.type === 'tasks' && tasksHistory.length === 0)) && !logsLoading && (
                            <div style={{ padding: '40px 20px', textAlign: 'center', color: '#605e5c' }}>
                                {logFilter.type === 'app' ? 'No log records. Click "Load Logs" to view system logs.' : 'No task history records.'}
                            </div>
                        )}
                    </Stack>
                </div>
            )}

            {activeTab === "settings" && (
                <div className={styles.tabContent}>
                    <div className={styles.actionCard}>
                        <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                            <h4>Library Management ({indexes.length})</h4>
                        </Stack>
                        <p style={{ color: '#605e5c', marginBottom: 16 }}>
                            Manage your video libraries. Select libraries using checkboxes to perform batch operations.
                        </p>
                        <LibraryList 
                            libraries={indexes}
                            onLibrariesChanged={onLibrariesChanged}
                            isProcessing={isProcessing}
                        />
                    </div>
                </div>
            )}
        </div>
    );
};
