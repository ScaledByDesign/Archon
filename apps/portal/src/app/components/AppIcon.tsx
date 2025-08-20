'use client';

import { App } from '@/lib/types';
import { isEmoji } from '@/lib/utils';

interface AppIconProps {
  app: App;
  size?: 'sm' | 'md' | 'lg';
}

export function AppIcon({ app, size = 'md' }: AppIconProps) {
  const sizeClasses = {
    sm: 'w-6 h-6 text-sm',
    md: 'w-8 h-8 text-lg',
    lg: 'w-12 h-12 text-2xl',
  };

  // Check if icon is an emoji
  if (isEmoji(app.icon)) {
    return (
      <div className={`app-icon ${sizeClasses[size]} flex items-center justify-center`}>
        <span>{app.icon}</span>
      </div>
    );
  }

  // Check if icon is a URL (image)
  if (app.icon.startsWith('http') || app.icon.startsWith('/')) {
    return (
      <div className={`app-icon ${sizeClasses[size]} flex items-center justify-center`}>
        <img
          src={app.icon}
          alt={`${app.name} icon`}
          className="w-full h-full object-contain rounded"
          onError={(e) => {
            // Fallback to first letter if image fails to load
            const target = e.target as HTMLImageElement;
            target.style.display = 'none';
            const fallback = document.createElement('div');
            fallback.className = 'w-full h-full flex items-center justify-center bg-gray-600 rounded text-white font-medium';
            fallback.textContent = app.name.charAt(0).toUpperCase();
            target.parentNode?.appendChild(fallback);
          }}
        />
      </div>
    );
  }

  // Check if icon is SVG
  if (app.icon.includes('<svg')) {
    return (
      <div 
        className={`app-icon ${sizeClasses[size]} flex items-center justify-center`}
        dangerouslySetInnerHTML={{ __html: app.icon }}
      />
    );
  }

  // Fallback to first letter
  return (
    <div className={`app-icon ${sizeClasses[size]} flex items-center justify-center bg-gray-600 rounded text-white font-medium`}>
      {app.name.charAt(0).toUpperCase()}
    </div>
  );
}
