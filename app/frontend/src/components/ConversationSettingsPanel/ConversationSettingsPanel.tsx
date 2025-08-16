import { useState, useEffect } from "react";
import { TextField, PrimaryButton, Dropdown, Separator, Stack, MessageBar, MessageBarType, IDropdownOption, DefaultButton, SpinButton } from "@fluentui/react";
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
    const [selectedIndex, setSelectedIndex] = useState(() => {
        return localStorage.getItem('target_library') || "";
    });
    const [message, setMessage] = useState<{ text: string; type: MessageBarType } | null>(null);
    
    // TopK setting state with localStorage initialization
    const [topK, setTopK] = useState(() => {
        const saved = localStorage.getItem('top_k');
        return saved ? parseInt(saved, 10) : 3; // Default to 3
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

    // Persist selectedIndex changes and load library-specific starters
    useEffect(() => {
        if (selectedIndex) {
            localStorage.setItem('target_library', selectedIndex);
            // Load conversation starters for the selected library
            loadLibraryConversationStarters(selectedIndex);
        } else {
            localStorage.removeItem('target_library');
            // Reset to default starters when no library is selected
            loadDefaultConversationStarters();
        }
    }, [selectedIndex]);

    // Persist topK changes
    useEffect(() => {
        localStorage.setItem('top_k', topK.toString());
    }, [topK]);


    // Save target library to localStorage
    const saveTargetLibrary = (libraryKey: string) => {
        try {
            if (libraryKey) {
                localStorage.setItem('target_library', libraryKey);
            } else {
                localStorage.removeItem('target_library');
            }
        } catch (error) {
            console.error('Error saving target library:', error);
        }
    };


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

            <Stack tokens={{ childrenGap: 20 }}>
                {/* Library Selection */}
                <div className={styles.settingCard}>
                    <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                        <h4>Target Library</h4>
                    </Stack>
                    <Dropdown
                        placeholder="Select library to configure"
                        options={indexes}
                        selectedKey={selectedIndex}
                        onChange={(_, item) => {
                            const libraryKey = item?.key as string || "";
                            setSelectedIndex(libraryKey);
                            saveTargetLibrary(libraryKey);
                        }}
                        styles={{ root: { marginTop: '8px' } }}
                    />
                </div>

                <Separator />

                {/* Top K Setting */}
                <div className={styles.settingCard}>
                    <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                        <h4>Top K Results</h4>
                    </Stack>
                    <p className={styles.description}>
                        Number of most relevant search results to use for generating answers (1-10).
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
                                {selectedIndex}
                            </span>
                        )}
                    </Stack>
                    <p className={styles.description}>
                        {selectedIndex 
                            ? `Configure conversation starters specifically for "${selectedIndex}". These will be shown when this library is selected.`
                            : "Please select a library above to configure library-specific conversation starters."
                        }
                    </p>
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