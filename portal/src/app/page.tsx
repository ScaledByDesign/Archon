'use client';

import { useState, useEffect } from 'react';
import { App, Config } from '@/lib/types';
import { Sidebar } from './components/Sidebar';
import { MainPanel } from './components/MainPanel';
import { AppModal } from './components/AppModal';
import { SettingsModal } from './components/SettingsModal';

export default function Home() {
  const [apps, setApps] = useState<App[]>([]);
  const [config, setConfig] = useState<Config | null>(null);
  const [selectedApp, setSelectedApp] = useState<App | null>(null);
  const [isAppModalOpen, setIsAppModalOpen] = useState(false);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [editingApp, setEditingApp] = useState<App | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false); // For mobile overlay
  const [isMobile, setIsMobile] = useState(false);
  const [loading, setLoading] = useState(true);

  // Load initial data
  useEffect(() => {
    loadConfig();
  }, []);

  // Detect mobile screen size
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const loadConfig = async () => {
    try {
      const response = await fetch('/api/config');
      const result = await response.json();
      
      if (result.success) {
        setConfig(result.data);
        setApps(result.data.apps);
        setSidebarCollapsed(result.data.settings.sidebarCollapsed || false);
        
        // Auto-select Dashy Dashboard as default, or first app if Dashy not found
        if (!selectedApp && result.data.apps.length > 0) {
          const dashyApp = result.data.apps.find((app: App) => app.id === 'dashy');
          setSelectedApp(dashyApp || result.data.apps[0]);
        }
      }
    } catch (error) {
      console.error('Failed to load config:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveApp = async (appData: Partial<App>) => {
    try {
      const url = editingApp ? `/api/apps/${editingApp.id}` : '/api/apps';
      const method = editingApp ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(appData),
      });

      const result = await response.json();
      
      if (result.success) {
        if (editingApp) {
          // Update existing app
          setApps(prev => prev.map(app => 
            app.id === editingApp.id ? result.data : app
          ));
          if (selectedApp?.id === editingApp.id) {
            setSelectedApp(result.data);
          }
        } else {
          // Add new app
          setApps(prev => [...prev, result.data]);
          setSelectedApp(result.data);
        }
        
        // Reload config to get updated groups
        loadConfig();
      } else {
        alert('Failed to save app: ' + result.error);
      }
    } catch (error) {
      console.error('Failed to save app:', error);
      alert('Failed to save app. Please try again.');
    }
  };

  const deleteApp = async (app: App) => {
    if (!confirm(`Are you sure you want to delete "${app.name}"?`)) {
      return;
    }

    try {
      const response = await fetch(`/api/apps/${app.id}`, {
        method: 'DELETE',
      });

      const result = await response.json();
      
      if (result.success) {
        setApps(prev => prev.filter(a => a.id !== app.id));
        
        if (selectedApp?.id === app.id) {
          const remainingApps = apps.filter(a => a.id !== app.id);
          setSelectedApp(remainingApps.length > 0 ? remainingApps[0] : null);
        }
        
        // Reload config to get updated groups
        loadConfig();
      } else {
        alert('Failed to delete app: ' + result.error);
      }
    } catch (error) {
      console.error('Failed to delete app:', error);
      alert('Failed to delete app. Please try again.');
    }
  };

  const reorderApps = async (reorderedApps: App[]) => {
    try {
      const response = await fetch('/api/apps', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ apps: reorderedApps }),
      });

      const result = await response.json();
      
      if (result.success) {
        setApps(result.data);
      } else {
        alert('Failed to reorder apps: ' + result.error);
      }
    } catch (error) {
      console.error('Failed to reorder apps:', error);
      alert('Failed to reorder apps. Please try again.');
    }
  };

  const refreshStatus = async (app: App) => {
    try {
      const response = await fetch(`/api/status/${app.id}`, {
        method: 'POST',
      });

      const result = await response.json();
      
      if (result.success) {
        setApps(prev => prev.map(a => 
          a.id === app.id ? { ...a, status: result.data.status } : a
        ));
        
        if (selectedApp?.id === app.id) {
          setSelectedApp(prev => prev ? { ...prev, status: result.data.status } : null);
        }
      }
    } catch (error) {
      console.error('Failed to refresh status:', error);
    }
  };

  const importConfig = async (newConfig: Config) => {
    try {
      const response = await fetch('/api/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ config: newConfig }),
      });

      const result = await response.json();
      
      if (result.success) {
        setConfig(result.data);
        setApps(result.data.apps);
        setSelectedApp(result.data.apps.length > 0 ? result.data.apps[0] : null);
        alert('Configuration imported successfully!');
      } else {
        alert('Failed to import configuration: ' + result.error);
      }
    } catch (error) {
      console.error('Failed to import config:', error);
      alert('Failed to import configuration. Please try again.');
    }
  };

  const updateSettings = async (settings: Partial<Config['settings']>) => {
    try {
      const response = await fetch('/api/config', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ settings }),
      });

      const result = await response.json();
      
      if (result.success) {
        setConfig(result.data);
      }
    } catch (error) {
      console.error('Failed to update settings:', error);
    }
  };

  const handleToggleSidebar = () => {
    const newCollapsed = !sidebarCollapsed;
    setSidebarCollapsed(newCollapsed);
    updateSettings({ sidebarCollapsed: newCollapsed });
  };

  const handleToggleMobileSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleCloseMobileSidebar = () => {
    setSidebarOpen(false);
  };

  const handleAddApp = () => {
    setEditingApp(null);
    setIsAppModalOpen(true);
  };

  const handleEditApp = (app: App) => {
    setEditingApp(app);
    setIsAppModalOpen(true);
  };

  const handleSettings = () => {
    setIsSettingsModalOpen(true);
  };

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading Portal...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex bg-gray-900 relative">
      {/* Mobile Header */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-30 bg-gray-800 border-b border-gray-700 px-4 py-3 flex items-center justify-between">
        <button
          onClick={handleToggleMobileSidebar}
          className="p-2 text-gray-400 hover:text-white transition-colors"
          aria-label="Toggle menu"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <h1 className="text-lg font-semibold text-white">Portal</h1>
        <button
          onClick={handleAddApp}
          className="p-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          aria-label="Add app"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
      </div>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div 
          className="md:hidden fixed inset-0 z-40 bg-black bg-opacity-50"
          onClick={handleCloseMobileSidebar}
        />
      )}

      {/* Sidebar */}
      <div className={`
        md:relative md:translate-x-0 md:z-auto
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        fixed left-0 top-0 bottom-0 z-50 transition-transform duration-300 ease-in-out
        md:transition-none
      `}>
        <Sidebar
          apps={apps}
          selectedApp={selectedApp}
          onSelectApp={(app) => {
            setSelectedApp(app);
            handleCloseMobileSidebar();
          }}
          onAddApp={handleAddApp}
          onEditApp={handleEditApp}
          onDeleteApp={deleteApp}
          onReorderApps={reorderApps}
          onImportExport={() => setIsSettingsModalOpen(true)}
          onSettings={handleSettings}
          collapsed={sidebarCollapsed}
          onToggleCollapsed={handleToggleSidebar}
          isMobile={isMobile}
          onCloseMobile={handleCloseMobileSidebar}
        />
      </div>
      
      {/* Main Panel */}
      <div className="flex-1 md:ml-0 h-screen pt-16 md:pt-0">
        <MainPanel
          selectedApp={selectedApp}
          onRefreshStatus={refreshStatus}
        />
      </div>

      <AppModal
        isOpen={isAppModalOpen}
        onClose={() => {
          setIsAppModalOpen(false);
          setEditingApp(null);
        }}
        onSave={saveApp}
        app={editingApp}
        existingGroups={config?.groups || []}
      />

      <SettingsModal
        isOpen={isSettingsModalOpen}
        onClose={() => setIsSettingsModalOpen(false)}
        onImport={importConfig}
        onUpdateSettings={updateSettings}
        currentConfig={config || { apps: [], groups: [], settings: {}, version: '1.0.0' }}
      />
    </div>
  );
}
