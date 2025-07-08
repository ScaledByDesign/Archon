import { type ClassValue, clsx } from 'clsx';
import { App, Config } from './types';

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function generateId(): string {
  return Math.random().toString(36).substring(2) + Date.now().toString(36);
}

export function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

export function isEmoji(str: string): boolean {
  // Simple emoji detection - check if string is a single character and looks like an emoji
  if (str.length > 4) return false;
  
  // Check for common emoji patterns
  const codePoint = str.codePointAt(0);
  if (!codePoint) return false;
  
  // Common emoji ranges (without unicode flag)
  return (
    (codePoint >= 0x1F600 && codePoint <= 0x1F64F) || // Emoticons
    (codePoint >= 0x1F300 && codePoint <= 0x1F5FF) || // Misc Symbols
    (codePoint >= 0x1F680 && codePoint <= 0x1F6FF) || // Transport
    (codePoint >= 0x2600 && codePoint <= 0x26FF) ||   // Misc symbols
    (codePoint >= 0x2700 && codePoint <= 0x27BF)      // Dingbats
  );
}

export function getDefaultConfig(): Config {
  return {
    apps: [
      {
        id: 'plex',
        name: 'Plex',
        url: 'http://plex.local:32400/web',
        icon: '🎬',
        group: 'Media',
        order: 0,
        status: 'unknown',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
      {
        id: 'radarr',
        name: 'Radarr',
        url: 'http://radarr.local:7878/',
        icon: '🍿',
        group: 'Media',
        order: 1,
        status: 'unknown',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
      {
        id: 'sonarr',
        name: 'Sonarr',
        url: 'http://sonarr.local:8989/',
        icon: '📺',
        group: 'Media',
        order: 2,
        status: 'unknown',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
      {
        id: 'portainer',
        name: 'Portainer',
        url: 'http://portainer.local:9000/',
        icon: '🐳',
        group: 'Management',
        order: 3,
        status: 'unknown',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
    ],
    groups: ['Media', 'Management'],
    settings: {
      theme: 'dark',
      showStatus: true,
      autoRefresh: false,
      sidebarCollapsed: false,
    },
    version: '1.0.0',
  };
}

export function sortAppsByOrder(apps: App[]): App[] {
  return [...apps].sort((a, b) => (a.order || 0) - (b.order || 0));
}

export function groupAppsByGroup(apps: App[]): Record<string, App[]> {
  const grouped: Record<string, App[]> = {};
  
  apps.forEach(app => {
    const group = app.group || 'Ungrouped';
    if (!grouped[group]) {
      grouped[group] = [];
    }
    grouped[group].push(app);
  });

  // Sort apps within each group
  Object.keys(grouped).forEach(group => {
    grouped[group] = sortAppsByOrder(grouped[group]);
  });

  return grouped;
}

export function filterApps(apps: App[], searchTerm: string): App[] {
  if (!searchTerm.trim()) return apps;
  
  const term = searchTerm.toLowerCase();
  return apps.filter(app => 
    app.name.toLowerCase().includes(term) ||
    app.url.toLowerCase().includes(term) ||
    (app.group && app.group.toLowerCase().includes(term))
  );
}

export function validateAppData(data: Partial<App>): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!data.name || data.name.trim().length === 0) {
    errors.push('App name is required');
  }

  if (!data.url || !isValidUrl(data.url)) {
    errors.push('Valid URL is required');
  }

  if (!data.icon || data.icon.trim().length === 0) {
    errors.push('Icon is required');
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

export function exportConfig(config: Config): string {
  return JSON.stringify(config, null, 2);
}

export function importConfig(jsonString: string): { valid: boolean; config?: Config; error?: string } {
  try {
    const parsed = JSON.parse(jsonString);
    
    // Basic validation
    if (!parsed.apps || !Array.isArray(parsed.apps)) {
      return { valid: false, error: 'Invalid config: apps array is required' };
    }

    // Ensure required fields exist
    const config: Config = {
      apps: parsed.apps,
      groups: parsed.groups || [],
      settings: {
        theme: parsed.settings?.theme || 'dark',
        showStatus: parsed.settings?.showStatus ?? true,
        autoRefresh: parsed.settings?.autoRefresh ?? false,
        sidebarCollapsed: parsed.settings?.sidebarCollapsed ?? false,
      },
      version: parsed.version || '1.0.0',
    };

    return { valid: true, config };
  } catch (error) {
    return { valid: false, error: 'Invalid JSON format' };
  }
}
