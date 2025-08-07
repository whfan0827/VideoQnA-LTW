import React, { useState, useEffect } from 'react';
import {
  Stack,
  Text,
  Dropdown,
  IDropdownOption,
  PrimaryButton,
  DefaultButton,
  MessageBar,
  MessageBarType,
  Dialog,
  DialogType,
  DialogFooter,
  TextField,
  ComboBox,
  IComboBoxOption,
  Slider,
  SpinButton,
  Toggle,
  Label,
  Separator,
  Position,
} from '@fluentui/react';

interface AITemplate {
  id?: number;
  templateName: string;
  displayName: string;
  description?: string;
  category: string;
  promptTemplate: string;
  temperature: number;
  maxTokens: number;
  semanticRanker: boolean;
  isSystemDefault: boolean;
  createdBy: string;
  createdAt?: string;
  updatedAt?: string;
}

interface AIConfigurationProps {
  selectedLibrary: string;
  onSettingsChanged: (settings: any) => void;
}

const AIConfiguration: React.FC<AIConfigurationProps> = ({
  selectedLibrary,
  onSettingsChanged,
}) => {
  const [templates, setTemplates] = useState<AITemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: MessageBarType } | null>(null);
  
  // Current AI configuration state
  const [aiConfig, setAiConfig] = useState({
    promptTemplate: '',
    temperature: 0.7,
    maxTokens: 800,
    semanticRanker: true,
    isFromTemplate: false,
    currentTemplateName: ''
  });
  
  // Template management state
  const [showTemplateDialog, setShowTemplateDialog] = useState(false);
  const [templateForm, setTemplateForm] = useState<Partial<AITemplate>>({
    templateName: '',
    displayName: '',
    description: '',
    category: 'Custom',
    promptTemplate: '',
    temperature: 0.7,
    maxTokens: 800,
    semanticRanker: true,
  });

  // Load templates and current settings on component mount
  useEffect(() => {
    loadTemplates();
    if (selectedLibrary) {
      loadCurrentSettings();
    }
  }, [selectedLibrary]);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/templates');
      if (!response.ok) throw new Error('Failed to load templates');
      
      const templatesData = await response.json();
      setTemplates(templatesData);
    } catch (error) {
      console.error('Error loading templates:', error);
      setMessage({ text: 'Failed to load AI templates', type: MessageBarType.error });
    } finally {
      setLoading(false);
    }
  };

  const loadCurrentSettings = async () => {
    try {
      const response = await fetch(`/settings/${selectedLibrary}`);
      if (!response.ok) throw new Error('Failed to load current settings');
      
      const settings = await response.json();
      setAiConfig({
        promptTemplate: settings.promptTemplate || '',
        temperature: settings.temperature || 0.7,
        maxTokens: settings.maxTokens || 800,
        semanticRanker: settings.semanticRanker !== false,
        isFromTemplate: false,
        currentTemplateName: ''
      });
    } catch (error) {
      console.error('Error loading current settings:', error);
    }
  };

  const applyTemplate = async () => {
    if (!selectedTemplate || !selectedLibrary) return;
    
    try {
      setLoading(true);
      const response = await fetch(`/api/templates/${selectedTemplate}/apply-to/${selectedLibrary}`, {
        method: 'POST',
      });
      
      if (!response.ok) throw new Error('Failed to apply template');
      
      // Get the applied template details and update local state
      const template = templates.find(t => t.templateName === selectedTemplate);
      if (template) {
        const newConfig = {
          promptTemplate: template.promptTemplate,
          temperature: template.temperature,
          maxTokens: template.maxTokens,
          semanticRanker: template.semanticRanker,
          isFromTemplate: true,
          currentTemplateName: template.displayName
        };
        
        setAiConfig(newConfig);
        onSettingsChanged(newConfig);
        setMessage({ text: `Template "${template.displayName}" applied successfully`, type: MessageBarType.success });
      }
    } catch (error) {
      console.error('Error applying template:', error);
      setMessage({ text: 'Failed to apply template', type: MessageBarType.error });
    } finally {
      setLoading(false);
    }
  };

  const saveCurrentSettings = async () => {
    if (!selectedLibrary) return;
    
    try {
      setLoading(true);
      const settingsData = {
        prompt_template: aiConfig.promptTemplate,
        temperature: aiConfig.temperature,
        max_tokens: aiConfig.maxTokens,
        semantic_ranker: aiConfig.semanticRanker
      };
      
      const response = await fetch(`/settings/${selectedLibrary}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settingsData),
      });
      
      if (!response.ok) throw new Error('Failed to save settings');
      
      setAiConfig(prev => ({ ...prev, isFromTemplate: false, currentTemplateName: '' }));
      setMessage({ text: 'Settings saved successfully', type: MessageBarType.success });
    } catch (error) {
      console.error('Error saving settings:', error);
      setMessage({ text: 'Failed to save settings', type: MessageBarType.error });
    } finally {
      setLoading(false);
    }
  };

  const resetToDefaults = async () => {
    if (!selectedLibrary) return;
    
    if (!confirm('Are you sure you want to reset to factory defaults? This will remove all custom settings for this library.')) {
      return;
    }
    
    try {
      setLoading(true);
      const response = await fetch(`/settings/${selectedLibrary}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) throw new Error('Failed to reset settings');
      
      // Reload default settings
      await loadCurrentSettings();
      setMessage({ text: 'Settings reset to factory defaults', type: MessageBarType.success });
    } catch (error) {
      console.error('Error resetting settings:', error);
      setMessage({ text: 'Failed to reset settings', type: MessageBarType.error });
    } finally {
      setLoading(false);
    }
  };

  const saveAsTemplate = () => {
    setTemplateForm({
      templateName: '',
      displayName: '',
      description: '',
      category: 'Custom',
      promptTemplate: aiConfig.promptTemplate,
      temperature: aiConfig.temperature,
      maxTokens: aiConfig.maxTokens,
      semanticRanker: aiConfig.semanticRanker,
    });
    setShowTemplateDialog(true);
  };

  const createTemplate = async () => {
    try {
      setLoading(true);
      
      const response = await fetch('/api/templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(templateForm),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to create template');
      }
      
      await loadTemplates();
      setShowTemplateDialog(false);
      setMessage({ text: 'Template created successfully', type: MessageBarType.success });
    } catch (error) {
      console.error('Error creating template:', error);
      setMessage({ text: (error as Error).message, type: MessageBarType.error });
    } finally {
      setLoading(false);
    }
  };

  const handleConfigChange = (field: keyof typeof aiConfig, value: any) => {
    const newConfig = {
      ...aiConfig,
      [field]: value,
      isFromTemplate: false,
      currentTemplateName: ''
    };
    setAiConfig(newConfig);
    onSettingsChanged(newConfig);
  };

  const templateOptions: IDropdownOption[] = templates.map(template => ({
    key: template.templateName,
    text: `${template.isSystemDefault ? '[System] ' : '[Custom] '}${template.displayName}`,
    data: template,
  }));

  const categoryOptions: IComboBoxOption[] = [
    { key: 'HR', text: 'HR' },
    { key: 'Technical', text: 'Technical' },
    { key: 'Creative', text: 'Creative' },
    { key: 'Education', text: 'Education' },
    { key: 'Custom', text: 'Custom' },
  ];

  return (
    <div style={{ padding: '16px', border: '1px solid #d1d1d1', borderRadius: '4px' }}>
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
        <Text variant="xLarge" styles={{ root: { fontWeight: 600 } }}>
          AI Configuration & Templates
        </Text>
        
        {/* Quick Start: Apply Template */}
        <Stack tokens={{ childrenGap: 12 }}>
          <Text variant="mediumPlus" styles={{ root: { fontWeight: 600 } }}>
            Quick Start: Apply Template
          </Text>
          
          <Dropdown
            label="Select AI Template"
            placeholder="Choose a template to apply"
            options={templateOptions}
            selectedKey={selectedTemplate}
            onChange={(_, option) => setSelectedTemplate(option?.key as string || '')}
            disabled={loading || !selectedLibrary}
          />
          
          <Stack horizontal tokens={{ childrenGap: 8 }}>
            <PrimaryButton
              text="Apply Template"
              onClick={applyTemplate}
              disabled={!selectedTemplate || !selectedLibrary || loading}
            />
            <DefaultButton
              text="Manage Templates"
              onClick={() => setShowTemplateDialog(true)}
            />
          </Stack>
        </Stack>

        <Separator />
        
        {/* Custom Configuration */}
        <Stack tokens={{ childrenGap: 16 }}>
          <Stack horizontal horizontalAlign="space-between" verticalAlign="center">
            <Text variant="mediumPlus" styles={{ root: { fontWeight: 600 } }}>
              Custom Configuration
            </Text>
            {aiConfig.isFromTemplate && (
              <Text variant="small" styles={{ root: { fontStyle: 'italic', color: '#0078d4' } }}>
                Based on template: {aiConfig.currentTemplateName}
              </Text>
            )}
          </Stack>
          
          {/* Prompt Template */}
          <Stack tokens={{ childrenGap: 8 }}>
            <Label>Prompt Template</Label>
            <Text variant="small" styles={{ root: { color: '#666' } }}>
              Customize how the AI interprets and responds to questions. The system will automatically inject video content and user questions.
            </Text>
            <TextField
              multiline
              rows={8}
              value={aiConfig.promptTemplate}
              onChange={(_, value) => handleConfigChange('promptTemplate', value || '')}
              placeholder="Enter your custom prompt template..."
              disabled={!selectedLibrary}
              styles={{ 
                field: { 
                  fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                  fontSize: '12px',
                  lineHeight: '1.4'
                }
              }}
            />
          </Stack>
          
          {/* Model Parameters */}
          <Stack tokens={{ childrenGap: 16 }}>
            <Label>Model Parameters</Label>
            
            <Stack horizontal tokens={{ childrenGap: 24 }} wrap>
              <Stack styles={{ root: { minWidth: 200 } }}>
                <Label>Temperature: {aiConfig.temperature}</Label>
                <Text variant="small" styles={{ root: { color: '#666', marginBottom: '8px' } }}>
                  Controls response creativity (0.1 = focused, 2.0 = creative)
                </Text>
                <Slider
                  min={0.1}
                  max={2.0}
                  step={0.1}
                  value={aiConfig.temperature}
                  onChange={(value) => handleConfigChange('temperature', value)}
                  disabled={!selectedLibrary}
                />
              </Stack>
              
              <Stack styles={{ root: { minWidth: 150 } }}>
                <SpinButton
                  label="Max Tokens"
                  labelPosition={Position.top}
                  value={aiConfig.maxTokens?.toString()}
                  onValidate={(value) => {
                    const numValue = parseInt(value) || 800;
                    handleConfigChange('maxTokens', numValue);
                    return String(numValue);
                  }}
                  min={100}
                  max={4000}
                  step={100}
                  disabled={!selectedLibrary}
                />
                <Text variant="small" styles={{ root: { color: '#666' } }}>
                  Maximum response length
                </Text>
              </Stack>
              
              <Stack>
                <Toggle
                  label="Semantic Ranker"
                  checked={aiConfig.semanticRanker}
                  onChange={(_, checked) => handleConfigChange('semanticRanker', !!checked)}
                  disabled={!selectedLibrary}
                />
                <Text variant="small" styles={{ root: { color: '#666' } }}>
                  Use AI-powered search
                </Text>
              </Stack>
            </Stack>
          </Stack>
          
          {/* Actions */}
          <Stack horizontal tokens={{ childrenGap: 12 }} wrap>
            <PrimaryButton
              text="Save to Library"
              onClick={saveCurrentSettings}
              disabled={!selectedLibrary || loading}
            />
            <DefaultButton
              text="Save as Template"
              onClick={saveAsTemplate}
              disabled={!selectedLibrary || !aiConfig.promptTemplate}
            />
            <DefaultButton
              text="Reset to Factory Defaults"
              onClick={resetToDefaults}
              disabled={!selectedLibrary || loading}
            />
          </Stack>
        </Stack>
      </Stack>

      {/* Template Management Dialog */}
      <Dialog
        hidden={!showTemplateDialog}
        onDismiss={() => setShowTemplateDialog(false)}
        dialogContentProps={{
          type: DialogType.largeHeader,
          title: 'Create New AI Template',
        }}
        modalProps={{
          isBlocking: true,
          dragOptions: undefined,
        }}
        maxWidth="600px"
      >
        <Stack tokens={{ childrenGap: 16 }}>
          <Stack horizontal tokens={{ childrenGap: 16 }}>
            <TextField
              label="Template Name"
              value={templateForm.templateName}
              onChange={(_, value) => setTemplateForm(prev => ({ ...prev, templateName: value || '' }))}
              required
              description="Unique identifier (lowercase, no spaces)"
            />
            <TextField
              label="Display Name"
              value={templateForm.displayName}
              onChange={(_, value) => setTemplateForm(prev => ({ ...prev, displayName: value || '' }))}
              required
              description="Human-readable name"
            />
          </Stack>
          
          <ComboBox
            label="Category"
            options={categoryOptions}
            selectedKey={templateForm.category}
            onChange={(_, option) => setTemplateForm(prev => ({ ...prev, category: option?.key as string || 'Custom' }))}
            allowFreeform
          />
          
          <TextField
            label="Description"
            value={templateForm.description}
            onChange={(_, value) => setTemplateForm(prev => ({ ...prev, description: value || '' }))}
            multiline
            rows={2}
            description="Brief description of template purpose"
          />
          
          <TextField
            label="Prompt Template"
            value={templateForm.promptTemplate}
            onChange={(_, value) => setTemplateForm(prev => ({ ...prev, promptTemplate: value || '' }))}
            multiline
            rows={6}
            required
            styles={{ 
              field: { 
                fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                fontSize: '12px'
              }
            }}
          />
        </Stack>
        
        <DialogFooter>
          <PrimaryButton
            onClick={createTemplate}
            text="Create Template"
            disabled={loading || !templateForm.templateName || !templateForm.displayName || !templateForm.promptTemplate}
          />
          <DefaultButton
            onClick={() => setShowTemplateDialog(false)}
            text="Cancel"
          />
        </DialogFooter>
      </Dialog>
    </div>
  );
};

export default AIConfiguration;
