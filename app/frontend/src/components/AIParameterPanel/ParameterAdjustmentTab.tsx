import React, { useState, useEffect } from 'react';
import {
  Stack,
  Text,
  TextField,
  SpinButton,
  Slider,
  Checkbox,
  PrimaryButton,
  DefaultButton,
  MessageBarType,
  Dropdown,
  IDropdownOption,
  Separator,
  Panel,
  PanelType,
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
  frequencyPenalty: number;
  presencePenalty: number;
  stopSequences: string[];
  systemPrompt: string;
  conversationStarters: string[];
  timeoutSeconds: number;
  enableStreaming: boolean;
  enableFunctionCalling: boolean;
  maxRetries: number;
}

const ParameterAdjustmentTab: React.FC<ParameterAdjustmentTabProps> = ({
  availableLibraries,
  onMessage,
  isLoading,
  setIsLoading,
}) => {
  const [selectedLibrary, setSelectedLibrary] = useState<string>('');
  const [parameters, setParameters] = useState<AIParameters>({
    model: 'gpt-4o',
    temperature: 0.7,
    maxTokens: 2000,
    topP: 0.9,
    frequencyPenalty: 0,
    presencePenalty: 0,
    stopSequences: [],
    systemPrompt: '',
    conversationStarters: [],
    timeoutSeconds: 30,
    enableStreaming: true,
    enableFunctionCalling: false,
    maxRetries: 3,
  });
  const [isAdvancedPanelOpen, setIsAdvancedPanelOpen] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // 載入參數
  useEffect(() => {
    if (selectedLibrary) {
      loadParameters();
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
      model: 'gpt-4o',
      temperature: 0.7,
      maxTokens: 2000,
      topP: 0.9,
      frequencyPenalty: 0,
      presencePenalty: 0,
      stopSequences: [],
      systemPrompt: '',
      conversationStarters: [],
      timeoutSeconds: 30,
      enableStreaming: true,
      enableFunctionCalling: false,
      maxRetries: 3,
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
    { key: 'gpt-4o', text: 'GPT-4o (Latest)' },
    { key: 'gpt-4-turbo', text: 'GPT-4 Turbo' },
    { key: 'gpt-4', text: 'GPT-4' },
    { key: 'gpt-3.5-turbo', text: 'GPT-3.5 Turbo' },
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
                    onChange={(_, option) => updateParameter('model', option?.key as string || 'gpt-4o')}
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
                    Advanced Sampling
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
                  </Stack>

                  <Stack tokens={{ childrenGap: 12 }}>
                    <Text variant="medium">Frequency Penalty: {parameters.frequencyPenalty}</Text>
                    <Slider
                      min={-2}
                      max={2}
                      step={0.1}
                      value={parameters.frequencyPenalty}
                      onChange={(value) => updateParameter('frequencyPenalty', value)}
                      showValue={false}
                      disabled={isLoading}
                    />
                  </Stack>

                  <Stack tokens={{ childrenGap: 12 }}>
                    <Text variant="medium">Presence Penalty: {parameters.presencePenalty}</Text>
                    <Slider
                      min={-2}
                      max={2}
                      step={0.1}
                      value={parameters.presencePenalty}
                      onChange={(value) => updateParameter('presencePenalty', value)}
                      showValue={false}
                      disabled={isLoading}
                    />
                  </Stack>
                </Stack>
              </div>

              <div className={styles.parameterCard}>
                <Stack tokens={{ childrenGap: 16 }}>
                  <Text variant="mediumPlus" styles={{ root: { fontWeight: 600 } }}>
                    System Options
                  </Text>
                  
                  <Checkbox
                    label="Enable Streaming"
                    checked={parameters.enableStreaming}
                    onChange={(_, checked) => updateParameter('enableStreaming', !!checked)}
                    disabled={isLoading}
                  />

                  <Checkbox
                    label="Enable Function Calling"
                    checked={parameters.enableFunctionCalling}
                    onChange={(_, checked) => updateParameter('enableFunctionCalling', !!checked)}
                    disabled={isLoading}
                  />

                  <SpinButton
                    label="Timeout (seconds)"
                    value={parameters.timeoutSeconds.toString()}
                    onValidate={(value) => updateParameter('timeoutSeconds', parseInt(value) || 30)}
                    onIncrement={(value) => updateParameter('timeoutSeconds', (parseInt(value) || 30) + 5)}
                    onDecrement={(value) => updateParameter('timeoutSeconds', Math.max(5, (parseInt(value) || 30) - 5))}
                    min={5}
                    max={300}
                    step={5}
                    disabled={isLoading}
                  />

                  <SpinButton
                    label="Max Retries"
                    value={parameters.maxRetries.toString()}
                    onValidate={(value) => updateParameter('maxRetries', parseInt(value) || 3)}
                    onIncrement={(value) => updateParameter('maxRetries', (parseInt(value) || 3) + 1)}
                    onDecrement={(value) => updateParameter('maxRetries', Math.max(0, (parseInt(value) || 3) - 1))}
                    min={0}
                    max={10}
                    step={1}
                    disabled={isLoading}
                  />
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
            
            <DefaultButton
              text="Advanced Settings"
              onClick={() => setIsAdvancedPanelOpen(true)}
              disabled={isLoading}
              iconProps={{ iconName: "Settings" }}
            />
          </Stack>
        </>
      )}

      {/* Advanced Settings Panel */}
      <Panel
        headerText="Advanced AI Parameters"
        isOpen={isAdvancedPanelOpen}
        onDismiss={() => setIsAdvancedPanelOpen(false)}
        type={PanelType.medium}
        closeButtonAriaLabel="Close"
      >
        <Stack tokens={{ childrenGap: 20 }}>
          <TextField
            label="Stop Sequences (comma-separated)"
            value={parameters.stopSequences.join(', ')}
            onChange={(_, value) => 
              updateParameter('stopSequences', 
                value ? value.split(',').map(s => s.trim()).filter(s => s) : []
              )
            }
            placeholder="Enter stop sequences..."
            multiline
            rows={2}
            disabled={isLoading}
          />
          
          <TextField
            label="Conversation Starters (one per line)"
            value={parameters.conversationStarters.join('\n')}
            onChange={(_, value) => 
              updateParameter('conversationStarters',
                value ? value.split('\n').map(s => s.trim()).filter(s => s) : []
              )
            }
            placeholder="Enter conversation starters..."
            multiline
            rows={5}
            disabled={isLoading}
          />
          
          <Stack horizontal tokens={{ childrenGap: 12 }}>
            <PrimaryButton
              text="Apply Advanced Settings"
              onClick={() => {
                setIsAdvancedPanelOpen(false);
                onMessage('Advanced settings updated', MessageBarType.info);
              }}
              disabled={isLoading}
            />
            <DefaultButton
              text="Cancel"
              onClick={() => setIsAdvancedPanelOpen(false)}
              disabled={isLoading}
            />
          </Stack>
        </Stack>
      </Panel>
    </Stack>
  );
};

export default ParameterAdjustmentTab;
