import { initializeIcons } from '@fluentui/font-icons-mdl2';
import { registerIconAlias } from '@fluentui/react';

export function setupFluentIcons(): void {
  // Initialize icons with local font path
  initializeIcons('/assets/fonts/');

  // Register aliases for missing icons
  registerIconAlias('lightning', 'LightningBolt');
  registerIconAlias('processingrun', 'Processing');
}