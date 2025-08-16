import { useRef, useState, useEffect } from "react";
import { Panel, PanelType, DefaultButton, Spinner, IDropdownOption } from "@fluentui/react";

import styles from "./OneShot.module.css";

import { askApi, Approaches, AskResponse, AskRequest, indexesAPI } from "../../api";
import { Answer, AnswerError } from "../../components/Answer";
import { QuestionInput } from "../../components/QuestionInput";
import { ExampleList } from "../../components/Example";
import { LibraryManagementPanel } from "../../components/LibraryManagementPanel";
import { AnalysisPanel, AnalysisPanelTabs } from "../../components/AnalysisPanel";
import { AIParameterButton } from "../../components/AIParameterButton";
import { ConversationSettingsButton } from "../../components/ConversationSettingsButton";
import { LibraryManagementButton } from "../../components/LibraryManagementButton";
import { ClearChatButton } from "../../components/ClearChatButton";
import { ConversationSettingsPanel } from "../../components/ConversationSettingsPanel";
import AIParameterPanel from "../../components/AIParameterPanel/AIParameterPanel";

const OneShot = () => {
    const [isConfigPanelOpen, setIsConfigPanelOpen] = useState(false);
    const [isLibraryPanelOpen, setIsLibraryPanelOpen] = useState(false);
    const [isAIParameterPanelOpen, setIsAIParameterPanelOpen] = useState(false);
    const [approach] = useState<Approaches>(Approaches.ReadRetrieveReadVector);
    const [promptTemplate] = useState<string>("");
    const [promptTemplatePrefix] = useState<string>("");
    const [promptTemplateSuffix] = useState<string>("");
    const [retrieveCount, setRetrieveCount] = useState<number>(() => {
        const saved = localStorage.getItem('top_k');
        return saved ? parseInt(saved, 10) : 3;
    });
    const [useSemanticRanker] = useState<boolean>(true);
    const [index, setIndex] = useState<string>();
    const [useSemanticCaptions] = useState<boolean>(false);
    const [excludeCategory] = useState<string>("");

    const lastQuestionRef = useRef<string>("");

    const [isAskLoading, setIsAskLoading] = useState<boolean>(false);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<unknown>();
    const [answer, setAnswer] = useState<AskResponse>();
    const [indexes, setIndexes] = useState<IDropdownOption[]>([]);

    const [activeCitation, setActiveCitation] = useState<string>();
    const [activeScene, setActiveScene] = useState<string>();
    const [question, setQuestion] = useState<string>();
    const [activeAnalysisPanelTab, setActiveAnalysisPanelTab] = useState<AnalysisPanelTabs | undefined>(undefined);

    //call getIndexes() on load
    useEffect(() => {
        getIndexes();
    }, []);
    
    // Load target library from localStorage and update index
    useEffect(() => {
        try {
            const targetLibrary = localStorage.getItem('target_library');
            if (targetLibrary && indexes.length > 0) {
                const isValidLibrary = indexes.some(idx => idx.key === targetLibrary);
                if (isValidLibrary) {
                    setIndex(targetLibrary);
                    console.log("[DEBUG] Set target library from localStorage:", targetLibrary);
                } else {
                    console.log("[DEBUG] Target library from localStorage not found in available indexes:", targetLibrary);
                }
            }
        } catch (error) {
            console.error('Error loading target library:', error);
        }
    }, [indexes]);
    
    // Listen for top_k changes in localStorage
    useEffect(() => {
        const handleStorageChange = () => {
            const saved = localStorage.getItem('top_k');
            const newValue = saved ? parseInt(saved, 10) : 3;
            setRetrieveCount(newValue);
        };

        // Listen for storage events (changes from other tabs)
        window.addEventListener('storage', handleStorageChange);
        
        // Also check on mount and when focus returns to window
        window.addEventListener('focus', handleStorageChange);
        
        return () => {
            window.removeEventListener('storage', handleStorageChange);
            window.removeEventListener('focus', handleStorageChange);
        };
    }, []);
    
    const refreshIndexes = async () => {
        const newIndexes = await indexesAPI();
        const convertedIndexes = newIndexes.map(index => ({ key: index, text: formatString(index) }));
        setIndexes(convertedIndexes);
    };
    
    const getIndexes = async () => {
        setIsLoading(true);
        try {
            const indexes = await indexesAPI();
            const convertedIndexes = indexes.map(index => ({ key: index, text: formatString(index) }));
            setIndexes(convertedIndexes);
            if (indexes.includes("vi-prompt-content-example-index")) {
                setIndex("vi-prompt-content-example-index");
            } else {
                setIndex(convertedIndexes[0].key);
            }
        } catch (error) {
            console.error(`Error when getting indexes: ${error}`);
        } finally {
            setIsLoading(false);
        }
    };

    const formatString = (input: string): string => {
        // Split the input by the hyphen character and store the resulting array
        const parts = input.split("-");
        // Initialize an empty array to store the formatted parts
        const formattedParts: string[] = [];
        // Loop through the parts array
        for (const part of parts) {
            // If the part is not empty and not equal to "vi", capitalize the first letter and push it to the formatted parts array
            if (part && part !== "vi") {
                formattedParts.push(part[0].toUpperCase() + part.slice(1));
            }
        }
        // Join the formatted parts array by a space and return the resulting string
        return formattedParts.join(" ");
    };

    const makeApiRequest = async (question: string) => {
        lastQuestionRef.current = question;

        error && setError(undefined);
        setIsAskLoading(true);
        setActiveCitation(undefined);
        setActiveScene(undefined);
        setActiveAnalysisPanelTab(undefined);

        try {
            // Check for target library from localStorage before making request
            let selectedIndex = index;
            try {
                const targetLibrary = localStorage.getItem('target_library');
                if (targetLibrary && indexes.some(idx => idx.key === targetLibrary)) {
                    selectedIndex = targetLibrary;
                    console.log("[DEBUG] Using target library for request:", targetLibrary);
                } else {
                    console.log("[DEBUG] No valid target library found, using default index:", selectedIndex);
                }
            } catch (e) {
                console.warn("Error reading target library from localStorage:", e);
            }

            const request: AskRequest = {
                question,
                approach,
                overrides: {
                    promptTemplate: promptTemplate.length === 0 ? undefined : promptTemplate,
                    promptTemplatePrefix: promptTemplatePrefix.length === 0 ? undefined : promptTemplatePrefix,
                    promptTemplateSuffix: promptTemplateSuffix.length === 0 ? undefined : promptTemplateSuffix,
                    excludeCategory: excludeCategory.length === 0 ? undefined : excludeCategory,
                    top: retrieveCount,
                    index: selectedIndex,
                    semanticRanker: useSemanticRanker,
                    semanticCaptions: useSemanticCaptions
                }
            };
            console.log("[DEBUG] Making API request with index:", selectedIndex);
            const result = await askApi(request);
            setAnswer(result);
        } catch (e) {
            setError(e);
        } finally {
            setIsAskLoading(false);
        }
    };









    const onExampleClicked = (example: string) => {
        makeApiRequest(example);
        setQuestion(example);
    };

    const onShowCitation = (citation: string, docId: string) => {
        if (activeCitation === citation && activeAnalysisPanelTab === AnalysisPanelTabs.CitationTab) {
            setActiveAnalysisPanelTab(undefined);
        } else {
            setActiveCitation(citation);
            setActiveScene(docId);
            setActiveAnalysisPanelTab(AnalysisPanelTabs.CitationTab);
        }
    };

    const clearChat = () => {
        lastQuestionRef.current = "";
        error && setError(undefined);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);
        setAnswer(undefined);
        setQuestion("");
    };

    const onToggleTab = (tab: AnalysisPanelTabs) => {
        if (activeAnalysisPanelTab !== tab) {
            setActiveAnalysisPanelTab(tab);
        }
    };

    // Check if any panel is open for accessibility management
    const isAnyPanelOpen = isConfigPanelOpen || isLibraryPanelOpen || isAIParameterPanelOpen;

    return (
        <div className={styles.oneshotContainer}>
            {/* Main content that should be hidden from screen readers when panels are open */}
            <div 
                className={styles.oneshotMainContent}
                aria-hidden={isAnyPanelOpen ? 'true' : undefined}
                inert={isAnyPanelOpen ? '' : undefined}
            >
                <div className={styles.oneshotTopSection}>
                    <div className={styles.commandsContainer}>
                        <AIParameterButton className={styles.commandButton} onClick={() => setIsAIParameterPanelOpen(true)} />
                        <LibraryManagementButton className={styles.commandButton} onClick={() => setIsLibraryPanelOpen(!isLibraryPanelOpen)} />
                        <ConversationSettingsButton className={styles.commandButton} onClick={() => setIsConfigPanelOpen(!isConfigPanelOpen)} />
                        <ClearChatButton className={styles.commandButton} onClick={clearChat} disabled={!lastQuestionRef.current || isAskLoading} />
                    </div>
                    <h1 className={styles.oneshotTitle}>Ask your video library</h1>
                    <h3 className={styles.oneshotSubTitle}>
                        <div>This is a platform of AI can find answers from your video library. </div>
                        <div>AI-generated content can have mistakes. Make sure it's accurate and appropriate before using it.</div>
                    </h3>
                    <div className={styles.oneshotQuestionInput}>
                        <QuestionInput
                            question={question}
                            placeholder="Tips: Go to Conversation Settings to pick up a Target Library first."
                            disabled={isAskLoading || isLoading}
                            onSend={question => makeApiRequest(question)}
                        />
                    </div>
                </div>
                {!isLoading ? (
                    <div className={styles.oneshotBottomSection}>
                        {isAskLoading && <Spinner label="Generating answer" />}
                        {!lastQuestionRef.current && <ExampleList onExampleClicked={onExampleClicked} />}
                        {!isAskLoading && answer && !error && (
                            <div className={styles.oneshotAnswerContainer}>
                                <Answer
                                    answer={answer}
                                    onCitationClicked={(x, docId) => onShowCitation(x, docId)}
                                    onThoughtProcessClicked={() => onToggleTab(AnalysisPanelTabs.ThoughtProcessTab)}
                                    onSupportingContentClicked={() => onToggleTab(AnalysisPanelTabs.SupportingContentTab)}
                                />
                            </div>
                        )}
                        {error ? (
                            <div className={styles.oneshotAnswerContainer}>
                                <AnswerError error={error.toString()} onRetry={() => makeApiRequest(lastQuestionRef.current)} />
                            </div>
                        ) : null}
                        {activeAnalysisPanelTab && answer && (
                            <AnalysisPanel
                                className={styles.oneshotAnalysisPanel}
                                activeCitation={activeCitation}
                                activeScene={activeScene}
                                onActiveTabChanged={x => onToggleTab(x)}
                                citationHeight="100%"
                                answer={answer}
                                activeTab={activeAnalysisPanelTab}
                            />
                        )}
                    </div>
                ) : (
                    <Spinner className={styles.loadingIndexes} label="Loading" />
                )}
            </div>
            <Panel
                headerText="Conversation Settings"
                isOpen={isConfigPanelOpen}
                isBlocking={false}
                onDismiss={() => setIsConfigPanelOpen(false)}
                closeButtonAriaLabel="Close"
                onRenderFooterContent={() => <DefaultButton onClick={() => setIsConfigPanelOpen(false)}>Close</DefaultButton>}
                isFooterAtBottom={true}
                type={PanelType.custom}
                customWidth="40%"
                layerProps={{
                    eventBubblingEnabled: false
                }}
            >
                <div className={styles.configSection}>
                    <ConversationSettingsPanel indexes={indexes} />
                </div>
            </Panel>

            <Panel
                headerText="Library Management"
                isOpen={isLibraryPanelOpen}
                isBlocking={false}
                onDismiss={() => setIsLibraryPanelOpen(false)}
                closeButtonAriaLabel="Close"
                onRenderFooterContent={() => <DefaultButton onClick={() => setIsLibraryPanelOpen(false)}>Close</DefaultButton>}
                isFooterAtBottom={true}
                type={PanelType.custom}
                customWidth="80%"
                layerProps={{
                    eventBubblingEnabled: false
                }}
            >
                <div className={styles.configSection}>
                    <LibraryManagementPanel 
                        indexes={indexes}
                        onLibrariesChanged={refreshIndexes}
                    />
                </div>
            </Panel>

            <Panel
                headerText="AI Parameter Configuration"
                isOpen={isAIParameterPanelOpen}
                isBlocking={false}
                onDismiss={() => setIsAIParameterPanelOpen(false)}
                closeButtonAriaLabel="Close"
                onRenderFooterContent={() => <DefaultButton onClick={() => setIsAIParameterPanelOpen(false)}>Close</DefaultButton>}
                isFooterAtBottom={true}
                type={PanelType.custom}
                customWidth="80%"
                layerProps={{
                    eventBubblingEnabled: false
                }}
            >
                <div className={styles.configSection}>
                    <AIParameterPanel 
                        availableLibraries={indexes.map(idx => ({ key: String(idx.key), text: idx.text }))}
                    />
                </div>
            </Panel>
        </div>
    );
};

export default OneShot;
