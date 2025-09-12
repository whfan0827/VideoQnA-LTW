import { useState, useEffect } from "react";
import { TextField, PrimaryButton, Dropdown, Separator, Stack, MessageBar, MessageBarType, IDropdownOption, DefaultButton, SpinButton } from "@fluentui/react";
import { useAppConfig } from '../../hooks/useAppConfig';
import styles from "./ConversationSettingsPanel.module.css";

interface ConversationSettingsPanelProps {
    indexes: IDropdownOption[];
}

interface ConversationStarter {
    text: string;
    value: string;
}


const DEFAULT_CONVERSATION_STARTERS: ConversationStarter[] = [
    {
        text: "What insights are included with Azure AI Video Indexer?",
        value: "What insights are included with Azure AI Video Indexer?"
    },
    {
        text: "What is OCR?",
        value: "What is OCR?"
    },
    {
        text: "What is the distance to Mars?",
        value: "What is the distance to Mars?"
    }
];

export const ConversationSettingsPanel = ({ indexes }: ConversationSettingsPanelProps) => {
    // Use global targetLibrary state instead of local state
    const { topK, setTopK, targetLibrary, setTargetLibrary } = useAppConfig();
    const [selectedIndex, setSelectedIndex] = useState("");
    const [message, setMessage] = useState<{ text: string; type: MessageBarType } | null>(null);
    
    // Debug logging
    console.log('🔍 ConversationSettingsPanel render:', {
        targetLibrary,
        selectedIndex,
        indexesLength: indexes.length
    });
    
    // Conversation Starters state with localStorage initialization
    const [starter1, setStarter1] = useState(() => {
        try {
            const saved = localStorage.getItem('conversation_starters');
            if (saved) {
                const starters = JSON.parse(saved) as ConversationStarter[];
                return starters[0]?.text || DEFAULT_CONVERSATION_STARTERS[0].text;
            }
            return DEFAULT_CONVERSATION_STARTERS[0].text;
        } catch (error) {
            return DEFAULT_CONVERSATION_STARTERS[0].text;
        }
    });
    const [starter2, setStarter2] = useState(() => {
        try {
            const saved = localStorage.getItem('conversation_starters');
            if (saved) {
                const starters = JSON.parse(saved) as ConversationStarter[];
                return starters[1]?.text || DEFAULT_CONVERSATION_STARTERS[1].text;
            }
            return DEFAULT_CONVERSATION_STARTERS[1].text;
        } catch (error) {
            return DEFAULT_CONVERSATION_STARTERS[1].text;
        }
    });
    const [starter3, setStarter3] = useState(() => {
        try {
            const saved = localStorage.getItem('conversation_starters');
            if (saved) {
                const starters = JSON.parse(saved) as ConversationStarter[];
                return starters[2]?.text || DEFAULT_CONVERSATION_STARTERS[2].text;
            }
            return DEFAULT_CONVERSATION_STARTERS[2].text;
        } catch (error) {
            return DEFAULT_CONVERSATION_STARTERS[2].text;
        }
    });

    const showMessage = (text: string, type: MessageBarType) => {
        setMessage({ text, type });
        setTimeout(() => setMessage(null), 5000);
    };

    // Load library-specific conversation starters
    const loadLibraryConversationStarters = async (libraryId: string) => {
        try {
            // First try to load from cache
            const cached = getLibraryStartersFromCache(libraryId);
            if (cached) {
                updateCurrentStarters(cached);
                return;
            }

            // Load from API
            const response = await fetch(`/api/libraries/${libraryId}/conversation-starters`);
            if (response.ok) {
                const data = await response.json();
                const starters = data.starters || DEFAULT_CONVERSATION_STARTERS;
                updateCurrentStarters(starters);
                saveLibraryStartersToCache(libraryId, starters);
            } else {
                throw new Error('Failed to load library starters');
            }
        } catch (error) {
            console.error('Error loading library conversation starters:', error);
            // Fall back to defaults
            updateCurrentStarters(DEFAULT_CONVERSATION_STARTERS);
        }
    };

    // Load default conversation starters
    const loadDefaultConversationStarters = () => {
        updateCurrentStarters(DEFAULT_CONVERSATION_STARTERS);
    };

    // Update current conversation starters display
    const updateCurrentStarters = (starters: ConversationStarter[]) => {
        setStarter1(starters[0]?.text || DEFAULT_CONVERSATION_STARTERS[0].text);
        setStarter2(starters[1]?.text || DEFAULT_CONVERSATION_STARTERS[1].text);
        setStarter3(starters[2]?.text || DEFAULT_CONVERSATION_STARTERS[2].text);
    };

    // Cache management functions
    const getLibraryStartersFromCache = (libraryId: string): ConversationStarter[] | null => {
        try {
            const cached = localStorage.getItem('library_conversation_starters');
            if (cached) {
                const libraryStarters = JSON.parse(cached);
                return libraryStarters[libraryId] || null;
            }
        } catch (error) {
            console.error('Error reading from cache:', error);
        }
        return null;
    };

    const saveLibraryStartersToCache = (libraryId: string, starters: ConversationStarter[]) => {
        try {
            const existingCache = localStorage.getItem('library_conversation_starters');
            const libraryStarters = existingCache ? JSON.parse(existingCache) : {};
            libraryStarters[libraryId] = starters;
            localStorage.setItem('library_conversation_starters', JSON.stringify(libraryStarters));
        } catch (error) {
            console.error('Error saving to cache:', error);
        }
    };

    // Load initial data and validate on mount
    useEffect(() => {
        // Only validation needed as state is initialized from localStorage
    }, []);

    // Validate selected index when indexes change
    useEffect(() => {
        if (selectedIndex && indexes.length > 0) {
            const isValid = indexes.some(idx => idx.key === selectedIndex);
            if (!isValid) {
                setSelectedIndex("");
                localStorage.removeItem('target_library');
            }
        }
    }, [indexes, selectedIndex]);

    // Initialize and sync selectedIndex with global targetLibrary
    useEffect(() => {
        console.log('🔍 ConversationSettings: Syncing targetLibrary change:', {
            targetLibrary,
            currentSelectedIndex: selectedIndex,
            needsUpdate: targetLibrary !== selectedIndex
        });
        
        // Always sync selectedIndex with targetLibrary, including initial load
        setSelectedIndex(targetLibrary || "");
    }, [targetLibrary]);

    // Load library-specific conversation starters when selectedIndex changes
    useEffect(() => {
        if (selectedIndex) {
            // Load conversation starters for the selected library
            loadLibraryConversationStarters(selectedIndex);
        } else {
            // Reset to default starters when no library is selected
            loadDefaultConversationStarters();
        }
    }, [selectedIndex]);

    // Note: localStorage persistence is now handled by useAppConfig


    const handleSaveConversationStarters = async () => {
        if (!selectedIndex) {
            showMessage("Please select a library first", MessageBarType.warning);
            return;
        }

        try {
            const starters: ConversationStarter[] = [
                { text: starter1, value: starter1 },
                { text: starter2, value: starter2 },
                { text: starter3, value: starter3 }
            ].filter(s => s.text.trim() !== ""); // Filter out empty starters

            // Save to backend API
            const response = await fetch(`/api/libraries/${selectedIndex}/conversation-starters`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ starters })
            });

            if (!response.ok) {
                throw new Error('Failed to save conversation starters');
            }

            // Update local cache
            saveLibraryStartersToCache(selectedIndex, starters);
            
            // Also save to global localStorage for backward compatibility
            localStorage.setItem('conversation_starters', JSON.stringify(starters));
            
            // Trigger events to notify other components
            window.dispatchEvent(new CustomEvent('conversation_starters_updated', {
                detail: { libraryId: selectedIndex }
            }));
            window.dispatchEvent(new CustomEvent('target_library_changed', {
                detail: { libraryId: selectedIndex }
            }));
            
            showMessage(`Conversation starters saved for library "${selectedIndex}"`, MessageBarType.success);
        } catch (error) {
            showMessage(`Failed to save conversation starters: ${error}`, MessageBarType.error);
        }
    };

    const handleResetConversationStarters = () => {
        if (confirm("Are you sure you want to reset conversation starters to default values?")) {
            setStarter1(DEFAULT_CONVERSATION_STARTERS[0].text);
            setStarter2(DEFAULT_CONVERSATION_STARTERS[1].text);
            setStarter3(DEFAULT_CONVERSATION_STARTERS[2].text);
            showMessage("Conversation starters reset to default values", MessageBarType.info);
        }
    };

    return (
        <div className={styles.conversationSettingsPanel}>
            <div className={styles.panelHeader}>
                <h3>Conversation Settings</h3>
                <p>Configure conversation starters and basic settings</p>
            </div>

            {message && (
                <MessageBar 
                    messageBarType={message.type} 
                    onDismiss={() => setMessage(null)}
                    styles={{ root: { marginBottom: '16px' } }}
                >
                    {message.text}
                </MessageBar>
            )}

            {/* Current Settings Summary */}
            <div className={styles.settingCard} style={{ backgroundColor: '#f8f9fa', border: '1px solid #e1e5e9' }}>
                <h4 style={{ color: '#0078d4', marginBottom: '12px' }}>Current Settings Summary</h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '8px', fontSize: '14px' }}>
                    <strong>Target Library:</strong>
                    <span style={{ color: targetLibrary ? '#107c10' : '#d83b01' }}>
                        {targetLibrary ? (
                            <span>
                                {indexes.find(idx => idx.key === targetLibrary)?.text || targetLibrary}
                                <span style={{ marginLeft: '8px', fontSize: '12px', opacity: 0.7 }}>✓ Selected</span>
                            </span>
                        ) : (
                            <span>
                                Not selected 
                                <span style={{ marginLeft: '8px', fontSize: '12px' }}>⚠️ Required</span>
                            </span>
                        )}
                    </span>
                    <strong>Top K Results:</strong>
                    <span>{topK} results</span>
                    <strong>Library Status:</strong>
                    <span style={{ color: indexes.length > 0 ? '#107c10' : '#d83b01' }}>
                        {indexes.length > 0 ? `${indexes.length} libraries available` : 'No libraries available'}
                    </span>
                </div>
            </div>

            <Stack tokens={{ childrenGap: 20 }}>
                {/* Library Selection */}
                <div className={styles.settingCard}>
                    <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                        <h4>Target Library Selection</h4>
                        {selectedIndex && (
                            <span style={{ 
                                fontSize: '12px', 
                                color: '#107c10', 
                                backgroundColor: '#f3f9f3',
                                padding: '2px 8px',
                                borderRadius: '10px',
                                fontWeight: 500
                            }}>
                                Selected: {indexes.find(idx => idx.key === selectedIndex)?.text || selectedIndex}
                            </span>
                        )}
                    </Stack>
                    <p className={styles.description}>
                        Choose the video library to use as the default query target. This setting affects all new queries.
                    </p>
                    <Dropdown
                        placeholder={selectedIndex ? "Change selected library..." : "Please select a library..."}
                        options={indexes}
                        selectedKey={selectedIndex}
                        onChange={(_, item) => {
                            const libraryKey = item?.key as string || "";
                            console.log(`🔍 ConversationSettings: Dropdown onChange - selected: ${libraryKey}`);
                            setSelectedIndex(libraryKey);
                            setTargetLibrary(libraryKey);  // This will handle localStorage via useAppConfig
                        }}
                        styles={{ root: { marginTop: '8px' } }}
                    />
                    {indexes.length === 0 && (
                        <div style={{ 
                            marginTop: '8px', 
                            padding: '8px', 
                            backgroundColor: '#fef4e6', 
                            border: '1px solid #f4d03f',
                            borderRadius: '4px',
                            fontSize: '14px',
                            color: '#d68910'
                        }}>
                            ⚠️ No libraries available. Please go to Library Management to create or import video libraries.
                        </div>
                    )}
                </div>

                <Separator />

                {/* Top K Setting */}
                <div className={styles.settingCard}>
                    <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                        <h4>Top K Results Setting</h4>
                        <span style={{ 
                            fontSize: '12px', 
                            color: '#0078d4', 
                            backgroundColor: '#f0f6ff',
                            padding: '2px 8px',
                            borderRadius: '10px',
                            fontWeight: 500
                        }}>
                            Current: {topK}
                        </span>
                    </Stack>
                    <p className={styles.description}>
                        Number of most relevant search results to use for generating answers (1-10). Higher values provide more context but may affect response speed.
                    </p>
                    <SpinButton
                        label="Top K"
                        value={topK.toString()}
                        onValidate={(value) => {
                            const num = parseInt(value, 10);
                            if (isNaN(num) || num < 1 || num > 10) {
                                return "1";
                            }
                            return num.toString();
                        }}
                        onIncrement={(value) => {
                            const current = parseInt(value, 10) || 1;
                            const newValue = Math.min(current + 1, 10);
                            setTopK(newValue);
                            return newValue.toString();
                        }}
                        onDecrement={(value) => {
                            const current = parseInt(value, 10) || 1;
                            const newValue = Math.max(current - 1, 1);
                            setTopK(newValue);
                            return newValue.toString();
                        }}
                        min={1}
                        max={10}
                        step={1}
                        styles={{ root: { marginTop: '8px', width: '120px' } }}
                    />
                </div>

                <Separator />

                {/* Conversation Starters */}
                <div className={styles.settingCard}>
                    <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                        <h4>Conversation Starters</h4>
                        {selectedIndex && (
                            <span style={{ 
                                fontSize: '12px', 
                                color: '#0078d4', 
                                backgroundColor: '#f0f6ff',
                                padding: '2px 8px',
                                borderRadius: '10px',
                                fontWeight: 500
                            }}>
                                For {indexes.find(idx => idx.key === selectedIndex)?.text || selectedIndex}
                            </span>
                        )}
                    </Stack>
                    <p className={styles.description}>
                        {selectedIndex 
                            ? `Configure conversation starters specifically for "${indexes.find(idx => idx.key === selectedIndex)?.text || selectedIndex}" library. These will be shown on the main page when this library is selected.`
                            : "Please select a library above to configure library-specific conversation starters."
                        }
                    </p>
                    
                    {selectedIndex && (
                        <div style={{ 
                            marginTop: '8px', 
                            marginBottom: '12px',
                            padding: '8px 12px', 
                            backgroundColor: '#f0f6ff', 
                            border: '1px solid #c7e0f4',
                            borderRadius: '4px',
                            fontSize: '13px'
                        }}>
                            <strong>Current Starters Preview:</strong>
                            <ol style={{ margin: '4px 0', paddingLeft: '20px' }}>
                                <li style={{ color: starter1 ? '#323130' : '#a19f9d' }}>
                                    {starter1 || '(Not set)'}
                                </li>
                                <li style={{ color: starter2 ? '#323130' : '#a19f9d' }}>
                                    {starter2 || '(Not set)'}
                                </li>
                                <li style={{ color: starter3 ? '#323130' : '#a19f9d' }}>
                                    {starter3 || '(Not set)'}
                                </li>
                            </ol>
                        </div>
                    )}
                    <Stack tokens={{ childrenGap: 12 }}>
                        <TextField
                            label="Starter 1"
                            value={starter1}
                            onChange={(_, value) => setStarter1(value || "")}
                            placeholder={selectedIndex ? "Enter first conversation starter..." : "Select a library first"}
                            disabled={!selectedIndex}
                        />
                        <TextField
                            label="Starter 2"
                            value={starter2}
                            onChange={(_, value) => setStarter2(value || "")}
                            placeholder={selectedIndex ? "Enter second conversation starter..." : "Select a library first"}
                            disabled={!selectedIndex}
                        />
                        <TextField
                            label="Starter 3"
                            value={starter3}
                            onChange={(_, value) => setStarter3(value || "")}
                            placeholder={selectedIndex ? "Enter third conversation starter..." : "Select a library first"}
                            disabled={!selectedIndex}
                        />
                    </Stack>
                    <Stack horizontal tokens={{ childrenGap: 12 }} styles={{ root: { marginTop: '16px' } }}>
                        <PrimaryButton
                            text="Save"
                            onClick={handleSaveConversationStarters}
                            iconProps={{ iconName: "Save" }}
                            disabled={!selectedIndex}
                        />
                        <DefaultButton
                            text="Reset"
                            onClick={handleResetConversationStarters}
                            iconProps={{ iconName: "Refresh" }}
                            disabled={!selectedIndex}
                        />
                    </Stack>
                </div>
            </Stack>
        </div>
    );
};