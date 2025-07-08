'use client';

import { useState, useEffect } from 'react';
import { Dialog } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { App } from '@/lib/types';
import { validateAppData, isEmoji } from '@/lib/utils';
import { AppIcon } from './AppIcon';

interface AppModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (app: Partial<App>) => void;
  app?: App | null;
  existingGroups: string[];
}

const EMOJI_SUGGESTIONS = [
  '🎬', '📺', '🍿', '🎵', '🎮', '📱', '💻', '🖥️', '⚙️', '🔧',
  '📊', '📈', '📉', '📋', '📝', '📁', '📂', '🗂️', '🔍', '🌐',
  '🔒', '🔑', '🛡️', '⚡', '🔥', '💡', '🚀', '⭐', '❤️', '💚',
  '🔵', '🟢', '🟡', '🟠', '🔴', '🟣', '⚫', '⚪', '🔶', '🔷',
];

export function AppModal({ isOpen, onClose, onSave, app, existingGroups }: AppModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    icon: '',
    group: '',
  });
  const [errors, setErrors] = useState<string[]>([]);
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [customGroup, setCustomGroup] = useState('');
  const [showCustomGroup, setShowCustomGroup] = useState(false);

  useEffect(() => {
    if (app) {
      setFormData({
        name: app.name,
        url: app.url,
        icon: app.icon,
        group: app.group || '',
      });
    } else {
      setFormData({
        name: '',
        url: '',
        icon: '🌐',
        group: '',
      });
    }
    setErrors([]);
    setShowEmojiPicker(false);
    setCustomGroup('');
    setShowCustomGroup(false);
  }, [app, isOpen]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const finalGroup = showCustomGroup ? customGroup : formData.group;
    const appData = {
      ...formData,
      group: finalGroup || undefined,
    };

    const validation = validateAppData(appData);
    if (!validation.valid) {
      setErrors(validation.errors);
      return;
    }

    onSave(appData);
    onClose();
  };

  const handleEmojiSelect = (emoji: string) => {
    setFormData(prev => ({ ...prev, icon: emoji }));
    setShowEmojiPicker(false);
  };

  const handleIconChange = (value: string) => {
    setFormData(prev => ({ ...prev, icon: value }));
  };

  const previewApp: App = {
    id: 'preview',
    name: formData.name || 'App Name',
    url: formData.url || 'https://example.com',
    icon: formData.icon || '🌐',
    group: showCustomGroup ? customGroup : formData.group,
  };

  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/50" aria-hidden="true" />
      
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="bg-gray-800 rounded-lg shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between p-6 border-b border-gray-700">
            <Dialog.Title className="text-lg font-semibold text-white">
              {app ? 'Edit App' : 'Add New App'}
            </Dialog.Title>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-white transition-colors -mr-2"
              aria-label="Close modal"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {errors.length > 0 && (
              <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-3">
                <ul className="text-sm text-red-400 space-y-1">
                  {errors.map((error, index) => (
                    <li key={index}>• {error}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Preview */}
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="text-sm text-gray-400 mb-2">Preview:</div>
              <div className="flex items-center space-x-3">
                <AppIcon app={previewApp} size="md" />
                <div>
                  <div className="text-white font-medium">
                    {previewApp.name}
                  </div>
                  <div className="text-gray-400 text-sm">
                    {previewApp.url ? new URL(previewApp.url).hostname : 'example.com'}
                  </div>
                </div>
              </div>
            </div>

            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                App Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 text-base"
                placeholder="Enter app name"
                required
              />
            </div>

            {/* URL */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                URL *
              </label>
              <input
                type="url"
                value={formData.url}
                onChange={(e) => setFormData(prev => ({ ...prev, url: e.target.value }))}
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 text-base"
                placeholder="https://example.com"
                required
              />
            </div>

            {/* Icon */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Icon *
              </label>
              <div className="space-y-2">
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={formData.icon}
                    onChange={(e) => handleIconChange(e.target.value)}
                    className="flex-1 px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 text-base"
                    placeholder="🌐 or image URL"
                  />
                  <button
                    type="button"
                    onClick={() => setShowEmojiPicker(!showEmojiPicker)}
                    className="px-4 py-3 bg-gray-600 hover:bg-gray-500 rounded-lg transition-colors text-base"
                    aria-label="Choose emoji"
                  >
                    😀
                  </button>
                </div>
                
                {showEmojiPicker && (
                  <div className="bg-gray-700 border border-gray-600 rounded-lg p-3">
                    <div className="grid grid-cols-6 sm:grid-cols-8 gap-2">
                      {EMOJI_SUGGESTIONS.map((emoji) => (
                        <button
                          key={emoji}
                          type="button"
                          onClick={() => handleEmojiSelect(emoji)}
                          className="w-10 h-10 sm:w-8 sm:h-8 flex items-center justify-center hover:bg-gray-600 rounded transition-colors text-lg"
                        >
                          {emoji}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Group */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Group (Optional)
              </label>
              <div className="space-y-2">
                <select
                  value={showCustomGroup ? '' : formData.group}
                  onChange={(e) => {
                    if (e.target.value === '__custom__') {
                      setShowCustomGroup(true);
                      setFormData(prev => ({ ...prev, group: '' }));
                    } else {
                      setShowCustomGroup(false);
                      setFormData(prev => ({ ...prev, group: e.target.value }));
                    }
                  }}
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 text-base"
                  disabled={showCustomGroup}
                >
                  <option value="">No Group</option>
                  {existingGroups.map((group) => (
                    <option key={group} value={group}>
                      {group}
                    </option>
                  ))}
                  <option value="__custom__">+ Create New Group</option>
                </select>

                {showCustomGroup && (
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={customGroup}
                      onChange={(e) => setCustomGroup(e.target.value)}
                      className="flex-1 px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 text-base"
                      placeholder="Enter group name"
                    />
                    <button
                      type="button"
                      onClick={() => {
                        setShowCustomGroup(false);
                        setCustomGroup('');
                      }}
                      className="px-4 py-3 bg-gray-600 hover:bg-gray-500 rounded-lg transition-colors text-white text-base"
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row justify-end space-y-2 sm:space-y-0 sm:space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-6 py-3 bg-gray-600 hover:bg-gray-500 text-white rounded-lg transition-colors text-base min-h-[48px]"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-base min-h-[48px]"
              >
                {app ? 'Update' : 'Add'} App
              </button>
            </div>
          </form>
        </Dialog.Panel>
      </div>
    </Dialog>
  );
}
