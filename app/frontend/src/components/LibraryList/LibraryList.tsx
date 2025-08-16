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
    IDropdownOption,
    TextField
} from '@fluentui/react';

interface LibraryItem {
    key: string;
    displayName: string;
    videoCount: number;
    createdAt: string;
    status: string;
}

interface LibraryListProps {
    libraries: IDropdownOption[];
    onLibrariesChanged: () => void;
    isProcessing?: boolean;
}

const LibraryList: React.FC<LibraryListProps> = ({ 
    libraries, 
    onLibrariesChanged, 
    isProcessing = false 
}) => {
    const [libraryItems, setLibraryItems] = useState<LibraryItem[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [deleteDialogVisible, setDeleteDialogVisible] = useState(false);
    const [renameDialogVisible, setRenameDialogVisible] = useState(false);
    const [deleting, setDeleting] = useState(false);
    const [selectedCount, setSelectedCount] = useState(0);
    const [newName, setNewName] = useState('');
    const [selection] = useState(new Selection({
        onSelectionChanged: () => {
            setSelectedCount(selection.getSelectedCount());
        },
    }));

    // Convert libraries to detailed items
    useEffect(() => {
        const items: LibraryItem[] = libraries.map(lib => ({
            key: lib.key as string,
            displayName: lib.text || lib.key as string,
            videoCount: 0, // Will be loaded from API
            createdAt: new Date().toISOString(), // Will be loaded from API
            status: 'Active'
        }));
        setLibraryItems(items);
        loadLibraryDetails(items);
    }, [libraries]);

    const loadLibraryDetails = async (items: LibraryItem[]) => {
        setLoading(true);
        try {
            // Load video counts for each library
            const updatedItems = await Promise.all(
                items.map(async (item) => {
                    try {
                        const response = await fetch(`/libraries/${item.key}/videos`);
                        if (response.ok) {
                            const data = await response.json();
                            return {
                                ...item,
                                videoCount: data.videos?.length || 0
                            };
                        }
                        return item;
                    } catch (err) {
                        console.warn(`Failed to load details for ${item.key}:`, err);
                        return item;
                    }
                })
            );
            setLibraryItems(updatedItems);
        } catch (err) {
            console.error('Error loading library details:', err);
            setError('Failed to load library details');
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString();
    };

    const columns: IColumn[] = [
        {
            key: 'displayName',
            name: 'Library Name',
            fieldName: 'displayName',
            minWidth: 200,
            maxWidth: 300,
            isResizable: true,
            onRender: (item: LibraryItem) => (
                <div>
                    <div style={{ fontWeight: 600, marginBottom: 2 }}>{item.displayName}</div>
                    <div style={{ fontSize: 12, color: '#605e5c' }} title={item.key}>
                        {item.key}
                    </div>
                </div>
            )
        },
        {
            key: 'videoCount',
            name: 'Videos',
            fieldName: 'videoCount',
            minWidth: 80,
            maxWidth: 100,
            isResizable: true,
            onRender: (item: LibraryItem) => (
                <span style={{ 
                    fontWeight: 500,
                    color: item.videoCount > 0 ? '#107c10' : '#605e5c'
                }}>
                    {item.videoCount}
                </span>
            )
        },
        {
            key: 'createdAt',
            name: 'Created',
            fieldName: 'createdAt',
            minWidth: 100,
            maxWidth: 150,
            isResizable: true,
            onRender: (item: LibraryItem) => formatDate(item.createdAt)
        },
        {
            key: 'status',
            name: 'Status',
            fieldName: 'status',
            minWidth: 80,
            maxWidth: 100,
            isResizable: true,
            onRender: (item: LibraryItem) => (
                <span style={{ 
                    color: item.status === 'Active' ? '#107c10' : '#605e5c',
                    fontWeight: 500
                }}>
                    {item.status}
                </span>
            )
        }
    ];

    const getSelectedItems = (): LibraryItem[] => {
        return selection.getSelection() as LibraryItem[];
    };

    const handleDeleteSelected = async () => {
        const selectedItems = getSelectedItems();
        if (selectedItems.length === 0) return;

        setDeleting(true);
        try {
            let successCount = 0;
            let failCount = 0;

            for (const item of selectedItems) {
                try {
                    const response = await fetch(`/libraries/${item.key}`, {
                        method: 'DELETE'
                    });
                    
                    if (response.ok) {
                        successCount++;
                    } else {
                        failCount++;
                        console.error(`Failed to delete ${item.key}`);
                    }
                } catch (err) {
                    failCount++;
                    console.error(`Error deleting ${item.key}:`, err);
                }
            }

            // Show result message
            if (failCount === 0) {
                setError(null);
            } else if (successCount === 0) {
                setError(`Failed to delete ${failCount} libraries`);
            } else {
                setError(`Deleted ${successCount} libraries, failed to delete ${failCount}`);
            }

            // Refresh the parent component
            onLibrariesChanged();
            
            // Clear selection
            selection.setAllSelected(false);
            setSelectedCount(0);
            
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to delete libraries');
            console.error('Error deleting libraries:', err);
        } finally {
            setDeleting(false);
            setDeleteDialogVisible(false);
        }
    };

    const handleRenameLibrary = async () => {
        const selectedItems = getSelectedItems();
        if (selectedItems.length !== 1 || !newName.trim()) return;

        const item = selectedItems[0];
        setDeleting(true);
        try {
            // For now, we'll show a message that rename is not yet implemented
            // In the future, this would call a rename API endpoint
            setError('Library renaming feature is coming soon!');
            setNewName('');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to rename library');
        } finally {
            setDeleting(false);
            setRenameDialogVisible(false);
        }
    };

    const commandBarItems: ICommandBarItemProps[] = [
        {
            key: 'refresh',
            text: 'Refresh',
            iconProps: { iconName: 'Refresh' },
            onClick: () => { 
                onLibrariesChanged();
                if (libraryItems.length > 0) {
                    loadLibraryDetails(libraryItems);
                }
            }
        },
        {
            key: 'rename',
            text: 'Rename',
            iconProps: { iconName: 'Edit' },
            disabled: selectedCount !== 1 || deleting || isProcessing,
            onClick: () => {
                const selected = getSelectedItems();
                if (selected.length === 1) {
                    setNewName(selected[0].displayName);
                    setRenameDialogVisible(true);
                }
            }
        },
        {
            key: 'delete',
            text: `Delete${selectedCount > 0 ? ` (${selectedCount})` : ''}`,
            iconProps: { iconName: 'Delete' },
            disabled: selectedCount === 0 || deleting || isProcessing,
            onClick: () => setDeleteDialogVisible(true)
        }
    ];

    if (loading && libraryItems.length === 0) {
        return (
            <div style={{ padding: 20, textAlign: 'center' }}>
                <Spinner size={SpinnerSize.large} label="Loading libraries..." />
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
                    styles={{ root: { marginBottom: 16 } }}
                >
                    {error}
                </MessageBar>
            )}
            
            <CommandBar
                items={commandBarItems}
                ariaLabel="Library management commands"
                styles={{ root: { marginBottom: 16 } }}
            />
            
            <DetailsList
                items={libraryItems}
                columns={columns}
                setKey="set"
                layoutMode={0}
                selection={selection}
                selectionPreservedOnEmptyClick={true}
                selectionMode={SelectionMode.multiple}
                ariaLabelForSelectionColumn="Toggle selection"
                ariaLabelForSelectAllCheckbox="Toggle selection for all items"
                checkButtonAriaLabel="select row"
                compact={false}
            />

            {libraryItems.length === 0 && !loading && (
                <div style={{ 
                    padding: 40, 
                    textAlign: 'center', 
                    color: '#605e5c',
                    backgroundColor: '#f8f9fa',
                    borderRadius: 4,
                    marginTop: 16
                }}>
                    <div style={{ fontSize: 16, marginBottom: 8 }}>No libraries found</div>
                    <div style={{ fontSize: 14 }}>Create your first library in the Upload tab!</div>
                </div>
            )}
            
            {/* Delete Confirmation Dialog */}
            <Dialog
                hidden={!deleteDialogVisible}
                onDismiss={() => setDeleteDialogVisible(false)}
                dialogContentProps={{
                    type: DialogType.normal,
                    title: 'Confirm Library Deletion',
                    subText: `Are you sure you want to delete ${selectedCount} library(ies)? This will permanently remove all videos and data. This action cannot be undone.`
                }}
                modalProps={{
                    isBlocking: true,
                    styles: { main: { maxWidth: 500 } },
                }}
            >
                <DialogFooter>
                    <PrimaryButton 
                        onClick={handleDeleteSelected} 
                        disabled={deleting}
                        text={deleting ? 'Deleting...' : 'Delete Libraries'}
                        styles={{
                            root: { backgroundColor: '#d13438' },
                            rootHovered: { backgroundColor: '#b92b2b' }
                        }}
                    />
                    <DefaultButton 
                        onClick={() => setDeleteDialogVisible(false)} 
                        text="Cancel" 
                        disabled={deleting}
                    />
                </DialogFooter>
            </Dialog>

            {/* Rename Dialog */}
            <Dialog
                hidden={!renameDialogVisible}
                onDismiss={() => setRenameDialogVisible(false)}
                dialogContentProps={{
                    type: DialogType.normal,
                    title: 'Rename Library',
                    subText: 'Enter a new display name for this library'
                }}
                modalProps={{
                    isBlocking: true,
                    styles: { main: { maxWidth: 450 } },
                }}
            >
                <TextField
                    label="New Library Name"
                    value={newName}
                    onChange={(_, value) => setNewName(value || '')}
                    placeholder="Enter new name..."
                    disabled={deleting}
                />
                <DialogFooter>
                    <PrimaryButton 
                        onClick={handleRenameLibrary} 
                        disabled={deleting || !newName.trim()}
                        text={deleting ? 'Renaming...' : 'Rename'}
                    />
                    <DefaultButton 
                        onClick={() => {
                            setRenameDialogVisible(false);
                            setNewName('');
                        }} 
                        text="Cancel" 
                        disabled={deleting}
                    />
                </DialogFooter>
            </Dialog>
        </div>
    );
};

export default LibraryList;