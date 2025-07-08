'use client';

import { useState, useEffect } from 'react';
import { 
  ArrowTopRightOnSquareIcon, 
  ArrowPathIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { App } from '@/lib/types';
import { AppIcon } from './AppIcon';

interface MainPanelProps {
  selectedApp: App | null;
  onRefreshStatus?: (app: App) => void;
}

export function MainPanel({ selectedApp, onRefreshStatus }: MainPanelProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [iframeKey, setIframeKey] = useState(0);

  useEffect(() => {
    if (selectedApp) {
      setIsLoading(true);
      setHasError(false);
      setIframeKey(prev => prev + 1);
    }
  }, [selectedApp]);

  const handleIframeLoad = () => {
    setIsLoading(false);
    setHasError(false);
  };

  const handleIframeError = () => {
    setIsLoading(false);
    setHasError(true);
  };

  const handleRefresh = () => {
    if (selectedApp) {
      setIframeKey(prev => prev + 1);
      setIsLoading(true);
      setHasError(false);
    }
  };

  const handleOpenInNewTab = () => {
    if (selectedApp) {
      window.open(selectedApp.url, '_blank');
    }
  };

  const handleRefreshStatus = () => {
    if (selectedApp && onRefreshStatus) {
      onRefreshStatus(selectedApp);
    }
  };

  if (!selectedApp) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-gray-800 rounded-full flex items-center justify-center">
            <ArrowTopRightOnSquareIcon className="w-8 h-8 text-gray-400" />
          </div>
          <h2 className="text-xl font-semibold text-gray-300 mb-2">
            Welcome to Portal
          </h2>
          <p className="text-gray-400 max-w-md">
            Select an app from the sidebar to get started, or add a new app to organize your dashboard.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* Content */}
      <div className="h-full relative">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900 z-10">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-gray-400">Loading {selectedApp.name}...</p>
            </div>
          </div>
        )}

        {hasError && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900 z-10">
            <div className="text-center">
              <ExclamationTriangleIcon className="w-12 h-12 text-red-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">
                Failed to load {selectedApp.name}
              </h3>
              <p className="text-gray-400 mb-4">
                The app might be offline or not accessible.
              </p>
              <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
                <button
                  onClick={handleRefresh}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-base min-h-[48px]"
                >
                  Try Again
                </button>
                <button
                  onClick={handleOpenInNewTab}
                  className="px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors text-base min-h-[48px]"
                >
                  Open in New Tab
                </button>
              </div>
            </div>
          </div>
        )}

        <iframe
          key={iframeKey}
          src={selectedApp.url}
          className="w-full h-full border-0"
          onLoad={handleIframeLoad}
          onError={handleIframeError}
          sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-popups-to-escape-sandbox"
          title={selectedApp.name}
        />
      </div>
    </div>
  );
}
