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

    // Persist selectedIndex changes
    useEffect(() => {
        if (selectedIndex) {
            localStorage.setItem('target_library', selectedIndex);
        } else {
            localStorage.removeItem('target_library');
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


    const handleSaveConversationStarters = () => {
        try {
            const starters: ConversationStarter[] = [
                { text: starter1, value: starter1 },
                { text: starter2, value: starter2 },
                { text: starter3, value: starter3 }
            ].filter(s => s.text.trim() !== ""); // Filter out empty starters

            localStorage.setItem('conversation_starters', JSON.stringify(starters));
            
            // Trigger event to notify ExampleList component
            window.dispatchEvent(new CustomEvent('conversation_starters_updated'));
            
            showMessage("Conversation starters saved successfully!", MessageBarType.success);
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
                    </Stack>
                    <p className={styles.description}>
                        Configure the example questions shown to users when they start a conversation.
                    </p>
                    <Stack tokens={{ childrenGap: 12 }}>
                        <TextField
                            label="Starter 1"
                            value={starter1}
                            onChange={(_, value) => setStarter1(value || "")}
                            placeholder="Enter first conversation starter..."
                        />
                        <TextField
                            label="Starter 2"
                            value={starter2}
                            onChange={(_, value) => setStarter2(value || "")}
                            placeholder="Enter second conversation starter..."
                        />
                        <TextField
                            label="Starter 3"
                            value={starter3}
                            onChange={(_, value) => setStarter3(value || "")}
                            placeholder="Enter third conversation starter..."
                        />
                    </Stack>
                    <Stack horizontal tokens={{ childrenGap: 12 }} styles={{ root: { marginTop: '16px' } }}>
                        <PrimaryButton
                            text="Save"
                            onClick={handleSaveConversationStarters}
                            iconProps={{ iconName: "Save" }}
                        />
                        <DefaultButton
                            text="Reset"
                            onClick={handleResetConversationStarters}
                            iconProps={{ iconName: "Refresh" }}
                        />
                    </Stack>
                </div>
            </Stack>
        </div>
    );
};