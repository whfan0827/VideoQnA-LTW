import React, { useState, useEffect } from 'react';
import {
    Stack,
    Text,
    Dropdown,
    IDropdownOption,
    DetailsList,
    IColumn,
    Selection,
    SelectionMode,
    MessageBar,
    MessageBarType,
    Spinner,
    SpinnerSize,
    TextField,
    PrimaryButton,
    DefaultButton,
    Pivot,
    PivotItem
} from '@fluentui/react';

interface BlobInfo {
    name: string;
    container: string;
    size: number;
    last_modified: string;
    content_type: string;
    md5_hash?: string;
    metadata?: Record<string, string>;
}

interface BlobStorageBrowserProps {
    onSelectionChange: (selectedBlobs: BlobInfo[]) => void;
    multiSelect?: boolean;
}

const BlobStorageBrowser: React.FC<BlobStorageBrowserProps> = ({
    onSelectionChange,
    multiSelect = true
}) => {
    const [containers, setContainers] = useState<string[]>([]);
    const [selectedContainer, setSelectedContainer] = useState<string>('');
    const [blobs, setBlobs] = useState<BlobInfo[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [importMode, setImportMode] = useState<'browse' | 'pattern' | 'list'>('browse');
    const [pathPattern, setPathPattern] = useState<string>('');
    const [blobList, setBlobList] = useState<string>('');

    const [selection] = useState(new Selection({
        onSelectionChanged: () => {
            const selectedItems = selection.getSelection() as BlobInfo[];
            onSelectionChange(selectedItems);
        }
    }));

    // Load containers on component mount
    useEffect(() => {
        loadContainers();
    }, []);

    // Load blobs when container changes
    useEffect(() => {
        if (selectedContainer && importMode === 'browse') {
            loadBlobs();
        }
    }, [selectedContainer, importMode]);

    const loadContainers = async () => {
        setLoading(true);
        try {
            const response = await fetch('/blob-storage/containers');
            if (response.ok) {
                const data = await response.json();
                setContainers(data.containers || []);
                if (data.containers.length > 0) {
                    setSelectedContainer(data.containers[0]);
                }
            } else {
                const errorData = await response.json();
                setError(errorData.error || 'Failed to load containers');
            }
        } catch (err) {
            setError('Network error while loading containers');
            console.error('Error loading containers:', err);
        } finally {
            setLoading(false);
        }
    };

    const loadBlobs = async () => {
        if (!selectedContainer) return;

        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`/blob-storage/containers/${selectedContainer}/blobs`);
            if (response.ok) {
                const data = await response.json();
                setBlobs(data.blobs || []);
                selection.setAllSelected(false);
            } else {
                const errorData = await response.json();
                setError(errorData.error || 'Failed to load blobs');
            }
        } catch (err) {
            setError('Network error while loading blobs');
            console.error('Error loading blobs:', err);
        } finally {
            setLoading(false);
        }
    };

    const formatFileSize = (bytes: number): string => {
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        if (bytes === 0) return '0 Bytes';
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return `${Math.round(bytes / Math.pow(1024, i) * 100) / 100} ${sizes[i]}`;
    };

    const formatDate = (dateString: string): string => {
        const date = new Date(dateString);
        return date.toLocaleString();
    };

    const columns: IColumn[] = [
        {
            key: 'name',
            name: 'Name',
            fieldName: 'name',
            minWidth: 200,
            maxWidth: 400,
            isResizable: true,
            onRender: (item: BlobInfo) => {
                const fileName = item.name.split('/').pop() || item.name;
                const path = item.name.includes('/') ? item.name.substring(0, item.name.lastIndexOf('/') + 1) : '';
                return (
                    <div>
                        {path && (
                            <Text variant="small" style={{ color: '#666' }}>
                                {path}
                            </Text>
                        )}
                        <Text variant="medium" style={{ fontWeight: 500 }}>
                            {fileName}
                        </Text>
                    </div>
                );
            }
        },
        {
            key: 'size',
            name: 'Size',
            fieldName: 'size',
            minWidth: 80,
            maxWidth: 120,
            isResizable: true,
            onRender: (item: BlobInfo) => formatFileSize(item.size)
        },
        {
            key: 'last_modified',
            name: 'Last Modified',
            fieldName: 'last_modified',
            minWidth: 150,
            maxWidth: 200,
            isResizable: true,
            onRender: (item: BlobInfo) => formatDate(item.last_modified)
        },
        {
            key: 'content_type',
            name: 'Type',
            fieldName: 'content_type',
            minWidth: 100,
            maxWidth: 150,
            isResizable: true
        }
    ];

    const containerOptions: IDropdownOption[] = containers.map(container => ({
        key: container,
        text: container
    }));

    const handlePatternSearch = () => {
        // Implementation for pattern-based search would go here
        console.log('Pattern search:', pathPattern);
    };

    const handleListImport = () => {
        // Implementation for list-based import would go here
        console.log('List import:', blobList);
    };

    if (loading && containers.length === 0) {
        return (
            <div style={{ padding: 20, textAlign: 'center' }}>
                <Spinner size={SpinnerSize.large} label="Loading blob storage..." />
            </div>
        );
    }

    return (
        <Stack tokens={{ childrenGap: 20 }}>
            {error && (
                <MessageBar
                    messageBarType={MessageBarType.error}
                    onDismiss={() => setError(null)}
                    dismissButtonAriaLabel="Close"
                >
                    {error}
                </MessageBar>
            )}

            <Pivot
                selectedKey={importMode}
                onLinkClick={(item) => setImportMode(item?.props.itemKey as 'browse' | 'pattern' | 'list')}
            >
                <PivotItem headerText="Browse & Select" itemKey="browse" itemIcon="FolderOpen">
                    <Stack tokens={{ childrenGap: 15 }} style={{ marginTop: 20 }}>
                        <Dropdown
                            label="Storage Container"
                            options={containerOptions}
                            selectedKey={selectedContainer}
                            onChange={(_, option) => setSelectedContainer(option?.key as string)}
                            placeholder="Select a container"
                        />

                        {selectedContainer && (
                            <>
                                <Text variant="medium">
                                    Select videos to import from <strong>{selectedContainer}</strong>
                                </Text>

                                {loading ? (
                                    <div style={{ padding: 20, textAlign: 'center' }}>
                                        <Spinner size={SpinnerSize.medium} label="Loading videos..." />
                                    </div>
                                ) : (
                                    <DetailsList
                                        items={blobs}
                                        columns={columns}
                                        setKey="set"
                                        layoutMode={0}
                                        selection={selection}
                                        selectionPreservedOnEmptyClick={true}
                                        selectionMode={multiSelect ? SelectionMode.multiple : SelectionMode.single}
                                        ariaLabelForSelectionColumn="Toggle selection"
                                        ariaLabelForSelectAllCheckbox="Toggle selection for all items"
                                        checkButtonAriaLabel="select row"
                                    />
                                )}

                                {blobs.length === 0 && !loading && (
                                    <Text variant="medium" style={{ color: '#666', textAlign: 'center', padding: 20 }}>
                                        No video files found in this container.
                                    </Text>
                                )}
                            </>
                        )}
                    </Stack>
                </PivotItem>

                <PivotItem headerText="Path Pattern" itemKey="pattern" itemIcon="Filter">
                    <Stack tokens={{ childrenGap: 15 }} style={{ marginTop: 20 }}>
                        <Dropdown
                            label="Storage Container"
                            options={containerOptions}
                            selectedKey={selectedContainer}
                            onChange={(_, option) => setSelectedContainer(option?.key as string)}
                            placeholder="Select a container"
                        />

                        <TextField
                            label="File Path Pattern"
                            value={pathPattern}
                            onChange={(_, value) => setPathPattern(value || '')}
                            placeholder="e.g., training-videos/*.mp4"
                            description="Use * to match multiple characters, ? to match single character"
                        />

                        <PrimaryButton
                            text="Search by Pattern"
                            onClick={handlePatternSearch}
                            disabled={!selectedContainer || !pathPattern}
                        />
                    </Stack>
                </PivotItem>

                <PivotItem headerText="File List" itemKey="list" itemIcon="BulkUpload">
                    <Stack tokens={{ childrenGap: 15 }} style={{ marginTop: 20 }}>
                        <Dropdown
                            label="Storage Container"
                            options={containerOptions}
                            selectedKey={selectedContainer}
                            onChange={(_, option) => setSelectedContainer(option?.key as string)}
                            placeholder="Select a container"
                        />

                        <TextField
                            label="File List"
                            value={blobList}
                            onChange={(_, value) => setBlobList(value || '')}
                            multiline
                            rows={10}
                            placeholder={`Enter one file path per line:\nfolder1/video1.mp4\nfolder2/video2.mp4\nsubfolder/video3.mp4`}
                            description="Each line should contain a full blob path within the container"
                        />

                        <PrimaryButton
                            text="Import File List"
                            onClick={handleListImport}
                            disabled={!selectedContainer || !blobList.trim()}
                        />
                    </Stack>
                </PivotItem>
            </Pivot>
        </Stack>
    );
};

export default BlobStorageBrowser;