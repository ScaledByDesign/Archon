'use client';

import { useState } from 'react';
import { Dialog } from '@headlessui/react';
import { 
  XMarkIcon, 
  DocumentArrowDownIcon, 
  DocumentArrowUpIcon,
  ClipboardDocumentIcon,
  CheckIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';
import { Config } from '@/lib/types';
import { exportConfig, importConfig } from '@/lib/utils';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImport: (config: Config) => void;
  onUpdateSettings: (settings: Partial<Config['settings']>) => void;
  currentConfig: Config;
}

export function SettingsModal({ 
  isOpen, 
  onClose, 
  onImport, 
  onUpdateSettings,
  currentConfig 
}: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState<'settings' | 'import' | 'export'>('settings');
  const [importData, setImportData] = useState('');
  const [importError, setImportError] = useState('');
  const [copied, setCopied] = useState(false);

  const handleExport = () => {
    const configJson = exportConfig(currentConfig);
    const blob = new Blob([configJson], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `portal-config-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleCopyToClipboard = async () => {
    try {
      const configJson = exportConfig(currentConfig);
      await navigator.clipboard.writeText(configJson);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const handleImport = () => {
    setImportError('');
    
    if (!importData.trim()) {
      setImportError('Please enter configuration data');
      return;
    }

    const result = importConfig(importData);
    if (!result.valid) {
      setImportError(result.error || 'Invalid configuration format');
      return;
    }

    onImport(result.config!);
    onClose();
    setImportData('');
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      setImportData(content);
      setImportError('');
    };
    reader.readAsText(file);
  };

  const handleClose = () => {
    onClose();
    setImportData('');
    setImportError('');
    setCopied(false);
  };

  const handleToggleStatusIndicators = () => {
    onUpdateSettings({ showStatus: !currentConfig.settings.showStatus });
  };

  const handleToggleSidebarCollapsed = () => {
    onUpdateSettings({ sidebarCollapsed: !currentConfig.settings.sidebarCollapsed });
  };

  return (
    <Dialog open={isOpen} onClose={handleClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/50" aria-hidden="true" />
      
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col mx-4">
          <div className="flex items-center justify-between p-6 border-b border-gray-700">
            <Dialog.Title className="text-lg font-semibold text-white">
              Settings & Configuration
            </Dialog.Title>
            <button
              onClick={handleClose}
              className="p-2 text-gray-400 hover:text-white transition-colors -mr-2"
              aria-label="Close modal"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-gray-700">
            <button
              onClick={() => setActiveTab('settings')}
              className={`flex-1 px-4 py-4 text-base font-medium transition-colors min-h-[56px] flex items-center justify-center ${
                activeTab === 'settings'
                  ? 'text-blue-400 border-b-2 border-blue-400'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <Cog6ToothIcon className="w-5 h-5 mr-2" />
              Settings
            </button>
            <button
              onClick={() => setActiveTab('export')}
              className={`flex-1 px-4 py-4 text-base font-medium transition-colors min-h-[56px] flex items-center justify-center ${
                activeTab === 'export'
                  ? 'text-blue-400 border-b-2 border-blue-400'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <DocumentArrowDownIcon className="w-5 h-5 mr-2" />
              Export
            </button>
            <button
              onClick={() => setActiveTab('import')}
              className={`flex-1 px-4 py-4 text-base font-medium transition-colors min-h-[56px] flex items-center justify-center ${
                activeTab === 'import'
                  ? 'text-blue-400 border-b-2 border-blue-400'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <DocumentArrowUpIcon className="w-5 h-5 mr-2" />
              Import
            </button>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto">
            {activeTab === 'settings' ? (
              <div className="p-6 space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-white mb-4">App Settings</h3>
                  
                  <div className="space-y-4">
                    {/* Status Indicators */}
                    <div className="flex items-center justify-between p-4 bg-gray-700 rounded-lg">
                      <div>
                        <div className="text-white font-medium">Status Indicators</div>
                        <div className="text-sm text-gray-400">Show online/offline status for apps</div>
                      </div>
                      <button
                        onClick={handleToggleStatusIndicators}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          currentConfig.settings.showStatus ? 'bg-blue-600' : 'bg-gray-600'
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            currentConfig.settings.showStatus ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>

                    {/* Sidebar Collapsed */}
                    <div className="flex items-center justify-between p-4 bg-gray-700 rounded-lg">
                      <div>
                        <div className="text-white font-medium">Collapsed Sidebar</div>
                        <div className="text-sm text-gray-400">Start with sidebar minimized</div>
                      </div>
                      <button
                        onClick={handleToggleSidebarCollapsed}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          currentConfig.settings.sidebarCollapsed ? 'bg-blue-600' : 'bg-gray-600'
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            currentConfig.settings.sidebarCollapsed ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-white mb-4">About</h3>
                  <div className="bg-gray-700 rounded-lg p-4 space-y-2">
                    <div className="text-white font-medium">Portal App Organizer</div>
                    <div className="text-sm text-gray-400">Version {currentConfig.version}</div>
                    <div className="text-sm text-gray-400">
                      A minimal, efficient app organizer dashboard with flat-file persistence
                    </div>
                  </div>
                </div>
              </div>
            ) : activeTab === 'export' ? (
              <div className="p-6 space-y-4">
                <div className="bg-blue-900/20 border border-blue-500/50 rounded-lg p-4">
                  <div className="flex items-start space-x-2">
                    <div className="text-blue-400 mt-0.5">ℹ️</div>
                    <div>
                      <div className="text-blue-400 font-medium">Export Configuration</div>
                      <div className="text-blue-300 text-sm">
                        Download or copy your current configuration to backup or share with others.
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <button
                    onClick={handleExport}
                    className="w-full flex items-center justify-center px-6 py-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-base min-h-[56px]"
                  >
                    <DocumentArrowDownIcon className="w-5 h-5 mr-2" />
                    Download Configuration File
                  </button>

                  <button
                    onClick={handleCopyToClipboard}
                    className="w-full flex items-center justify-center px-6 py-4 bg-gray-600 hover:bg-gray-500 text-white rounded-lg transition-colors text-base min-h-[56px]"
                  >
                    {copied ? (
                      <>
                        <CheckIcon className="w-5 h-5 mr-2" />
                        Copied to Clipboard!
                      </>
                    ) : (
                      <>
                        <ClipboardDocumentIcon className="w-5 h-5 mr-2" />
                        Copy to Clipboard
                      </>
                    )}
                  </button>
                </div>

                <div className="bg-gray-700 rounded-lg p-4">
                  <h4 className="text-white font-medium mb-2">Configuration Preview</h4>
                  <pre className="text-xs text-gray-300 bg-gray-800 rounded p-3 overflow-x-auto max-h-40">
                    {exportConfig(currentConfig)}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="p-6 space-y-4">
                <div className="bg-yellow-900/20 border border-yellow-500/50 rounded-lg p-4">
                  <div className="flex items-start space-x-2">
                    <div className="text-yellow-400 mt-0.5">⚠️</div>
                    <div>
                      <div className="text-yellow-400 font-medium">Warning</div>
                      <div className="text-yellow-300 text-sm">
                        Importing will replace your current configuration. Make sure to export your current settings first if you want to keep them.
                      </div>
                    </div>
                  </div>
                </div>

                {importError && (
                  <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-3">
                    <div className="text-red-400 text-sm">{importError}</div>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Upload Configuration File
                  </label>
                  <input
                    type="file"
                    accept=".json"
                    onChange={handleFileUpload}
                    className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white text-base file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700 file:text-base"
                  />
                </div>

                <div className="text-center text-gray-400">or</div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Paste Configuration JSON
                  </label>
                  <textarea
                    value={importData}
                    onChange={(e) => setImportData(e.target.value)}
                    className="w-full h-40 px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-base"
                    placeholder="Paste your configuration JSON here..."
                  />
                </div>

                <button
                  onClick={handleImport}
                  disabled={!importData.trim()}
                  className="w-full px-6 py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors text-base min-h-[56px]"
                >
                  Import Configuration
                </button>
              </div>
            )}
          </div>
        </Dialog.Panel>
      </div>
    </Dialog>
  );
}
