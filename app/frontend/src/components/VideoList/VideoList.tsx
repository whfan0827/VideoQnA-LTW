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
    SpinnerSize
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
        return new Date(dateString).toLocaleString();
    };

    const columns: IColumn[] = [
        {
            key: 'filename',
            name: 'Filename',
            fieldName: 'filename',
            minWidth: 200,
            maxWidth: 300,
            isResizable: true,
            onRender: (item: VideoItem) => (
                <span title={item.filename}>{item.filename}</span>
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
        }
    ];

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

    const commandBarItems: ICommandBarItemProps[] = [
        {
            key: 'refresh',
            text: 'Refresh',
            iconProps: { iconName: 'Refresh' },
            onClick: () => { loadVideos(); }
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
        </div>
    );
};

export default VideoList;
