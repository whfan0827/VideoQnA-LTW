import React, { useState } from 'react';
import {
    Stack,
    Text,
    ChoiceGroup,
    IChoiceGroupOption,
    Icon,
    Separator
} from '@fluentui/react';

interface UploadOption {
    type: 'local' | 'blob';
    label: string;
    description: string;
    icon: string;
}

interface UploadModeSelectorProps {
    selectedMode: 'local' | 'blob';
    onModeChange: (mode: 'local' | 'blob') => void;
}

const UploadModeSelector: React.FC<UploadModeSelectorProps> = ({
    selectedMode,
    onModeChange
}) => {
    const uploadOptions: UploadOption[] = [
        {
            type: 'local',
            label: 'Local File Upload',
            description: 'Upload video files directly from your computer (suitable for small quantities)',
            icon: 'Upload'
        },
        {
            type: 'blob',
            label: 'Azure Blob Storage Import',
            description: 'Import videos from Azure Blob Storage (suitable for large quantities)',
            icon: 'CloudUpload'
        }
    ];

    const choiceOptions: IChoiceGroupOption[] = uploadOptions.map(option => ({
        key: option.type,
        text: '',
        onRenderField: (props, render) => (
            <div style={{ 
                display: 'flex', 
                alignItems: 'flex-start',
                padding: '12px 0',
                minHeight: '60px'
            }}>
                {render!(props)}
                <div style={{ marginLeft: 12 }}>
                    <Icon 
                        iconName={option.icon} 
                        style={{ 
                            marginRight: 12,
                            marginTop: 2,
                            fontSize: 18,
                            color: selectedMode === option.type ? '#0078d4' : '#666'
                        }} 
                    />
                </div>
                <div style={{ flex: 1 }}>
                    <Text 
                        variant="medium" 
                        block 
                        style={{ 
                            fontWeight: selectedMode === option.type ? 600 : 400,
                            marginBottom: 6,
                            color: selectedMode === option.type ? '#0078d4' : '#323130'
                        }}
                    >
                        {option.label}
                    </Text>
                    <Text 
                        variant="small" 
                        style={{ 
                            color: '#666',
                            lineHeight: '1.4',
                            display: 'block'
                        }}
                    >
                        {option.description}
                    </Text>
                </div>
            </div>
        )
    }));

    return (
        <Stack tokens={{ childrenGap: 20 }}>
            <div>
                <Text variant="xLarge" style={{ fontWeight: 600, marginBottom: 12, display: 'block' }}>
                    Add Videos to Library
                </Text>
                <Text variant="medium" style={{ color: '#666', display: 'block' }}>
                    Choose how you want to add videos to this library
                </Text>
            </div>
            
            <Separator />
            
            <ChoiceGroup
                options={choiceOptions}
                selectedKey={selectedMode}
                onChange={(_, option) => onModeChange(option?.key as 'local' | 'blob')}
                styles={{
                    root: {
                        marginTop: 8
                    },
                    flexContainer: {
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '12px'
                    }
                }}
            />
        </Stack>
    );
};

export default UploadModeSelector;