export interface App {
  id: string;
  name: string;
  url: string;
  icon: string; // emoji, SVG, or image URL
  group?: string;
  order?: number;
  status?: 'online' | 'offline' | 'unknown';
  createdAt?: string;
  updatedAt?: string;
}

export interface AppGroup {
  name: string;
  apps: App[];
  collapsed?: boolean;
  order?: number;
}

export interface Config {
  apps: App[];
  groups: string[];
  settings: {
    theme?: 'light' | 'dark';
    showStatus?: boolean;
    autoRefresh?: boolean;
    sidebarCollapsed?: boolean;
  };
  version: string;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface StatusCheckResult {
  id: string;
  status: 'online' | 'offline' | 'unknown';
  responseTime?: number;
  lastChecked: string;
}
