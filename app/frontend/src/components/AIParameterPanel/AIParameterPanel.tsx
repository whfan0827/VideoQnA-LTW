import React, { useState, useEffect } from 'react';
import {
  Panel,
  PanelType,
  Pivot,
  PivotItem,
  MessageBar,
  MessageBarType,
  DefaultButton,
} from '@fluentui/react';

import QuickSetupTab from './QuickSetupTab';
import ParameterAdjustmentTab from './ParameterAdjustmentTab';
import TemplateManagementTab from './TemplateManagementTab';
import styles from './AIParameterPanel.module.css';

interface AIParameterPanelProps {
  availableLibraries: Array<{ key: string; text: string }>;
  onMessage?: (text: string, type: MessageBarType) => void;
}

interface PanelMessage {
  text: string;
  type: MessageBarType;
}

const AIParameterPanel: React.FC<AIParameterPanelProps> = ({
  availableLibraries,
  onMessage,
}) => {
  const [activeTab, setActiveTab] = useState(() => {
    return localStorage.getItem('aiParameterPanel_activeTab') || 'quickSetup';
  });
  const [message, setMessage] = useState<PanelMessage | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Persist activeTab to localStorage
  useEffect(() => {
    localStorage.setItem('aiParameterPanel_activeTab', activeTab);
  }, [activeTab]);

  // Function to show messages
  const showMessage = (text: string, type: MessageBarType) => {
    setMessage({ text, type });
    setTimeout(() => setMessage(null), 5000);
    // Also call parent onMessage if provided
    if (onMessage) {
      onMessage(text, type);
    }
  };

  // Handle tab switching
  const handleTabChange = (item?: PivotItem) => {
    if (item?.props.itemKey) {
      setActiveTab(item.props.itemKey);
    }
  };

  return (
    <div>
      {/* Panel Subtitle */}
      <div className={styles.panelSubtitleSection}>
        <p className={styles.panelSubtitle}>
          Configure AI templates, adjust parameters, and manage settings for your video libraries
        </p>
      </div>

      {/* Message Display */}
      {message && (
        <div className={styles.messageContainer}>
          <MessageBar
            messageBarType={message.type}
            onDismiss={() => setMessage(null)}
          >
            {message.text}
          </MessageBar>
        </div>
      )}

      {/* Tab Navigation */}
      <Pivot
        selectedKey={activeTab}
        onLinkClick={handleTabChange}
        headersOnly={true}
        styles={{
          root: {
            borderBottom: '1px solid #d2d0ce',
            marginBottom: '0',
          },
        }}
      >
            <PivotItem
              headerText="Quick Setup"
              itemKey="quickSetup"
              itemIcon="Lightning"
            />
            <PivotItem
              headerText="Parameter Adjustment"
              itemKey="parameterAdjustment"
              itemIcon="Settings"
            />
            <PivotItem
              headerText="Template Management"
              itemKey="templateManagement"
              itemIcon="Library"
            />
          </Pivot>

          {/* Tab Content */}
          <div className={styles.tabContent}>
            {activeTab === 'quickSetup' && (
              <QuickSetupTab
                availableLibraries={availableLibraries}
                onMessage={showMessage}
                isLoading={isLoading}
                setIsLoading={setIsLoading}
              />
            )}

            {activeTab === 'parameterAdjustment' && (
              <ParameterAdjustmentTab
                availableLibraries={availableLibraries}
                onMessage={showMessage}
                isLoading={isLoading}
                setIsLoading={setIsLoading}
              />
            )}

          {activeTab === 'templateManagement' && (
            <TemplateManagementTab
              onMessage={showMessage}
              isLoading={isLoading}
              setIsLoading={setIsLoading}
            />
          )}
        </div>
    </div>
  );
};

export default AIParameterPanel;
