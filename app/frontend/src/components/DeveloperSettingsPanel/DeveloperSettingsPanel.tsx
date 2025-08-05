import { useState, useEffect } from "react";
import { TextField, PrimaryButton, Dropdown, Separator, Stack, Label, MessageBar, MessageBarType, IDropdownOption, DefaultButton } from "@fluentui/react";
import styles from "./DeveloperSettingsPanel.module.css";

interface DeveloperSettingsPanelProps {
    indexes: IDropdownOption[];
}

interface Settings {
    promptTemplate: string;
    semanticRanker: boolean;
    temperature: number;
    maxTokens: number;
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
    const [settings, setSettings] = useState<Settings>({
        promptTemplate: DEFAULT_PROMPT_TEMPLATE,
        semanticRanker: false,
        temperature: 0.7,
        maxTokens: 800
    });
    const [selectedIndex, setSelectedIndex] = useState("");
    const [isSaving, setIsSaving] = useState(false);
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
    }, []);

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

    // Load settings when component mounts or index changes
    useEffect(() => {
        if (selectedIndex) {
            loadSettings();
        }
    }, [selectedIndex]);

    const loadSettings = async () => {
        try {
            const response = await fetch(`/settings/${selectedIndex}`);
            if (response.ok) {
                const data = await response.json();
                setSettings({ 
                    promptTemplate: data.promptTemplate || DEFAULT_PROMPT_TEMPLATE,
                    semanticRanker: data.semanticRanker ?? false,
                    temperature: data.temperature ?? 0.7,
                    maxTokens: data.maxTokens ?? 800
                });
            } else {
                // If no settings found, use defaults
                setSettings({
                    promptTemplate: DEFAULT_PROMPT_TEMPLATE,
                    semanticRanker: false,
                    temperature: 0.7,
                    maxTokens: 800
                });
            }
        } catch (error) {
            console.log("Using default settings");
            setSettings({
                promptTemplate: DEFAULT_PROMPT_TEMPLATE,
                semanticRanker: false,
                temperature: 0.7,
                maxTokens: 800
            });
        }
    };

    const handleSaveSettings = async () => {
        if (!selectedIndex) {
            showMessage("Please select a library first", MessageBarType.warning);
            return;
        }

        setIsSaving(true);
        try {
            const response = await fetch(`/settings/${selectedIndex}`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(settings)
            });

            if (!response.ok) {
                throw new Error("Failed to save settings");
            }

            showMessage("Settings saved successfully!", MessageBarType.success);
        } catch (error) {
            showMessage(`Failed to save settings: ${error}`, MessageBarType.error);
        } finally {
            setIsSaving(false);
        }
    };

    const handleResetToDefault = () => {
        if (confirm("Are you sure you want to reset all settings to default values?")) {
            setSettings({
                promptTemplate: DEFAULT_PROMPT_TEMPLATE,
                semanticRanker: false,
                temperature: 0.7,
                maxTokens: 800
            });
            showMessage("Settings reset to default values", MessageBarType.info);
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

    const semanticRankerOptions: IDropdownOption[] = [
        { key: "false", text: "Disabled - Use keyword search only" },
        { key: "true", text: "Enabled - Use AI semantic search" }
    ];

    const temperatureOptions: IDropdownOption[] = [
        { key: 0.1, text: "0.1 - Very focused and deterministic" },
        { key: 0.3, text: "0.3 - Focused with some creativity" },
        { key: 0.5, text: "0.5 - Balanced" },
        { key: 0.7, text: "0.7 - Creative (Recommended)" },
        { key: 0.9, text: "0.9 - Very creative and diverse" }
    ];

    const maxTokensOptions: IDropdownOption[] = [
        { key: 400, text: "400 - Short responses" },
        { key: 800, text: "800 - Medium responses (Recommended)" },
        { key: 1200, text: "1200 - Long responses" },
        { key: 1600, text: "1600 - Very long responses" }
    ];

    return (
        <div className={styles.developerSettingsPanel}>
            <div className={styles.panelHeader}>
                <h3>Developer Settings</h3>
                <p>Configure AI model parameters and prompt templates</p>
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
                        onChange={(_, item) => setSelectedIndex(item?.key as string || "")}
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

                <Separator />

                {/* AI Configuration */}
                <div className={styles.settingCard}>
                    <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 8 }}>
                        <h4>AI Configuration</h4>
                    </Stack>
                    
                    {/* Prompt Template Section */}
                    <div style={{ marginBottom: '24px' }}>
                        <Label><strong>Prompt Template</strong></Label>
                        <p className={styles.description}>
                            Customize how the AI interprets and responds to questions. Use {"{context}"} for video content and {"{question}"} for user queries.
                        </p>
                        <TextField
                            multiline
                            rows={8}
                            value={settings.promptTemplate}
                            onChange={(_, value) => setSettings({ ...settings, promptTemplate: value || "" })}
                            placeholder="Enter your custom prompt template..."
                            disabled={!selectedIndex}
                            styles={{ 
                                field: { 
                                    fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                                    fontSize: '12px',
                                    lineHeight: '1.4'
                                }
                            }}
                        />
                    </div>

                    {/* Model Parameters Section */}
                    <div style={{ marginBottom: '24px' }}>
                        <Label><strong>Model Parameters</strong></Label>
                        <Stack tokens={{ childrenGap: 16 }} styles={{ root: { marginTop: '12px' } }}>
                            {/* Temperature */}
                            <div>
                                <Label>Response Creativity (Temperature)</Label>
                                <p className={styles.parameterDescription}>
                                    Controls randomness in AI responses. Lower values = more focused, higher values = more creative.
                                </p>
                                <Dropdown
                                    options={temperatureOptions}
                                    selectedKey={settings.temperature}
                                    onChange={(_, item) => setSettings({ ...settings, temperature: item?.key as number || 0.7 })}
                                    disabled={!selectedIndex}
                                />
                            </div>

                            {/* Max Tokens */}
                            <div>
                                <Label>Response Length (Max Tokens)</Label>
                                <p className={styles.parameterDescription}>
                                    Maximum length of AI responses. Higher values allow longer answers but cost more.
                                </p>
                                <Dropdown
                                    options={maxTokensOptions}
                                    selectedKey={settings.maxTokens}
                                    onChange={(_, item) => setSettings({ ...settings, maxTokens: item?.key as number || 800 })}
                                    disabled={!selectedIndex}
                                />
                            </div>

                            {/* Semantic Ranker */}
                            <div>
                                <Label>Search Method</Label>
                                <p className={styles.parameterDescription}>
                                    Choose between keyword-based search or AI-powered semantic search for better context understanding.
                                </p>
                                <Dropdown
                                    options={semanticRankerOptions}
                                    selectedKey={settings.semanticRanker.toString()}
                                    onChange={(_, item) => setSettings({ ...settings, semanticRanker: item?.key === "true" })}
                                    disabled={!selectedIndex}
                                />
                            </div>
                        </Stack>
                    </div>

                    {/* Current Configuration Preview */}
                    {selectedIndex && (
                        <div>
                            <Label><strong>Current Configuration Preview</strong></Label>
                            <div className={styles.previewGrid} style={{ marginTop: '12px' }}>
                                <div className={styles.previewItem}>
                                    <strong>Library:</strong>
                                    <span>{indexes.find(i => i.key === selectedIndex)?.text || selectedIndex}</span>
                                </div>
                                <div className={styles.previewItem}>
                                    <strong>Temperature:</strong>
                                    <span>{settings.temperature}</span>
                                </div>
                                <div className={styles.previewItem}>
                                    <strong>Max Tokens:</strong>
                                    <span>{settings.maxTokens}</span>
                                </div>
                                <div className={styles.previewItem}>
                                    <strong>Semantic Search:</strong>
                                    <span>{settings.semanticRanker ? "Enabled" : "Disabled"}</span>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Action Buttons */}
                    <div style={{ marginTop: '24px' }}>
                        <Label><strong>Actions</strong></Label>
                        <Stack horizontal tokens={{ childrenGap: 12 }} styles={{ root: { marginTop: '12px' } }}>
                            <PrimaryButton
                                text={isSaving ? "Saving..." : "Save Settings"}
                                onClick={handleSaveSettings}
                                disabled={!selectedIndex || isSaving}
                                iconProps={{ iconName: "Save" }}
                            />
                            <PrimaryButton
                                text="Reset to Default"
                                onClick={handleResetToDefault}
                                disabled={!selectedIndex}
                                iconProps={{ iconName: "Refresh" }}
                                styles={{
                                    root: {
                                        backgroundColor: '#f3f2f1',
                                        borderColor: '#d2d0ce',
                                        color: '#323130'
                                    },
                                    rootHovered: {
                                        backgroundColor: '#edebe9',
                                        borderColor: '#c8c6c4'
                                    }
                                }}
                            />
                        </Stack>
                    </div>
                </div>
            </Stack>
        </div>
    );
};
