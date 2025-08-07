import React, { useState, useEffect } from 'react';
import {
  Stack,
  Dropdown,
  IDropdownOption,
  PrimaryButton,
  Text,
  MessageBarType,
  Spinner,
  SpinnerSize,
} from '@fluentui/react';
import styles from './AIParameterPanel.module.css';

interface QuickSetupTabProps {
  availableLibraries: Array<{ key: string; text: string }>;
  onMessage: (text: string, type: MessageBarType) => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
}

interface AITemplate {
  templateName: string;
  displayName: string;
  description: string;
  category: string;
  isSystemDefault: boolean;
}

const QuickSetupTab: React.FC<QuickSetupTabProps> = ({
  availableLibraries,
  onMessage,
  isLoading,
  setIsLoading,
}) => {
  const [selectedLibrary, setSelectedLibrary] = useState<string>('');
  const [templates, setTemplates] = useState<AITemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [templateDescription, setTemplateDescription] = useState<string>('');

  // Load template list
  useEffect(() => {
    loadTemplates();
  }, []);

  // Update description when template is selected
  useEffect(() => {
    if (selectedTemplate) {
      const template = templates.find(t => t.templateName === selectedTemplate);
      setTemplateDescription(template?.description || '');
    } else {
      setTemplateDescription('');
    }
  }, [selectedTemplate, templates]);

  const loadTemplates = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/templates');
      if (!response.ok) throw new Error('Failed to load templates');
      
      const templatesData = await response.json();
      setTemplates(templatesData);
    } catch (error) {
      console.error('Error loading templates:', error);
      onMessage('Failed to load AI templates', MessageBarType.error);
    } finally {
      setIsLoading(false);
    }
  };

  const applyTemplate = async () => {
    if (!selectedTemplate || !selectedLibrary) {
      onMessage('Please select both a library and a template', MessageBarType.warning);
      return;
    }
    
    try {
      setIsLoading(true);
      const response = await fetch(`/api/templates/${selectedTemplate}/apply-to/${selectedLibrary}`, {
        method: 'POST',
      });
      
      if (!response.ok) throw new Error('Failed to apply template');
      
      const template = templates.find(t => t.templateName === selectedTemplate);
      onMessage(`Template "${template?.displayName}" applied successfully to library "${selectedLibrary}"`, MessageBarType.success);
      
      // 清除選擇以便進行下一次操作
      setSelectedTemplate('');
      
    } catch (error) {
      console.error('Error applying template:', error);
      onMessage('Failed to apply template', MessageBarType.error);
    } finally {
      setIsLoading(false);
    }
  };

  const templateOptions: IDropdownOption[] = templates.map(template => ({
    key: template.templateName,
    text: `${template.isSystemDefault ? '[System] ' : '[Custom] '}${template.displayName}`,
    data: template,
  }));

  const libraryOptions: IDropdownOption[] = availableLibraries.map(lib => ({
    key: lib.key,
    text: lib.text,
  }));

  if (isLoading && templates.length === 0) {
    return (
      <div className={styles.loadingSpinner}>
        <Spinner size={SpinnerSize.large} label="Loading templates..." />
      </div>
    );
  }

  return (
    <Stack tokens={{ childrenGap: 24 }}>
      <div className={styles.settingSection}>
        <div className={styles.sectionHeader}>
          <h3 className={styles.sectionTitle}>Quick Template Application</h3>
          <p className={styles.sectionDescription}>
            Quickly apply pre-configured AI templates to your video libraries. 
            Templates include optimized prompts and parameters for different use cases.
          </p>
        </div>

        <Stack tokens={{ childrenGap: 20 }}>
          {/* Library Selection */}
          <Stack tokens={{ childrenGap: 8 }}>
            <Text variant="mediumPlus" styles={{ root: { fontWeight: 600 } }}>
              Target Library
            </Text>
            <Dropdown
              placeholder="Select a video library to configure"
              options={libraryOptions}
              selectedKey={selectedLibrary}
              onChange={(_, option) => setSelectedLibrary(option?.key as string || '')}
              disabled={isLoading}
              styles={{ dropdown: { width: '100%' } }}
            />
            <Text variant="small" styles={{ root: { color: '#605e5c' } }}>
              Choose which video library you want to apply AI settings to
            </Text>
          </Stack>

          {/* Template Selection */}
          <Stack tokens={{ childrenGap: 8 }}>
            <Text variant="mediumPlus" styles={{ root: { fontWeight: 600 } }}>
              AI Template
            </Text>
            <Dropdown
              placeholder="Choose an AI template to apply"
              options={templateOptions}
              selectedKey={selectedTemplate}
              onChange={(_, option) => setSelectedTemplate(option?.key as string || '')}
              disabled={isLoading || !selectedLibrary}
              styles={{ dropdown: { width: '100%' } }}
            />
            <Text variant="small" styles={{ root: { color: '#605e5c' } }}>
              Select from pre-configured templates or your custom templates
            </Text>
          </Stack>

          {/* Template Description */}
          {templateDescription && (
            <Stack tokens={{ childrenGap: 8 }}>
              <Text variant="mediumPlus" styles={{ root: { fontWeight: 600 } }}>
                Template Description
              </Text>
              <div style={{ 
                padding: '12px', 
                backgroundColor: '#f3f2f1', 
                borderRadius: '4px',
                border: '1px solid #d2d0ce'
              }}>
                <Text variant="small" styles={{ root: { lineHeight: 1.4 } }}>
                  {templateDescription}
                </Text>
              </div>
            </Stack>
          )}

          {/* Apply Button */}
          <Stack horizontal tokens={{ childrenGap: 12 }} styles={{ root: { marginTop: '16px' } }}>
            <PrimaryButton
              text={isLoading ? "Applying..." : "Apply Template"}
              onClick={applyTemplate}
              disabled={!selectedTemplate || !selectedLibrary || isLoading}
              iconProps={{ iconName: "Accept" }}
            />
          </Stack>
        </Stack>
      </div>

      {/* Available Templates Overview */}
      <div className={styles.settingSection}>
        <div className={styles.sectionHeader}>
          <h3 className={styles.sectionTitle}>Available Templates</h3>
          <p className={styles.sectionDescription}>
            Overview of all available AI templates with their categories and purposes.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
          {templates.map(template => (
            <div
              key={template.templateName}
              style={{
                padding: '16px',
                border: '1px solid #d2d0ce',
                borderRadius: '4px',
                backgroundColor: template.isSystemDefault ? '#f0f9ff' : '#ffffff',
              }}
            >
              <Stack tokens={{ childrenGap: 8 }}>
                <Stack horizontal horizontalAlign="space-between" verticalAlign="center">
                  <Text variant="mediumPlus" styles={{ root: { fontWeight: 600 } }}>
                    {template.displayName}
                  </Text>
                  <div
                    style={{
                      padding: '4px 8px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      backgroundColor: template.isSystemDefault ? '#dff6dd' : '#deecf9',
                      color: template.isSystemDefault ? '#107c10' : '#0078d4',
                    }}
                  >
                    {template.category}
                  </div>
                </Stack>
                <Text variant="small" styles={{ root: { color: '#605e5c', lineHeight: 1.3 } }}>
                  {template.description}
                </Text>
              </Stack>
            </div>
          ))}
        </div>
      </div>
    </Stack>
  );
};

export default QuickSetupTab;
