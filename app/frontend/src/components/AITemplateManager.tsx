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
  Separator,
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

interface AITemplateManagerProps {
  selectedLibrary: string;
  onTemplateApplied: (template: AITemplate) => void;
  onSettingsChanged: (settings: any) => void;
}

const AITemplateManager: React.FC<AITemplateManagerProps> = ({
  selectedLibrary,
  onTemplateApplied,
  onSettingsChanged,
}) => {
  const [templates, setTemplates] = useState<AITemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: MessageBarType } | null>(null);
  
  // Template management state
  const [showTemplateDialog, setShowTemplateDialog] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<AITemplate | null>(null);
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

  // Load templates on component mount
  useEffect(() => {
    loadTemplates();
  }, []);

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

  const applyTemplate = async () => {
    if (!selectedTemplate || !selectedLibrary) return;
    
    try {
      setLoading(true);
      const response = await fetch(`/api/templates/${selectedTemplate}/apply-to/${selectedLibrary}`, {
        method: 'POST',
      });
      
      if (!response.ok) throw new Error('Failed to apply template');
      
      const result = await response.json();
      
      // Get the applied template details
      const template = templates.find(t => t.templateName === selectedTemplate);
      if (template) {
        onTemplateApplied(template);
        onSettingsChanged({
          promptTemplate: template.promptTemplate,
          temperature: template.temperature,
          maxTokens: template.maxTokens,
          semanticRanker: template.semanticRanker,
        });
      }
      
      setMessage({ text: result.message, type: MessageBarType.success });
    } catch (error) {
      console.error('Error applying template:', error);
      setMessage({ text: 'Failed to apply template', type: MessageBarType.error });
    } finally {
      setLoading(false);
    }
  };

  const openTemplateDialog = (template?: AITemplate) => {
    if (template) {
      setEditingTemplate(template);
      setTemplateForm({ ...template });
    } else {
      setEditingTemplate(null);
      setTemplateForm({
        templateName: '',
        displayName: '',
        description: '',
        category: 'Custom',
        promptTemplate: '',
        temperature: 0.7,
        maxTokens: 800,
        semanticRanker: true,
      });
    }
    setShowTemplateDialog(true);
  };

  const saveTemplate = async () => {
    try {
      setLoading(true);
      
      const url = editingTemplate 
        ? `/api/templates/${editingTemplate.templateName}`
        : '/api/templates';
      const method = editingTemplate ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(templateForm),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to save template');
      }
      
      await loadTemplates();
      setShowTemplateDialog(false);
      setMessage({ 
        text: editingTemplate ? 'Template updated successfully' : 'Template created successfully', 
        type: MessageBarType.success 
      });
    } catch (error) {
      console.error('Error saving template:', error);
      setMessage({ text: (error as Error).message, type: MessageBarType.error });
    } finally {
      setLoading(false);
    }
  };


  const templateOptions: IDropdownOption[] = templates.map(template => ({
    key: template.templateName,
    text: `${template.isSystemDefault ? '🏛️' : '📝'} ${template.displayName}`,
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
    <Stack tokens={{ childrenGap: 16 }}>
      {message && (
        <MessageBar
          messageBarType={message.type}
          onDismiss={() => setMessage(null)}
        >
          {message.text}
        </MessageBar>
      )}
      
      <Stack tokens={{ childrenGap: 8 }}>
        <Text variant="mediumPlus" styles={{ root: { fontWeight: 600 } }}>
          🎯 AI Template Quick Apply
        </Text>
        
        <Dropdown
          label="Select AI Template"
          placeholder="Choose a template to apply"
          options={templateOptions}
          selectedKey={selectedTemplate}
          onChange={(_, option) => setSelectedTemplate(option?.key as string || '')}
          disabled={loading}
        />
        
        <Stack horizontal tokens={{ childrenGap: 8 }}>
          <PrimaryButton
            text="Apply Template"
            onClick={applyTemplate}
            disabled={!selectedTemplate || !selectedLibrary || loading}
          />
          <DefaultButton
            text="Template Manager"
            onClick={() => openTemplateDialog()}
          />
        </Stack>
      </Stack>

      <Separator />
      
      <Stack tokens={{ childrenGap: 8 }}>
        <Text variant="mediumPlus" styles={{ root: { fontWeight: 600 } }}>
          💾 Template Operations
        </Text>
        
        <Stack horizontal tokens={{ childrenGap: 8 }}>
          <DefaultButton
            text="Save as New Template"
            onClick={() => openTemplateDialog()}
          />
          <DefaultButton
            text="Update Current Template"
            onClick={() => {
              if (selectedTemplate) {
                const template = templates.find(t => t.templateName === selectedTemplate);
                if (template && !template.isSystemDefault) {
                  openTemplateDialog(template);
                } else {
                  setMessage({ text: 'Cannot modify system default templates', type: MessageBarType.warning });
                }
              }
            }}
            disabled={!selectedTemplate}
          />
        </Stack>
      </Stack>

      {/* Template Management Dialog */}
      <Dialog
        hidden={!showTemplateDialog}
        onDismiss={() => setShowTemplateDialog(false)}
        dialogContentProps={{
          type: DialogType.largeHeader,
          title: editingTemplate ? 'Edit AI Template' : 'Create New AI Template',
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
              disabled={!!editingTemplate}
              required
            />
            <TextField
              label="Display Name"
              value={templateForm.displayName}
              onChange={(_, value) => setTemplateForm(prev => ({ ...prev, displayName: value || '' }))}
              required
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
          />
          
          <TextField
            label="Prompt Template"
            value={templateForm.promptTemplate}
            onChange={(_, value) => setTemplateForm(prev => ({ ...prev, promptTemplate: value || '' }))}
            multiline
            rows={8}
            required
          />
          
          <Stack horizontal tokens={{ childrenGap: 16 }}>
            <Stack styles={{ root: { minWidth: 200 } }}>
              <Text>Temperature: {templateForm.temperature}</Text>
              <Slider
                min={0.1}
                max={2.0}
                step={0.1}
                value={templateForm.temperature}
                onChange={(value) => setTemplateForm(prev => ({ ...prev, temperature: value }))}
              />
            </Stack>
            
            <SpinButton
              label="Max Tokens"
              value={templateForm.maxTokens?.toString()}
              onValidate={(value) => {
                const numValue = parseInt(value);
                setTemplateForm(prev => ({ ...prev, maxTokens: numValue }));
                return String(numValue);
              }}
              min={100}
              max={4000}
              step={100}
            />
          </Stack>
          
          <Toggle
            label="Semantic Ranker"
            checked={templateForm.semanticRanker}
            onChange={(_, checked) => setTemplateForm(prev => ({ ...prev, semanticRanker: !!checked }))}
          />
        </Stack>
        
        <DialogFooter>
          <PrimaryButton
            onClick={saveTemplate}
            text={editingTemplate ? "Update Template" : "Create Template"}
            disabled={loading || !templateForm.templateName || !templateForm.displayName || !templateForm.promptTemplate}
          />
          <DefaultButton
            onClick={() => setShowTemplateDialog(false)}
            text="Cancel"
          />
        </DialogFooter>
      </Dialog>
    </Stack>
  );
};

export default AITemplateManager;
