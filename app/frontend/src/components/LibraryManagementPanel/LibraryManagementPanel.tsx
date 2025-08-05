import { useState } from "react";
import { TextField, PrimaryButton, DefaultButton, Dropdown, MessageBar, MessageBarType, Stack, Separator, IDropdownOption } from "@fluentui/react";
import styles from "./LibraryManagementPanel.module.css";

interface LibraryManagementPanelProps {
    indexes: IDropdownOption[];
    onLibrariesChanged: () => void;
}

export const LibraryManagementPanel = ({ indexes, onLibrariesChanged }: LibraryManagementPanelProps) => {
    const [newLibraryName, setNewLibraryName] = useState("");
    const [selectedLibraryToDelete, setSelectedLibraryToDelete] = useState("");
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [selectedUploadLibrary, setSelectedUploadLibrary] = useState("");
    const [isProcessing, setIsProcessing] = useState(false);
    const [message, setMessage] = useState<{ text: string; type: MessageBarType } | null>(null);

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
                throw new Error("Failed to create library");
            }
            
            setNewLibraryName("");
            onLibrariesChanged();
            showMessage(`Library "${libraryName}" created successfully!`, MessageBarType.success);
        } catch (error) {
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

    // Upload Videos
    const handleUploadVideos = async () => {
        if (selectedFiles.length === 0 || !selectedUploadLibrary) return;

        setIsProcessing(true);
        try {
            for (let i = 0; i < selectedFiles.length; i++) {
                const file = selectedFiles[i];
                const formData = new FormData();
                formData.append('video', file);
                formData.append('library', selectedUploadLibrary);

                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData,
                });

                if (!response.ok) {
                    throw new Error(`Upload failed for ${file.name}`);
                }

                showMessage(`Video ${i + 1}/${selectedFiles.length}: "${file.name}" uploaded successfully!`, MessageBarType.success);
            }

            setSelectedFiles([]);
            setSelectedUploadLibrary("");
            showMessage(`All ${selectedFiles.length} videos uploaded successfully!`, MessageBarType.success);
        } catch (error) {
            showMessage(`Failed to upload videos: ${error}`, MessageBarType.error);
        } finally {
            setIsProcessing(false);
        }
    };

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const files = event.target.files;
        if (files && files.length > 0) {
            const validFiles: File[] = [];
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                if (file.type.startsWith('video/') || file.name.match(/\.(mp4|mov|avi|mkv)$/i)) {
                    validFiles.push(file);
                }
            }
            
            if (validFiles.length > 0) {
                setSelectedFiles(validFiles);
            } else {
                showMessage('Please select valid video files (.mp4, .mov, .avi, .mkv)', MessageBarType.warning);
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
                            text={isProcessing ? "Uploading..." : `Upload ${selectedFiles.length} Video(s)`}
                            onClick={handleUploadVideos}
                            disabled={selectedFiles.length === 0 || !selectedUploadLibrary || isProcessing}
                            iconProps={{ iconName: "Upload" }}
                        />
                    </Stack>
                </div>

                <Separator />

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
    );
};
