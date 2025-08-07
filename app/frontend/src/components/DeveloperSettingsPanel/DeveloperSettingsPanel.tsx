import { useState, useEffect } from "react";
import { TextField, PrimaryButton, Dropdown, Separator, Stack, MessageBar, MessageBarType, IDropdownOption, DefaultButton } from "@fluentui/react";
import styles from "./DeveloperSettingsPanel.module.css";

interface DeveloperSettingsPanelProps {
    indexes: IDropdownOption[];
}

interface ConversationStarter {
    text: string;
    value: string;
}

const DEFAULT_PROMPT_TEMPLATE = `You are an intelligent assistant helping customers with their video questions.
Use 'you' to refer to the individual asking the questions even if they ask with 'I'.
Answer the following question using the data provided in the sources below.
For tabular information return it as an html table. Do not return markdown format.
Each source has a name followed by colon and the actual information, always include the source name for each fact you use in the response.
The source name should be surrounded by square brackets. e.g. [video_id].
Provide helpful information even if the sources don't contain complete step-by-step instructions.
If the sources contain related information, explain what information is available and how it might be helpful.
Only say "I didn't find the answer, can you please rephrase?" if the sources contain no relevant information at all.
A Source always starts with a UUID followed by a colon and the source content.
Sources include some of the following:
Video title: title of the video.
Visual: textual content which is visible in the video.
Transcript: textual content which is spoken in the video. May start with a speaker name.
Known people: names of people who appear in video.
Tags: tags which describe the time period in the video.
Audio effects: sound effects which are heard in the video.

###
Question: '{question}'

Sources:
{context}

Answer:`;

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

export const DeveloperSettingsPanel = ({ indexes }: DeveloperSettingsPanelProps) => {
    const [selectedIndex, setSelectedIndex] = useState("");
    const [message, setMessage] = useState<{ text: string; type: MessageBarType } | null>(null);
    
    // Conversation Starters state
    const [starter1, setStarter1] = useState("");
    const [starter2, setStarter2] = useState("");
    const [starter3, setStarter3] = useState("");

    const showMessage = (text: string, type: MessageBarType) => {
        setMessage({ text, type });
        setTimeout(() => setMessage(null), 5000);
    };

    // Load conversation starters from localStorage
    useEffect(() => {
        loadConversationStarters();
        loadTargetLibrary();
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

    // Load target library from localStorage
    const loadTargetLibrary = () => {
        try {
            const saved = localStorage.getItem('target_library');
            if (saved) {
                setSelectedIndex(saved);
            }
        } catch (error) {
            console.error('Error loading target library:', error);
        }
    };

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

    const loadConversationStarters = () => {
        try {
            const saved = localStorage.getItem('conversation_starters');
            if (saved) {
                const starters = JSON.parse(saved) as ConversationStarter[];
                setStarter1(starters[0]?.text || "");
                setStarter2(starters[1]?.text || "");
                setStarter3(starters[2]?.text || "");
            } else {
                // Load defaults
                setStarter1(DEFAULT_CONVERSATION_STARTERS[0].text);
                setStarter2(DEFAULT_CONVERSATION_STARTERS[1].text);
                setStarter3(DEFAULT_CONVERSATION_STARTERS[2].text);
            }
        } catch (error) {
            console.error('Error loading conversation starters:', error);
            // Load defaults on error
            setStarter1(DEFAULT_CONVERSATION_STARTERS[0].text);
            setStarter2(DEFAULT_CONVERSATION_STARTERS[1].text);
            setStarter3(DEFAULT_CONVERSATION_STARTERS[2].text);
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
        <div className={styles.developerSettingsPanel}>
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
