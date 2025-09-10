import React, { useState, useEffect } from 'react';
import {
  Stack,
  Text,
  TextField,
  SpinButton,
  Slider,
  PrimaryButton,
  DefaultButton,
  MessageBarType,
  Dropdown,
  IDropdownOption,
  Separator,
} from '@fluentui/react';
import styles from './AIParameterPanel.module.css';

interface ParameterAdjustmentTabProps {
  availableLibraries: Array<{ key: string; text: string }>;
  onMessage: (text: string, type: MessageBarType) => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
}

interface AIParameters {
  model: string;
  temperature: number;
  maxTokens: number;
  topP: number;
  systemPrompt: string;
}

const ParameterAdjustmentTab: React.FC<ParameterAdjustmentTabProps> = ({
  availableLibraries,
  onMessage,
  isLoading,
  setIsLoading,
}) => {
  const [selectedLibrary, setSelectedLibrary] = useState<string>(() => {
    return localStorage.getItem('aiParameters_selectedLibrary') || '';
  });
  const [parameters, setParameters] = useState<AIParameters>({
    model: 'gpt-4.1-mini',
    temperature: 0.7,
    maxTokens: 2000,
    topP: 0.9,
    systemPrompt: '',
  });
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // 載入參數
  useEffect(() => {
    if (selectedLibrary) {
      loadParameters();
    }
  }, [selectedLibrary]);

  // Persist selectedLibrary to localStorage
  useEffect(() => {
    if (selectedLibrary) {
      localStorage.setItem('aiParameters_selectedLibrary', selectedLibrary);
    } else {
      localStorage.removeItem('aiParameters_selectedLibrary');
    }
  }, [selectedLibrary]);

  const loadParameters = async () => {
    if (!selectedLibrary) return;
    
    try {
      setIsLoading(true);
      const response = await fetch(`/api/libraries/${selectedLibrary}/ai-parameters`);
      if (!response.ok) throw new Error('Failed to load parameters');
      
      const params = await response.json();
      setParameters(params);
      setHasUnsavedChanges(false);
    } catch (error) {
      console.error('Error loading parameters:', error);
      onMessage('Failed to load AI parameters', MessageBarType.error);
    } finally {
      setIsLoading(false);
    }
  };

  const saveParameters = async () => {
    if (!selectedLibrary) return;
    
    try {
      setIsLoading(true);
      const response = await fetch(`/api/libraries/${selectedLibrary}/ai-parameters`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(parameters),
      });
      
      if (!response.ok) throw new Error('Failed to save parameters');
      
      setHasUnsavedChanges(false);
      onMessage('AI parameters saved successfully', MessageBarType.success);
    } catch (error) {
      console.error('Error saving parameters:', error);
      onMessage('Failed to save AI parameters', MessageBarType.error);
    } finally {
      setIsLoading(false);
    }
  };

  const resetToDefaults = () => {
    setParameters({
      model: 'gpt-4.1-mini',
      temperature: 0.7,
      maxTokens: 2000,
      topP: 0.9,
      systemPrompt: '',
    });
    setHasUnsavedChanges(true);
  };

  const updateParameter = <K extends keyof AIParameters>(
    key: K,
    value: AIParameters[K]
  ) => {
    // Validate temperature range
    if (key === 'temperature' && typeof value === 'number') {
      value = Math.max(0, Math.min(1, value)) as AIParameters[K];
    }
    setParameters(prev => ({ ...prev, [key]: value }));
    setHasUnsavedChanges(true);
  };

  const libraryOptions: IDropdownOption[] = availableLibraries.map(lib => ({
    key: lib.key,
    text: lib.text,
  }));

  const modelOptions: IDropdownOption[] = [
    { key: 'gpt-4.1-mini', text: 'GPT-4.1 Mini (Available)' },
  ];

  return (
    <Stack tokens={{ childrenGap: 24 }}>
      {/* Library Selection */}
      <div className={styles.settingSection}>
        <div className={styles.sectionHeader}>
          <h3 className={styles.sectionTitle}>Target Library Configuration</h3>
          <p className={styles.sectionDescription}>
            Select a video library to configure its AI parameters. Each library can have customized settings.
          </p>
        </div>

        <Stack tokens={{ childrenGap: 12 }}>
          <Dropdown
            label="Target Library"
            placeholder="Select a video library to configure"
            options={libraryOptions}
            selectedKey={selectedLibrary}
            onChange={(_, option) => setSelectedLibrary(option?.key as string || '')}
            disabled={isLoading}
            required
          />
          
          {hasUnsavedChanges && (
            <Text variant="small" styles={{ root: { color: '#d83b01', fontStyle: 'italic' } }}>
              You have unsaved changes. Don't forget to save your configuration.
            </Text>
          )}
        </Stack>
      </div>

      {selectedLibrary && (
        <>
          {/* Core Parameters */}
          <div className={styles.settingSection}>
            <div className={styles.sectionHeader}>
              <h3 className={styles.sectionTitle}>Core AI Parameters</h3>
              <p className={styles.sectionDescription}>
                Essential settings that control AI behavior and response generation.
              </p>
            </div>

            <div className={styles.parameterGrid}>
              <div className={styles.parameterCard}>
                <Stack tokens={{ childrenGap: 16 }}>
                  <Text variant="mediumPlus" styles={{ root: { fontWeight: 600 } }}>
                    Model Configuration
                  </Text>
                  
                  <Dropdown
                    label="AI Model"
                    options={modelOptions}
                    selectedKey={parameters.model}
                    onChange={(_, option) => updateParameter('model', option?.key as string || 'gpt-4.1-mini')}
                    disabled={isLoading}
                  />
                  
                  <TextField
                    label="System Prompt"
                    multiline
                    rows={4}
                    value={parameters.systemPrompt}
                    onChange={(_, value) => updateParameter('systemPrompt', value || '')}
                    placeholder="Enter system prompt that defines AI behavior..."
                    disabled={isLoading}
                  />
                </Stack>
              </div>

              <div className={styles.parameterCard}>
                <Stack tokens={{ childrenGap: 16 }}>
                  <Text variant="mediumPlus" styles={{ root: { fontWeight: 600 } }}>
                    Response Generation
                  </Text>
                  
                  <Stack tokens={{ childrenGap: 12 }}>
                    <Text variant="medium">Temperature: {parameters.temperature}</Text>
                    <Slider
                      min={0}
                      max={1}
                      step={0.1}
                      value={parameters.temperature}
                      onChange={(value) => updateParameter('temperature', value)}
                      showValue={false}
                      disabled={isLoading}
                    />
                    <Text variant="small" styles={{ root: { color: '#605e5c' } }}>
                      Lower values make responses more focused and deterministic
                    </Text>
                  </Stack>

                  <SpinButton
                    label="Max Tokens"
                    value={parameters.maxTokens.toString()}
                    onValidate={(value) => updateParameter('maxTokens', parseInt(value) || 2000)}
                    onIncrement={(value) => updateParameter('maxTokens', (parseInt(value) || 2000) + 100)}
                    onDecrement={(value) => updateParameter('maxTokens', Math.max(100, (parseInt(value) || 2000) - 100))}
                    min={100}
                    max={8000}
                    step={100}
                    disabled={isLoading}
                  />
                </Stack>
              </div>

              <div className={styles.parameterCard}>
                <Stack tokens={{ childrenGap: 16 }}>
                  <Text variant="mediumPlus" styles={{ root: { fontWeight: 600 } }}>
                    Advanced Control
                  </Text>
                  
                  <Stack tokens={{ childrenGap: 12 }}>
                    <Text variant="medium">Top P: {parameters.topP}</Text>
                    <Slider
                      min={0}
                      max={1}
                      step={0.05}
                      value={parameters.topP}
                      onChange={(value) => updateParameter('topP', value)}
                      showValue={false}
                      disabled={isLoading}
                    />
                    <Text variant="small" styles={{ root: { color: '#605e5c' } }}>
                      Controls response diversity - lower values for more focused responses
                    </Text>
                  </Stack>
                </Stack>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <Separator />
          
          <Stack horizontal tokens={{ childrenGap: 12 }} horizontalAlign="start">
            <PrimaryButton
              text={isLoading ? "Saving..." : "Save Parameters"}
              onClick={saveParameters}
              disabled={!hasUnsavedChanges || isLoading}
              iconProps={{ iconName: "Save" }}
            />
            
            <DefaultButton
              text="Reset to Defaults"
              onClick={resetToDefaults}
              disabled={isLoading}
              iconProps={{ iconName: "Refresh" }}
            />
            
          </Stack>
        </>
      )}

    </Stack>
  );
};

export default ParameterAdjustmentTab;
