import React, { useState, useEffect } from 'react';
import {
  Stack,
  Text,
  TextField,
  PrimaryButton,
  DefaultButton,
  IconButton,
  MessageBarType,
  Dropdown,
  IDropdownOption,
  DetailsList,
  IColumn,
  SelectionMode,
  CommandBar,
  ICommandBarItemProps,
  Dialog,
  DialogType,
  DialogFooter,
  MessageBar,
  Spinner,
  SpinnerSize,
} from '@fluentui/react';
import styles from './AIParameterPanel.module.css';

interface TemplateManagementTabProps {
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
  promptTemplate: string;
  temperature: number;
  maxTokens: number;
  semanticRanker: boolean;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

interface NewTemplateForm {
  displayName: string;
  description: string;
  category: string;
  copyFromTemplate?: string;
}

const TemplateManagementTab: React.FC<TemplateManagementTabProps> = ({
  onMessage,
  isLoading,
  setIsLoading,
}) => {
  const [templates, setTemplates] = useState<AITemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<AITemplate | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [templateToDelete, setTemplateToDelete] = useState<AITemplate | null>(null);
  const [newTemplateForm, setNewTemplateForm] = useState<NewTemplateForm>({
    displayName: '',
    description: '',
    category: '',
    copyFromTemplate: '',
  });

  // Persist selected template ID
  useEffect(() => {
    if (selectedTemplate) {
      localStorage.setItem('templateManagement_selectedTemplateName', selectedTemplate.templateName);
    } else {
      localStorage.removeItem('templateManagement_selectedTemplateName');
    }
  }, [selectedTemplate]);

  // Restore selected template when templates are loaded
  useEffect(() => {
    if (templates.length > 0) {
      const savedTemplateName = localStorage.getItem('templateManagement_selectedTemplateName');
      if (savedTemplateName) {
        const template = templates.find(t => t.templateName === savedTemplateName);
        if (template) {
          setSelectedTemplate(template);
        }
      }
    }
  }, [templates]);

  useEffect(() => {
    loadTemplates();
  }, []);

  // Add some test data if templates are empty and not loading
  useEffect(() => {
    if (!isLoading && templates.length === 0) {
      console.log('No templates from API, check backend connection');
      // You can uncomment the below lines to test UI with sample data:
      /*
      setTemplates([
        {
          templateName: 'test-template',
          displayName: 'Test Template',
          description: 'This is a test template to verify the UI works',
          category: 'Test',
          isSystemDefault: false,
          promptTemplate: 'You are a test assistant.',
          temperature: 0.7,
          maxTokens: 800,
          semanticRanker: true,
          createdBy: 'System',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        }
      ]);
      */
    }
  }, [isLoading, templates.length]);

  const loadTemplates = async () => {
    try {
      setIsLoading(true);
      console.log('Loading templates from /api/templates');
      const response = await fetch('/api/templates');
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        console.error('Response not ok:', response.statusText);
        throw new Error('Failed to load templates');
      }
      
      const templatesData = await response.json();
      console.log('Templates data received:', templatesData);
      setTemplates(templatesData);
    } catch (error) {
      console.error('Error loading templates:', error);
      onMessage('Failed to load templates', MessageBarType.error);
    } finally {
      setIsLoading(false);
    }
  };

  const createTemplate = async () => {
    if (!newTemplateForm.displayName || !newTemplateForm.description || !newTemplateForm.category) {
      onMessage('Please fill in all required fields', MessageBarType.warning);
      return;
    }

    try {
      setIsLoading(true);
      const payload = {
        templateName: newTemplateForm.displayName.toLowerCase().replace(/\s+/g, '-'),
        displayName: newTemplateForm.displayName,
        description: newTemplateForm.description,
        category: newTemplateForm.category,
        promptTemplate: "You are a helpful AI assistant. Answer questions based on the provided video content.",
        temperature: 0.7,
        maxTokens: 800,
        semanticRanker: true,
        copyFromTemplate: newTemplateForm.copyFromTemplate || null,
      };
      
      const response = await fetch('/api/templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      
      if (!response.ok) throw new Error('Failed to create template');
      
      onMessage(`Template "${newTemplateForm.displayName}" created successfully`, MessageBarType.success);
      setIsCreateDialogOpen(false);
      setNewTemplateForm({ displayName: '', description: '', category: '', copyFromTemplate: '' });
      await loadTemplates();
    } catch (error) {
      console.error('Error creating template:', error);
      onMessage('Failed to create template', MessageBarType.error);
    } finally {
      setIsLoading(false);
    }
  };

  const deleteTemplate = async () => {
    if (!templateToDelete) return;

    try {
      setIsLoading(true);
      const response = await fetch(`/api/templates/${templateToDelete.templateName}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) throw new Error('Failed to delete template');
      
      onMessage(`Template "${templateToDelete.displayName}" deleted successfully`, MessageBarType.success);
      setIsDeleteDialogOpen(false);
      setTemplateToDelete(null);
      setSelectedTemplate(null);
      await loadTemplates();
    } catch (error) {
      console.error('Error deleting template:', error);
      onMessage('Failed to delete template', MessageBarType.error);
    } finally {
      setIsLoading(false);
    }
  };

  const duplicateTemplate = async (template: AITemplate) => {
    try {
      setIsLoading(true);
      const payload = {
        displayName: `${template.displayName} (Copy)`,
        description: `Copy of ${template.description}`,
        category: template.category,
        copyFromTemplate: template.templateName,
      };
      
      const response = await fetch('/api/templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      
      if (!response.ok) throw new Error('Failed to duplicate template');
      
      onMessage(`Template duplicated successfully`, MessageBarType.success);
      await loadTemplates();
    } catch (error) {
      console.error('Error duplicating template:', error);
      onMessage('Failed to duplicate template', MessageBarType.error);
    } finally {
      setIsLoading(false);
    }
  };

  const exportTemplate = (template: AITemplate) => {
    const templateData = {
      displayName: template.displayName,
      description: template.description,
      category: template.category,
      promptTemplate: template.promptTemplate,
      temperature: template.temperature,
      maxTokens: template.maxTokens,
      semanticRanker: template.semanticRanker,
    };
    
    const blob = new Blob([JSON.stringify(templateData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${template.templateName}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    onMessage('Template exported successfully', MessageBarType.success);
  };

  const templateColumns: IColumn[] = [
    {
      key: 'displayName',
      name: 'Name',
      fieldName: 'displayName',
      minWidth: 200,
      maxWidth: 300,
      onRender: (item: AITemplate) => (
        <Stack tokens={{ childrenGap: 4 }}>
          <Text variant="medium" styles={{ root: { fontWeight: 600 } }}>
            {item.displayName}
          </Text>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <div
              style={{
                padding: '2px 6px',
                borderRadius: '10px',
                fontSize: '11px',
                backgroundColor: item.isSystemDefault ? '#dff6dd' : '#deecf9',
                color: item.isSystemDefault ? '#107c10' : '#0078d4',
              }}
            >
              {item.isSystemDefault ? 'System' : 'Custom'}
            </div>
            <Text variant="xSmall" styles={{ root: { color: '#605e5c' } }}>
              {item.category}
            </Text>
          </div>
        </Stack>
      ),
    },
    {
      key: 'description',
      name: 'Description',
      fieldName: 'description',
      minWidth: 300,
      maxWidth: 500,
      onRender: (item: AITemplate) => (
        <Text variant="small" styles={{ root: { lineHeight: 1.3 } }}>
          {item.description}
        </Text>
      ),
    },
    {
      key: 'parameters',
      name: 'Key Parameters',
      minWidth: 150,
      maxWidth: 200,
      onRender: (item: AITemplate) => (
        <Stack tokens={{ childrenGap: 2 }}>
          <Text variant="xSmall">Template: {item.promptTemplate ? 'Custom' : 'Default'}</Text>
          <Text variant="xSmall">Temp: {item.temperature}</Text>
          <Text variant="xSmall">Tokens: {item.maxTokens}</Text>
        </Stack>
      ),
    },
    {
      key: 'actions',
      name: 'Actions',
      minWidth: 120,
      maxWidth: 120,
      onRender: (item: AITemplate) => (
        <Stack horizontal tokens={{ childrenGap: 4 }}>
          <IconButton
            iconProps={{ iconName: 'Copy' }}
            title="Duplicate template"
            onClick={() => duplicateTemplate(item)}
            disabled={isLoading}
          />
          <IconButton
            iconProps={{ iconName: 'Download' }}
            title="Export template"
            onClick={() => exportTemplate(item)}
            disabled={isLoading}
          />
          {!item.isSystemDefault && (
            <IconButton
              iconProps={{ iconName: 'Delete' }}
              title="Delete template"
              onClick={() => {
                setTemplateToDelete(item);
                setIsDeleteDialogOpen(true);
              }}
              disabled={isLoading}
              styles={{ icon: { color: '#d83b01' } }}
            />
          )}
        </Stack>
      ),
    },
  ];

  const commandBarItems: ICommandBarItemProps[] = [
    {
      key: 'newTemplate',
      text: 'New Template',
      iconProps: { iconName: 'Add' },
      onClick: () => setIsCreateDialogOpen(true),
      disabled: isLoading,
    },
    {
      key: 'refresh',
      text: 'Refresh',
      iconProps: { iconName: 'Refresh' },
      onClick: loadTemplates,
      disabled: isLoading,
    },
  ];

  const categoryOptions: IDropdownOption[] = [
    { key: 'General', text: 'General Purpose' },
    { key: 'Educational', text: 'Educational Content' },
    { key: 'Technical', text: 'Technical Documentation' },
    { key: 'Creative', text: 'Creative Content' },
    { key: 'Business', text: 'Business & Professional' },
    { key: 'Custom', text: 'Custom Category' },
  ];

  const availableTemplatesForCopy: IDropdownOption[] = [
    { key: '', text: 'Create from scratch' },
    ...templates.map(t => ({
      key: t.templateName,
      text: `${t.isSystemDefault ? '[System] ' : '[Custom] '}${t.displayName}`,
    })),
  ];

  if (isLoading && templates.length === 0) {
    return (
      <div className={styles.loadingSpinner}>
        <Spinner size={SpinnerSize.large} label="Loading templates..." />
      </div>
    );
  }

  return (
    <Stack tokens={{ childrenGap: 24 }}>
      {/* Header and Actions */}
      <div className={styles.settingSection}>
        <div className={styles.sectionHeader}>
          <h3 className={styles.sectionTitle}>Template Management</h3>
          <p className={styles.sectionDescription}>
            Create, modify, and organize AI parameter templates. Templates allow you to save and reuse 
            configurations for different types of video content.
          </p>
        </div>

        <CommandBar
          items={commandBarItems}
          styles={{
            root: { padding: 0 },
          }}
        />
      </div>

      {/* Templates List */}
      <div className={styles.settingSection}>
        <DetailsList
          items={templates}
          columns={templateColumns}
          selectionMode={SelectionMode.single}
          setKey="templates"
          styles={{
            root: { minHeight: '300px' },
            headerWrapper: { '& [role=row]': { backgroundColor: '#f8f9fa' } },
          }}
          onItemInvoked={(item: AITemplate) => {
            setSelectedTemplate(item);
            onMessage(`Template "${item.displayName}" selected`, MessageBarType.info);
          }}
        />

        {templates.length === 0 && !isLoading && (
          <div style={{ 
            textAlign: 'center', 
            padding: '40px', 
            backgroundColor: '#f8f9fa',
            borderRadius: '4px',
            border: '1px dashed #d2d0ce'
          }}>
            <Text variant="medium" styles={{ root: { color: '#605e5c' } }}>
              No templates found. Create your first template to get started.
            </Text>
          </div>
        )}
      </div>

      {/* Create Template Dialog */}
      <Dialog
        hidden={!isCreateDialogOpen}
        onDismiss={() => setIsCreateDialogOpen(false)}
        dialogContentProps={{
          type: DialogType.largeHeader,
          title: 'Create New AI Template',
          subText: 'Create a new template with custom AI parameters and configurations.',
        }}
        minWidth="500px"
        maxWidth="600px"
      >
        <Stack tokens={{ childrenGap: 20 }}>
          <TextField
            label="Template Name"
            placeholder="Enter a descriptive name for your template"
            value={newTemplateForm.displayName}
            onChange={(_, value) => setNewTemplateForm(prev => ({ ...prev, displayName: value || '' }))}
            required
            disabled={isLoading}
          />
          
          <TextField
            label="Description"
            placeholder="Describe what this template is for and when to use it"
            multiline
            rows={3}
            value={newTemplateForm.description}
            onChange={(_, value) => setNewTemplateForm(prev => ({ ...prev, description: value || '' }))}
            required
            disabled={isLoading}
          />
          
          <Dropdown
            label="Category"
            placeholder="Select a category for this template"
            options={categoryOptions}
            selectedKey={newTemplateForm.category}
            onChange={(_, option) => setNewTemplateForm(prev => ({ ...prev, category: option?.key as string || '' }))}
            required
            disabled={isLoading}
          />
          
          <Dropdown
            label="Base Template (Optional)"
            placeholder="Choose an existing template to copy settings from"
            options={availableTemplatesForCopy}
            selectedKey={newTemplateForm.copyFromTemplate}
            onChange={(_, option) => setNewTemplateForm(prev => ({ ...prev, copyFromTemplate: option?.key as string || '' }))}
            disabled={isLoading}
          />
          
          {newTemplateForm.copyFromTemplate && (
            <MessageBar messageBarType={MessageBarType.info}>
              This template will be created with the same parameters as the selected base template. 
              You can modify these parameters after creation.
            </MessageBar>
          )}
        </Stack>
        
        <DialogFooter>
          <PrimaryButton
            onClick={createTemplate}
            text={isLoading ? "Creating..." : "Create Template"}
            disabled={isLoading || !newTemplateForm.displayName || !newTemplateForm.description || !newTemplateForm.category}
          />
          <DefaultButton
            onClick={() => setIsCreateDialogOpen(false)}
            text="Cancel"
            disabled={isLoading}
          />
        </DialogFooter>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        hidden={!isDeleteDialogOpen}
        onDismiss={() => setIsDeleteDialogOpen(false)}
        dialogContentProps={{
          type: DialogType.normal,
          title: 'Delete Template',
          closeButtonAriaLabel: 'Close',
          subText: `Are you sure you want to delete the template "${templateToDelete?.displayName}"? This action cannot be undone.`,
        }}
      >
        <DialogFooter>
          <PrimaryButton
            onClick={deleteTemplate}
            text={isLoading ? "Deleting..." : "Delete"}
            disabled={isLoading}
            styles={{ root: { backgroundColor: '#d83b01', borderColor: '#d83b01' } }}
          />
          <DefaultButton
            onClick={() => setIsDeleteDialogOpen(false)}
            text="Cancel"
            disabled={isLoading}
          />
        </DialogFooter>
      </Dialog>
    </Stack>
  );
};

export default TemplateManagementTab;
