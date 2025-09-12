import { Pivot, PivotItem } from "@fluentui/react";
import DOMPurify from "dompurify";

import styles from "./AnalysisPanel.module.css";

import { SupportingContent } from "../SupportingContent";
import { AskResponse } from "../../api";
import { AnalysisPanelTabs } from "./AnalysisPanelTabs";
import { getFormattedEndTime, getFormattedStartTime, getVideoTitle } from "../../utils/vi-utils";

interface Props {
    className: string;
    activeTab: AnalysisPanelTabs;
    onActiveTabChanged: (tab: AnalysisPanelTabs) => void;
    activeCitation: string | undefined;
    activeScene?: string | undefined;
    citationHeight: string;
    answer: AskResponse;
}

const pivotItemDisabledStyle = { disabled: true, style: { color: "grey" } };

export const AnalysisPanel = ({ answer, activeTab, activeCitation, activeScene, citationHeight, className, onActiveTabChanged }: Props) => {
    const isDisabledThoughtProcessTab: boolean = !answer.thoughts;
    const isDisabledSupportingContentTab: boolean = !answer.data_points.length;
    const isDisabledCitationTab: boolean = !activeCitation;
    const sanitizedThoughts = DOMPurify.sanitize(answer.thoughts!);

    return (
        <Pivot
            className={className}
            selectedKey={activeTab}
            onLinkClick={pivotItem => pivotItem && onActiveTabChanged(pivotItem.props.itemKey! as AnalysisPanelTabs)}
            overflowBehavior="menu"
        >
            <PivotItem
                itemKey={AnalysisPanelTabs.ThoughtProcessTab}
                headerText="Thought process"
                headerButtonProps={isDisabledThoughtProcessTab ? pivotItemDisabledStyle : undefined}
            >
                <div className={styles.thoughtProcess} dangerouslySetInnerHTML={{ __html: sanitizedThoughts }}></div>
            </PivotItem>
            <PivotItem
                itemKey={AnalysisPanelTabs.SupportingContentTab}
                headerText="Supporting content"
                headerButtonProps={isDisabledSupportingContentTab ? pivotItemDisabledStyle : undefined}
            >
                <SupportingContent supportingContent={answer.data_points} answer={answer} />
            </PivotItem>

            <PivotItem
                className={styles.citationTab}
                itemKey={AnalysisPanelTabs.CitationTab}
                headerText="Citation"
                headerButtonProps={isDisabledCitationTab ? pivotItemDisabledStyle : undefined}
            >
                {/* Debug information */}
                {import.meta.env.DEV && (
                    <div style={{background: '#f5f5f5', padding: '10px', marginBottom: '10px', fontSize: '12px'}}>
                        <strong>Debug Info:</strong><br/>
                        activeScene: {activeScene || 'undefined'}<br/>
                        activeCitation: {activeCitation || 'undefined'}<br/>
                        docs_by_id keys: {Object.keys(answer.docs_by_id || {}).length}<br/>
                        Scene data exists: {activeScene ? (answer.docs_by_id[activeScene] ? 'YES' : 'NO') : 'N/A'}<br/>
                        
                        {activeScene && answer.docs_by_id[activeScene] && (
                            <>
                                <strong>Document Data:</strong><br/>
                                video_name: {answer.docs_by_id[activeScene].video_name || 'undefined'}<br/>
                                account_id: {answer.docs_by_id[activeScene].account_id || 'undefined'}<br/>
                                video_id: {answer.docs_by_id[activeScene].video_id || 'undefined'}<br/>
                                location: {answer.docs_by_id[activeScene].location || 'undefined'}<br/>
                                start_time: {answer.docs_by_id[activeScene].start_time || 'undefined'}<br/>
                                end_time: {answer.docs_by_id[activeScene].end_time || 'undefined'}<br/>
                            </>
                        )}
                        
                        <strong>All docs_by_id entries:</strong><br/>
                        {Object.entries(answer.docs_by_id || {}).map(([key, doc]: [string, any]) => (
                            <div key={key} style={{marginLeft: '10px', fontSize: '10px'}}>
                                {key}: {doc.video_name || 'No video_name'} | account_id: {doc.account_id || 'missing'} | video_id: {doc.video_id || 'missing'}
                            </div>
                        ))}
                    </div>
                )}
                
                {activeScene ? (
                    <div>
                        <div className={styles.playerContainer}>
                            <iframe
                                className={styles.playerIframe}
                                title="Citation"
                                src={activeCitation}
                                width="100%"
                                height={citationHeight}
                                frameBorder="0"
                                allow="fullscreen"
                                onLoad={() => console.log('✅ Citation iframe loaded:', activeCitation)}
                                onError={() => console.error('❌ Citation iframe failed to load:', activeCitation)}
                            />
                        </div>
                        <h2 className={styles.citationVideoTitle}>{getVideoTitle(activeScene, answer.docs_by_id, false, false)}</h2>
                        <p className={styles.citationVideoTime}>{`${getFormattedStartTime(answer.docs_by_id[activeScene!])} - ${getFormattedEndTime(
                            answer.docs_by_id[activeScene!]
                        )}`}</p>
                    </div>
                ) : (
                    <div style={{padding: '20px', textAlign: 'center', color: '#666'}}>
                        <p>No citation data available</p>
                        {import.meta.env.DEV && (
                            <div style={{marginTop: '10px', fontSize: '12px', textAlign: 'left'}}>
                                <strong>Possible reasons:</strong>
                                <ul>
                                    <li>activeScene is null or undefined</li>
                                    <li>docs_by_id doesn't contain the expected document</li>
                                    <li>Citation URL generation failed</li>
                                </ul>
                            </div>
                        )}
                    </div>
                )}
            </PivotItem>
        </Pivot>
    );
};
