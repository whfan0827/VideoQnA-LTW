import React, { useState, useEffect } from 'react';
import { 
    DetailsList, 
    IColumn, 
    SelectionMode, 
    Selection,
    CommandBar,
    ICommandBarItemProps,
    MessageBar,
    MessageBarType,
    Dialog,
    DialogType,
    DialogFooter,
    PrimaryButton,
    DefaultButton,
    Spinner,
    SpinnerSize,
    Dropdown,
    IDropdownOption,
    TooltipHost
} from '@fluentui/react';

interface VideoItem {
    id: number;
    filename: string;
    video_id?: string;
    file_size?: number;
    duration?: string;
    status: string;
    created_at: string;
    updated_at: string;
    source_type?: string;
    blob_url?: string;
    blob_container?: string;
    source_language?: string;
}

interface VideoListProps {
    libraryName: string;
    onVideoDeleted?: (videoIds: string[]) => void;
}

const VideoList: React.FC<VideoListProps> = ({ libraryName, onVideoDeleted }) => {
    const [videos, setVideos] = useState<VideoItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [deleteDialogVisible, setDeleteDialogVisible] = useState(false);
    const [deleting, setDeleting] = useState(false);
    const [selectedCount, setSelectedCount] = useState(0);
    const [cleanupDialogVisible, setCleanupDialogVisible] = useState(false);
    const [cleanupInProgress, setCleanupInProgress] = useState(false);
    const [cleanupResult, setCleanupResult] = useState<any>(null);
    const [exportPanelVisible, setExportPanelVisible] = useState<string | null>(null); // video_id for which panel is open
    const [selection] = useState(new Selection({
        onSelectionChanged: () => {
            // Force component re-render by updating selection count
            setSelectedCount(selection.getSelectedCount());
        },
    }));

    // Load videos for the library
    useEffect(() => {
        loadVideos();
    }, [libraryName]);

    const loadVideos = async () => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await fetch(`/libraries/${libraryName}/videos`);
            if (response.ok) {
                const data = await response.json();
                setVideos(data.videos || []);
                // Clear selection when data is reloaded
                selection.setAllSelected(false);
                setSelectedCount(0);
            } else {
                const errorData = await response.json();
                setError(errorData.error || 'Failed to load videos');
            }
        } catch (err) {
            setError('Network error while loading videos');
            console.error('Error loading videos:', err);
        } finally {
            setLoading(false);
        }
    };

    const formatFileSize = (bytes?: number) => {
        if (!bytes) return 'Unknown';
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return `${Math.round(bytes / Math.pow(1024, i) * 100) / 100} ${sizes[i]}`;
    };

    const formatDate = (dateString: string) => {
        if (!dateString || dateString === 'null' || dateString === 'undefined') {
            return '-';
        }
        
        const date = new Date(dateString);
        
        // Check if the date is valid
        if (isNaN(date.getTime())) {
            return '-';
        }
        
        // Check if it's the Unix epoch (1970-01-01)
        if (date.getTime() === 0) {
            return '-';
        }
        
        return date.toLocaleString();
    };

    const formatLanguage = (languageCode?: string) => {
        if (!languageCode || languageCode === 'auto') {
            return '🌐 Auto';
        }
        
        const languageMap: { [key: string]: string } = {
            'de-DE': '🇩🇪 Deutsch',
            'en-US': '🇺🇸 English',
            'es-ES': '🇪🇸 Español',
            'fr-FR': '🇫🇷 Français', 
            'it-IT': '🇮🇹 Italiano',
            'ja-JP': '🇯🇵 日本語',
            'zh-Hans': '🇨🇳 简体中文',
            'zh-Hant': '🇹🇼 繁體中文',
            'zh-HK': '🇭🇰 粵語',
            'vi-VN': '🇻🇳 Tiếng Việt'
        };
        
        return languageMap[languageCode] || languageCode;
    };

    const columns: IColumn[] = [
        {
            key: 'video_id',
            name: 'Video ID',
            fieldName: 'video_id',
            minWidth: 120,
            maxWidth: 150,
            isResizable: true,
            onRender: (item: VideoItem) => (
                <span 
                    title={item.video_id || 'No Video ID'}
                    style={{ 
                        fontFamily: 'monospace', 
                        fontSize: '12px',
                        color: item.video_id ? '#0078d4' : '#a19f9d'
                    }}
                >
                    {item.video_id || 'N/A'}
                </span>
            )
        },
        {
            key: 'filename',
            name: 'Filename',
            fieldName: 'filename',
            minWidth: 180,
            maxWidth: 280,
            isResizable: true,
            onRender: (item: VideoItem) => (
                <div>
                    <span title={item.filename}>{item.filename}</span>
                </div>
            )
        },
        {
            key: 'file_size',
            name: 'Size',
            fieldName: 'file_size',
            minWidth: 80,
            maxWidth: 120,
            isResizable: true,
            onRender: (item: VideoItem) => formatFileSize(item.file_size)
        },
        {
            key: 'source_language',
            name: 'Language',
            fieldName: 'source_language',
            minWidth: 100,
            maxWidth: 140,
            isResizable: true,
            onRender: (item: VideoItem) => (
                <span style={{ 
                    fontSize: '12px',
                    fontWeight: 500
                }}>
                    {formatLanguage(item.source_language)}
                </span>
            )
        },
        {
            key: 'source_type',
            name: 'Source',
            fieldName: 'source_type',
            minWidth: 80,
            maxWidth: 120,
            isResizable: true,
            onRender: (item: VideoItem) => (
                <span style={{ 
                    color: item.source_type === 'blob_storage' ? '#0078d4' : '#605e5c',
                    fontWeight: 500
                }}>
                    {item.source_type === 'blob_storage' ? 'Blob Storage' : 'Local File'}
                </span>
            )
        },
        {
            key: 'status',
            name: 'Status',
            fieldName: 'status',
            minWidth: 80,
            maxWidth: 100,
            isResizable: true,
            onRender: (item: VideoItem) => (
                <span style={{ 
                    color: item.status === 'indexed' ? '#107c10' : '#605e5c',
                    fontWeight: 500
                }}>
                    {item.status}
                </span>
            )
        },
        {
            key: 'created_at',
            name: 'Created',
            fieldName: 'created_at',
            minWidth: 150,
            maxWidth: 200,
            isResizable: true,
            onRender: (item: VideoItem) => formatDate(item.created_at)
        },
        {
            key: 'export',
            name: 'Export',
            minWidth: 100,
            maxWidth: 120,
            isResizable: true,
            onRender: (item: VideoItem) => (
                <div style={{ position: 'relative', zIndex: 1 }}>
                    <TooltipHost content={item.status !== 'indexed' ? 'Video must be indexed to export captions' : 'Export subtitle files'}>
                        <PrimaryButton
                            text="Export"
                            iconProps={{ iconName: 'Download' }}
                            disabled={item.status !== 'indexed'}
                            onClick={() => setExportPanelVisible(exportPanelVisible === item.video_id ? null : item.video_id || null)}
                            data-video-id={item.video_id}
                            styles={{ 
                                root: { 
                                    minWidth: 80,
                                    height: 24,
                                    fontSize: '11px',
                                    padding: '0 8px'
                                }
                            }}
                        />
                    </TooltipHost>
                </div>
            )
        },
        // Portal for export panel to avoid stacking context issues
        exportPanelVisible && {
            key: 'exportPortal',
            name: '',
            minWidth: 1,
            maxWidth: 1,
            onRender: () => {
                const currentVideo = videos.find(v => v.video_id === exportPanelVisible);
                if (!currentVideo) return null;

                return (
                    <div style={{
                        position: 'fixed',
                        top: 0,
                        left: 0,
                        width: '100vw',
                        height: '100vh',
                        zIndex: 9999,
                        pointerEvents: 'none'
                    }}>
                        <div 
                            style={{
                                position: 'absolute',
                                top: '50%', // Will be adjusted by JavaScript
                                right: '20px',
                                zIndex: 10000,
                                backgroundColor: 'white',
                                border: '1px solid #d1d1d1',
                                borderRadius: '4px',
                                padding: '12px',
                                minWidth: '280px',
                                boxShadow: '0 8px 16px rgba(0,0,0,0.2)',
                                maxHeight: '400px',
                                overflow: 'visible',
                                pointerEvents: 'auto'
                            }}
                            ref={(el) => {
                                if (el) {
                                    // Position the panel near the clicked button
                                    const buttonElement = document.querySelector(`[data-video-id="${exportPanelVisible}"]`);
                                    if (buttonElement) {
                                        const rect = buttonElement.getBoundingClientRect();
                                        el.style.top = `${rect.bottom + 4}px`;
                                        el.style.right = `${window.innerWidth - rect.right}px`;
                                    }
                                }
                            }}
                        >
                            <div style={{ marginBottom: '12px', fontWeight: 600, fontSize: '13px' }}>
                                Export Options
                            </div>
                            
                            <div style={{ marginBottom: '12px', fontSize: '12px', color: '#666' }}>
                                Subtitle files will be exported in the language specified during video upload.
                            </div>
                            
                            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                                <DefaultButton
                                    text="SRT"
                                    iconProps={{ iconName: 'Download' }}
                                    onClick={() => handleExport(currentVideo, 'srt', currentVideo.source_language || 'auto')}
                                    styles={{ root: { minWidth: '60px' } }}
                                />
                                <DefaultButton
                                    text="VTT"
                                    iconProps={{ iconName: 'Download' }}
                                    onClick={() => handleExport(currentVideo, 'vtt', currentVideo.source_language || 'auto')}
                                    styles={{ root: { minWidth: '60px' } }}
                                />
                                <PrimaryButton
                                    text="Both"
                                    iconProps={{ iconName: 'CloudDownload' }}
                                    onClick={() => handleExport(currentVideo, 'both', currentVideo.source_language || 'auto')}
                                    styles={{ root: { minWidth: '60px' } }}
                                />
                            </div>
                            
                            <div style={{ marginTop: '8px' }}>
                                <DefaultButton
                                    text="Cancel"
                                    onClick={() => setExportPanelVisible(null)}
                                    styles={{ 
                                        root: { 
                                            width: '100%',
                                            fontSize: '11px',
                                            height: '24px'
                                        }
                                    }}
                                />
                            </div>

                            {/* Click outside to close */}
                            <div 
                                style={{
                                    position: 'fixed',
                                    top: 0,
                                    left: 0,
                                    width: '100vw',
                                    height: '100vh',
                                    zIndex: -1
                                }}
                                onClick={() => setExportPanelVisible(null)}
                            />
                        </div>
                    </div>
                );
            }
        }
    ].filter(Boolean) as IColumn[];

    const getSelectedItems = (): VideoItem[] => {
        return selection.getSelection() as VideoItem[];
    };

    const handleDeleteSelected = async () => {
        const selectedItems = getSelectedItems();
        if (selectedItems.length === 0) return;

        setDeleting(true);
        try {
            const videoIds = selectedItems.map(item => item.video_id || item.filename);
            
            if (selectedItems.length === 1) {
                // Single deletion
                const response = await fetch(`/libraries/${libraryName}/videos/${videoIds[0]}`, {
                    method: 'DELETE'
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Failed to delete video');
                }
            } else {
                // Batch deletion
                const response = await fetch(`/libraries/${libraryName}/videos/batch-delete`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ video_ids: videoIds })
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Failed to delete videos');
                }
            }

            // Notify parent component
            if (onVideoDeleted) {
                onVideoDeleted(videoIds);
            }

            // Refresh the list
            await loadVideos();
            
            // Clear selection
            selection.setAllSelected(false);
            setSelectedCount(0);
            
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to delete videos');
            console.error('Error deleting videos:', err);
        } finally {
            setDeleting(false);
            setDeleteDialogVisible(false);
        }
    };

    const handleCleanupOrphaned = async (shouldDelete: boolean = false) => {
        setCleanupInProgress(true);
        setError(null);
        
        try {
            const response = await fetch(`/libraries/${libraryName}/cleanup-orphaned`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ delete: shouldDelete })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to cleanup orphaned videos');
            }
            
            const result = await response.json();
            setCleanupResult(result);
            
            if (shouldDelete && result.deleted > 0) {
                // Refresh the list if videos were actually deleted
                await loadVideos();
            }
            
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to cleanup orphaned videos');
            console.error('Error cleaning up orphaned videos:', err);
        } finally {
            setCleanupInProgress(false);
        }
    };

    const handleExport = async (item: VideoItem, format: string, language?: string) => {
        if (!item.video_id || item.status !== 'indexed') {
            setError('Video must be indexed and have a valid video ID to export captions');
            return;
        }

        const selectedLanguage = language || 'auto'; // Default to auto-detect

        try {
            if (format === 'both') {
                // Download both SRT and VTT
                await downloadCaption(item, 'srt', selectedLanguage);
                await downloadCaption(item, 'vtt', selectedLanguage);
            } else {
                await downloadCaption(item, format, selectedLanguage);
            }
            
            // Close the export panel after successful download
            setExportPanelVisible(null);
        } catch (err) {
            setError(`Failed to export ${format.toUpperCase()} file: ${err instanceof Error ? err.message : 'Unknown error'}`);
            console.error('Error exporting captions:', err);
        }
    };

    const downloadCaption = async (item: VideoItem, format: string, language: string = 'auto') => {
        const url = `/libraries/${libraryName}/videos/${item.video_id}/captions/${format}${language !== 'auto' ? `?language=${language}` : ''}`;
        
        const response = await fetch(url, {
            method: 'GET'
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Failed to export caption file' }));
            throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
        }

        // Create download link
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        
        // Generate filename: remove extension and add format and language
        const baseFilename = item.filename.replace(/\.[^/.]+$/, '');
        const languageSuffix = language !== 'auto' ? `.${language}` : '';
        link.download = `${baseFilename}${languageSuffix}.${format}`;
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(downloadUrl);
        
        console.log(`Successfully exported ${format.toUpperCase()} for video: ${item.filename} (Language: ${language})`);
    };

    const commandBarItems: ICommandBarItemProps[] = [
        {
            key: 'refresh',
            text: 'Refresh',
            iconProps: { iconName: 'Refresh' },
            onClick: () => { loadVideos(); }
        },
        {
            key: 'cleanup',
            text: 'Cleanup Orphaned',
            iconProps: { iconName: 'CleanData' },
            disabled: cleanupInProgress,
            onClick: () => {
                setCleanupResult(null);
                setCleanupDialogVisible(true);
                handleCleanupOrphaned(false); // First check only
            }
        },
        {
            key: 'delete',
            text: `Delete Selected${selectedCount > 0 ? ` (${selectedCount})` : ''}`,
            iconProps: { iconName: 'Delete' },
            disabled: selectedCount === 0 || deleting,
            onClick: () => setDeleteDialogVisible(true)
        }
    ];

    if (loading) {
        return (
            <div style={{ padding: 20, textAlign: 'center' }}>
                <Spinner size={SpinnerSize.large} label="Loading videos..." />
            </div>
        );
    }

    return (
        <div>
            {error && (
                <MessageBar 
                    messageBarType={MessageBarType.error} 
                    onDismiss={() => setError(null)}
                    dismissButtonAriaLabel="Close"
                >
                    {error}
                </MessageBar>
            )}
            
            <CommandBar
                items={commandBarItems}
                ariaLabel="Video management commands"
            />
            
            <DetailsList
                items={videos}
                columns={columns}
                setKey="set"
                layoutMode={0}
                selection={selection}
                selectionPreservedOnEmptyClick={true}
                selectionMode={SelectionMode.multiple}
                ariaLabelForSelectionColumn="Toggle selection"
                ariaLabelForSelectAllCheckbox="Toggle selection for all items"
                checkButtonAriaLabel="select row"
            />

            {videos.length === 0 && !loading && (
                <div style={{ padding: 20, textAlign: 'center', color: '#605e5c' }}>
                    No videos found in this library.
                </div>
            )}
            
            <Dialog
                hidden={!deleteDialogVisible}
                onDismiss={() => setDeleteDialogVisible(false)}
                dialogContentProps={{
                    type: DialogType.normal,
                    title: 'Confirm Deletion',
                    subText: `Are you sure you want to delete ${selectedCount} video(s)? This action cannot be undone.`
                }}
                modalProps={{
                    isBlocking: true,
                    styles: { main: { maxWidth: 450 } },
                }}
            >
                <DialogFooter>
                    <PrimaryButton 
                        onClick={handleDeleteSelected} 
                        disabled={deleting}
                        text={deleting ? 'Deleting...' : 'Delete'}
                    />
                    <DefaultButton 
                        onClick={() => setDeleteDialogVisible(false)} 
                        text="Cancel" 
                        disabled={deleting}
                    />
                </DialogFooter>
            </Dialog>
            
            <Dialog
                hidden={!cleanupDialogVisible}
                onDismiss={() => {
                    setCleanupDialogVisible(false);
                    setCleanupResult(null);
                }}
                dialogContentProps={{
                    type: DialogType.normal,
                    title: 'Cleanup Orphaned Videos',
                    subText: cleanupResult ? '' : 'Checking for orphaned video records...'
                }}
                modalProps={{
                    isBlocking: true,
                    styles: { main: { maxWidth: 600, minHeight: 300 } },
                }}
            >
                <div style={{ padding: '10px 0' }}>
                    {cleanupInProgress && (
                        <div style={{ textAlign: 'center', padding: 20 }}>
                            <Spinner size={SpinnerSize.medium} label="Checking videos..." />
                        </div>
                    )}
                    
                    {cleanupResult && (
                        <div>
                            <div style={{ marginBottom: 15 }}>
                                <strong>Cleanup Results:</strong>
                                <ul style={{ marginTop: 5 }}>
                                    <li>Total videos checked: {cleanupResult.total_checked}</li>
                                    <li>Orphaned records found: {cleanupResult.total_orphaned}</li>
                                    {cleanupResult.deleted !== undefined && (
                                        <li style={{ color: cleanupResult.deleted > 0 ? 'green' : 'orange' }}>
                                            Records deleted: {cleanupResult.deleted}
                                        </li>
                                    )}
                                </ul>
                            </div>
                            
                            {cleanupResult.orphaned && cleanupResult.orphaned.length > 0 && (
                                <div>
                                    <strong>Orphaned Videos:</strong>
                                    <div style={{ 
                                        maxHeight: 200, 
                                        overflow: 'auto', 
                                        border: '1px solid #d1d1d1', 
                                        padding: 10, 
                                        marginTop: 5,
                                        fontSize: '12px'
                                    }}>
                                        {cleanupResult.orphaned.map((orphan: any, idx: number) => (
                                            <div key={idx} style={{ marginBottom: 8, padding: 5, backgroundColor: '#f8f8f8' }}>
                                                <div><strong>File:</strong> {orphan.filename}</div>
                                                <div><strong>Video ID:</strong> {orphan.video_id || 'N/A'}</div>
                                                <div><strong>Reason:</strong> {orphan.reason}</div>
                                                {orphan.deleted !== undefined && (
                                                    <div style={{ color: orphan.deleted ? 'green' : 'red' }}>
                                                        <strong>Deleted:</strong> {orphan.deleted ? 'Yes' : 'No'}
                                                        {orphan.delete_error && ` (${orphan.delete_error})`}
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
                
                <DialogFooter>
                    {cleanupResult && cleanupResult.total_orphaned > 0 && cleanupResult.deleted === undefined && (
                        <PrimaryButton 
                            onClick={() => handleCleanupOrphaned(true)} 
                            disabled={cleanupInProgress}
                            text={cleanupInProgress ? 'Deleting...' : `Delete ${cleanupResult.total_orphaned} Orphaned Records`}
                            style={{ backgroundColor: '#d13438', borderColor: '#d13438' }}
                        />
                    )}
                    <DefaultButton 
                        onClick={() => {
                            setCleanupDialogVisible(false);
                            setCleanupResult(null);
                        }} 
                        text="Close" 
                        disabled={cleanupInProgress}
                    />
                </DialogFooter>
            </Dialog>
        </div>
    );
};

export default VideoList;
