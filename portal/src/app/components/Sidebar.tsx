'use client';

import { useState, useEffect } from 'react';
import { 
  PlusIcon, 
  MagnifyingGlassIcon, 
  Cog6ToothIcon,
  ArrowsUpDownIcon,
  DocumentArrowDownIcon,
  DocumentArrowUpIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ChevronDownIcon,
  Bars3Icon,
} from '@heroicons/react/24/outline';
import { App } from '@/lib/types';
import { cn, groupAppsByGroup, sortAppsByOrder, filterApps } from '@/lib/utils';
import { AppIcon } from './AppIcon';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';

interface SidebarProps {
  apps: App[];
  selectedApp: App | null;
  onSelectApp: (app: App) => void;
  onAddApp: () => void;
  onEditApp: (app: App) => void;
  onDeleteApp: (app: App) => void;
  onReorderApps: (apps: App[]) => void;
  onImportExport: () => void;
  onSettings: () => void;
  collapsed: boolean;
  onToggleCollapsed: () => void;
  isMobile?: boolean;
  onCloseMobile?: () => void;
}

export function Sidebar({
  apps,
  selectedApp,
  onSelectApp,
  onAddApp,
  onEditApp,
  onDeleteApp,
  onReorderApps,
  onImportExport,
  onSettings,
  collapsed,
  onToggleCollapsed,
  isMobile = false,
  onCloseMobile,
}: SidebarProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [showSearch, setShowSearch] = useState(false);
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set());
  const [contextMenu, setContextMenu] = useState<{
    app: App;
    x: number;
    y: number;
  } | null>(null);

  const filteredApps = filterApps(apps, searchTerm);
  const sortedApps = sortAppsByOrder(filteredApps);
  const groupedApps = groupAppsByGroup(sortedApps);

  const toggleGroupCollapse = (groupName: string) => {
    setCollapsedGroups(prev => {
      const newSet = new Set(prev);
      if (newSet.has(groupName)) {
        newSet.delete(groupName);
      } else {
        newSet.add(groupName);
      }
      return newSet;
    });
  };

  useEffect(() => {
    const handleClickOutside = () => setContextMenu(null);
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setContextMenu(null);
        if (showSearch) {
          setShowSearch(false);
          setSearchTerm('');
        }
      }
    };
    
    document.addEventListener('click', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('click', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [showSearch]);

  const handleContextMenu = (e: React.MouseEvent, app: App) => {
    e.preventDefault();
    setContextMenu({
      app,
      x: e.clientX,
      y: e.clientY,
    });
  };

  const handleDragEnd = (result: any) => {
    if (!result.destination) return;

    const items = Array.from(sortedApps);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);

    // Update order property
    const reorderedApps = items.map((app, index) => ({
      ...app,
      order: index,
    }));

    onReorderApps(reorderedApps);
  };

  return (
    <>
      <div className={cn(
        'flex flex-col h-full bg-gray-800 border-r border-gray-700 transition-all duration-300',
        collapsed ? 'w-16' : 'w-64',
        isMobile && 'w-80 max-w-[80vw]' // Wider on mobile for better touch targets
      )}>
        {/* Header */}
        <div className="flex items-center justify-center p-4 border-b border-gray-700">
          {collapsed ? (
            <button
              onClick={onToggleCollapsed}
              className="p-2 text-gray-400 hover:text-white transition-colors"
              title="Expand sidebar"
            >
              <ChevronRightIcon className="w-5 h-5" />
            </button>
          ) : (
            <div className="flex items-center justify-between w-full">
              <h1 className="text-lg font-semibold text-white">Portal</h1>
              {isMobile ? (
                <button
                  onClick={onCloseMobile}
                  className="p-2 text-gray-400 hover:text-white transition-colors"
                  title="Close menu"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              ) : (
                <button
                  onClick={onToggleCollapsed}
                  className="p-1 text-gray-400 hover:text-white transition-colors"
                  title="Minimize to icons"
                >
                  <ChevronLeftIcon className="w-5 h-5" />
                </button>
              )}
            </div>
          )}
        </div>

        {/* Search */}
        {!collapsed || isMobile ? (
          <div className="p-4 border-b border-gray-700">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search apps..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className={cn(
                  'w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500',
                  isMobile && 'py-3 text-base' // Larger touch target on mobile
                )}
              />
            </div>
          </div>
        ) : null}

        {/* Apps List */}
        <div className="flex-1 overflow-y-auto sidebar-scrollbar">
          <DragDropContext onDragEnd={handleDragEnd}>
            <Droppable droppableId="apps">
              {(provided) => (
                <div
                  {...provided.droppableProps}
                  ref={provided.innerRef}
                  className="p-2 space-y-1"
                >
                  {Object.entries(groupedApps).map(([groupName, groupApps]) => (
                    <div key={groupName} className="space-y-1">
                      {!collapsed && groupName !== 'Ungrouped' && (
                        <div className="px-2 py-1 text-xs font-medium text-gray-400 uppercase tracking-wider">
                          {groupName}
                        </div>
                      )}
                      {groupApps.map((app, index) => (
                          <Draggable key={app.id} draggableId={app.id} index={index}>
                            {(provided, snapshot) => (
                              <div
                                ref={provided.innerRef}
                                {...provided.draggableProps}
                                {...provided.dragHandleProps}
                                className={cn(
                                  'flex items-center rounded-lg cursor-pointer transition-colors relative',
                                  selectedApp?.id === app.id
                                    ? 'bg-blue-600 text-white'
                                    : 'text-gray-300 hover:bg-gray-700 hover:text-white',
                                  collapsed ? 'p-2 justify-center' : 'p-3',
                                  isMobile && 'p-4 min-h-[56px]', // Larger touch targets on mobile
                                  snapshot.isDragging && 'opacity-50'
                                )}
                                onClick={() => onSelectApp(app)}
                                onContextMenu={(e) => {
                                  e.preventDefault();
                                  setContextMenu({
                                    app,
                                    x: e.clientX,
                                    y: e.clientY,
                                  });
                                }}
                              >
                                <AppIcon app={app} />
                                {!collapsed && (
                                  <div className="ml-3 flex-1 min-w-0">
                                    <div className="text-sm font-medium truncate">
                                      {app.name}
                                    </div>
                                    <div className="text-xs text-gray-400 truncate">
                                      {new URL(app.url).hostname}
                                    </div>
                                  </div>
                                )}
                              </div>
                            )}
                          </Draggable>
                        ))}
                    </div>
                  ))}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          </DragDropContext>
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-gray-700">
          <div className="flex justify-center space-x-3">
            <button
              onClick={onAddApp}
              className="p-2 bg-blue-600 hover:bg-blue-700 rounded-md transition-colors"
              title="Add new app"
            >
              <PlusIcon className="w-4 h-4 text-white" />
            </button>
            
            <button
              onClick={onImportExport}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-md transition-colors"
              title="Import/Export"
            >
              <DocumentArrowUpIcon className="w-4 h-4" />
            </button>
            
            <button
              onClick={onSettings}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-md transition-colors"
              title="Settings"
            >
              <Cog6ToothIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Search Overlay for Collapsed Sidebar */}
      {collapsed && showSearch && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-40 flex items-start justify-center pt-20">
          <div className="bg-gray-800 border border-gray-600 rounded-lg shadow-lg p-4 w-80 max-w-sm">
            <div className="relative mb-4">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search apps..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                autoFocus
              />
            </div>
            <div className="max-h-60 overflow-y-auto space-y-1">
              {filteredApps.length > 0 ? (
                filteredApps.map((app) => (
                  <div
                    key={app.id}
                    className="flex items-center p-2 rounded-lg cursor-pointer hover:bg-gray-700 transition-colors"
                    onClick={() => {
                      onSelectApp(app);
                      setShowSearch(false);
                      setSearchTerm('');
                    }}
                  >
                    <AppIcon app={app} />
                    <div className="ml-3 flex-1 min-w-0">
                      <div className="text-sm font-medium text-white truncate">
                        {app.name}
                      </div>
                      <div className="text-xs text-gray-400 truncate">
                        {new URL(app.url).hostname}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center text-gray-400 py-4">
                  No apps found
                </div>
              )}
            </div>
            <div className="mt-4 flex justify-end">
              <button
                onClick={() => {
                  setShowSearch(false);
                  setSearchTerm('');
                }}
                className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Context Menu */}
      {contextMenu && (
        <div
          className="fixed z-50 bg-gray-800 border border-gray-600 rounded-lg shadow-lg py-1 min-w-[120px]"
          style={{
            left: contextMenu.x,
            top: contextMenu.y,
          }}
        >
          <button
            onClick={() => {
              onEditApp(contextMenu.app);
              setContextMenu(null);
            }}
            className="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-700 hover:text-white"
          >
            Edit
          </button>
          <button
            onClick={() => {
              onDeleteApp(contextMenu.app);
              setContextMenu(null);
            }}
            className="w-full px-4 py-2 text-left text-sm text-red-400 hover:bg-gray-700 hover:text-red-300"
          >
            Delete
          </button>
        </div>
      )}
    </>
  );
}
