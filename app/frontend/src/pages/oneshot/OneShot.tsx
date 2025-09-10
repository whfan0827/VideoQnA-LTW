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

import { useAppConfig } from "../../hooks/useAppConfig";
import { useApiCall } from "../../hooks/useApiCall";

const OneShot = () => {
    // UI Panel states
    const [isConfigPanelOpen, setIsConfigPanelOpen] = useState(false);
    const [isLibraryPanelOpen, setIsLibraryPanelOpen] = useState(false);
    const [isAIParameterPanelOpen, setIsAIParameterPanelOpen] = useState(false);
    
    // Configuration management
    const { topK, targetLibrary, setTargetLibrary } = useAppConfig();
    
    // API call management
    const askApiCall = useApiCall<AskResponse, AskRequest>();
    const indexesApiCall = useApiCall<string[]>();
    
    // Constants (moved from state)
    const approach = Approaches.ReadRetrieveReadVector;
    const promptTemplate = "";
    const promptTemplatePrefix = "";
    const promptTemplateSuffix = "";
    const useSemanticRanker = true;
    const useSemanticCaptions = false;
    const excludeCategory = "";

    // Local component state
    const lastQuestionRef = useRef<string>("");
    const [indexes, setIndexes] = useState<IDropdownOption[]>([]);
    const [index, setIndex] = useState<string>();
    const [activeCitation, setActiveCitation] = useState<string>();
    const [activeScene, setActiveScene] = useState<string>();
    const [question, setQuestion] = useState<string>();
    const [activeAnalysisPanelTab, setActiveAnalysisPanelTab] = useState<AnalysisPanelTabs | undefined>(undefined);

    // Load indexes on component mount
    useEffect(() => {
        getIndexes();
    }, []);
    
    // Sync target library with index selection
    useEffect(() => {
        if (targetLibrary && indexes.length > 0) {
            const isValidLibrary = indexes.some(idx => idx.key === targetLibrary);
            if (isValidLibrary) {
                setIndex(targetLibrary);
            }
        }
    }, [targetLibrary, indexes]);

    
    const refreshIndexes = async () => {
        const newIndexes = await indexesAPI();
        const convertedIndexes = newIndexes.map(index => ({ key: index, text: formatString(index) }));
        setIndexes(convertedIndexes);
    };
    
    const getIndexes = async () => {
        try {
            const indexes = await indexesApiCall.execute(indexesAPI);
            const convertedIndexes = indexes.map(index => ({ key: index, text: formatString(index) }));
            setIndexes(convertedIndexes);
            if (indexes.includes("vi-prompt-content-example-index")) {
                setIndex("vi-prompt-content-example-index");
            } else {
                setIndex(convertedIndexes[0].key);
            }
        } catch (error) {
            console.error(`Error when getting indexes: ${error}`);
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
        
        // Reset UI state
        setActiveCitation(undefined);
        setActiveScene(undefined);
        setActiveAnalysisPanelTab(undefined);

        // Use target library or current index
        const selectedIndex = targetLibrary || index;

        const request: AskRequest = {
            question,
            approach,
            overrides: {
                promptTemplate: promptTemplate || undefined,
                promptTemplatePrefix: promptTemplatePrefix || undefined,
                promptTemplateSuffix: promptTemplateSuffix || undefined,
                excludeCategory: excludeCategory || undefined,
                top: topK,
                index: selectedIndex,
                semanticRanker: useSemanticRanker,
                semanticCaptions: useSemanticCaptions
            }
        };
        
        return askApiCall.execute(askApi, request);
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
        askApiCall.reset();
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);
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
                        <ClearChatButton className={styles.commandButton} onClick={clearChat} disabled={!lastQuestionRef.current || askApiCall.isLoading} />
                    </div>
                    <h1 className={styles.oneshotTitle}>Unlock insights from your video library</h1>
                    <h3 className={styles.oneshotSubTitle}>
                        <div>This is a platform of AI can find answers from your video library. </div>
                        <div>AI-generated content can have mistakes. Make sure it's accurate and appropriate before using it.</div>
                    </h3>
                    <div className={styles.oneshotQuestionInput}>
                        <QuestionInput
                            question={question}
                            placeholder="Tips: Go to Conversation Settings to pick up a Target Library first."
                            disabled={askApiCall.isLoading || indexesApiCall.isLoading}
                            onSend={question => makeApiRequest(question)}
                        />
                    </div>
                </div>
                {!indexesApiCall.isLoading ? (
                    <div className={styles.oneshotBottomSection}>
                        {askApiCall.isLoading && <Spinner label="Generating answer" />}
                        {!lastQuestionRef.current && <ExampleList onExampleClicked={onExampleClicked} />}
                        {!askApiCall.isLoading && askApiCall.data && !askApiCall.error && (
                            <div className={styles.oneshotAnswerContainer}>
                                <Answer
                                    answer={askApiCall.data}
                                    onCitationClicked={(x, docId) => onShowCitation(x, docId)}
                                    onThoughtProcessClicked={() => onToggleTab(AnalysisPanelTabs.ThoughtProcessTab)}
                                    onSupportingContentClicked={() => onToggleTab(AnalysisPanelTabs.SupportingContentTab)}
                                />
                            </div>
                        )}
                        {askApiCall.error ? (
                            <div className={styles.oneshotAnswerContainer}>
                                <AnswerError error={askApiCall.error.toString()} onRetry={() => makeApiRequest(lastQuestionRef.current)} />
                            </div>
                        ) : null}
                        {activeAnalysisPanelTab && askApiCall.data && (
                            <AnalysisPanel
                                className={styles.oneshotAnalysisPanel}
                                activeCitation={activeCitation}
                                activeScene={activeScene}
                                onActiveTabChanged={x => onToggleTab(x)}
                                citationHeight="100%"
                                answer={askApiCall.data}
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
