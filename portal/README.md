# Portal - App Organizer

A minimal, efficient dashboard for managing server-related or personal web-based apps. Portal provides a clean interface to organize and navigate your applications with zero-dependency flat-file persistence.

![Portal Dashboard](https://via.placeholder.com/800x400/1f2937/ffffff?text=Portal+Dashboard)

## Features

- **🎯 Minimal & Fast** - Clean, responsive interface with instant loading
- **📁 Flat-File Storage** - All data stored in a simple JSON file, no database required
- **🔄 Drag & Drop** - Easily reorder and organize your apps
- **📱 Responsive Design** - Works perfectly on desktop, tablet, and mobile
- **🎨 Modern UI** - Dark theme with smooth animations and intuitive navigation
- **📊 Status Monitoring** - Optional ping checks to see if your apps are online
- **📦 Import/Export** - Easy backup and migration of your configuration
- **🏷️ App Grouping** - Organize apps into custom groups/categories
- **🔍 Search & Filter** - Quickly find apps by name or URL
- **🐳 Docker Ready** - Fully containerized with Docker Compose

## Quick Start

### Using Docker Compose (Recommended)

1. **Clone or download** this repository
2. **Start the container**:
   ```bash
   docker-compose up -d
   ```
3. **Access Portal** at `http://localhost:3000`
4. **Start adding your apps!**

That's it! Your configuration will be automatically persisted in the `./data/tabs.json` file.

### Manual Installation

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Start development server**:
   ```bash
   npm run dev
   ```

3. **Or build for production**:
   ```bash
   npm run build
   npm start
   ```

## Configuration

### Data Persistence

All your apps and settings are stored in `data/tabs.json`. This file is automatically created with sample data on first run.

### Sample Configuration

```json
{
  "apps": [
    {
      "id": "plex",
      "name": "Plex",
      "url": "http://plex.local:32400/web",
      "icon": "🎬",
      "group": "Media",
      "order": 0,
      "status": "unknown"
    }
  ],
  "groups": ["Media", "Management"],
  "settings": {
    "theme": "dark",
    "showStatus": true,
    "autoRefresh": false,
    "sidebarCollapsed": false
  },
  "version": "1.0.0"
}
```

### Docker Volumes

The Docker setup automatically mounts `./data` to `/app/data` for persistence. Your configuration will survive container restarts and updates.

## Usage

### Adding Apps

1. Click the **"+ Add App"** button in the sidebar
2. Fill in the app details:
   - **Name**: Display name for your app
   - **URL**: Full URL to your application
   - **Icon**: Emoji, image URL, or SVG
   - **Group**: Optional category (create new or use existing)
3. Click **"Add App"** to save

### Managing Apps

- **Click** an app icon to load it in the main panel
- **Right-click** an app for edit/delete options
- **Drag and drop** to reorder apps
- **Search** using the search bar to filter apps

### Import/Export

- **Export**: Download your configuration as a JSON file
- **Import**: Upload a configuration file or paste JSON data
- **Backup**: Configuration files can be easily backed up and restored

### Status Monitoring

Portal can optionally check if your apps are online:

- **Green dot**: App is responding
- **Red dot**: App is not responding
- **Gray dot**: Status unknown/not checked

Click the refresh button in the app header to manually check status.

## API Endpoints

Portal provides a REST API for programmatic access:

- `GET /api/apps` - Get all apps
- `POST /api/apps` - Create new app
- `PUT /api/apps/[id]` - Update app
- `DELETE /api/apps/[id]` - Delete app
- `GET /api/config` - Get full configuration
- `POST /api/config` - Import configuration
- `GET /api/status/[id]` - Check app status

## Customization

### Icons

Portal supports multiple icon types:

- **Emojis**: `🎬`, `📺`, `🍿`
- **Image URLs**: `https://example.com/icon.png`
- **SVG**: Inline SVG code
- **Fallback**: First letter of app name

### Themes

Currently supports dark theme with plans for light theme and custom themes in future versions.

## Docker Configuration

### Environment Variables

- `NODE_ENV`: Set to `production` for production builds
- `PORT`: Server port (default: 3000)
- `HOSTNAME`: Server hostname (default: 0.0.0.0)

### Health Checks

The container includes health checks that verify the API is responding correctly.

### Volumes

- `/app/data`: Configuration and data storage
- Mount `./data:/app/data` to persist your configuration

## Development

### Project Structure

```
portal/
├── src/
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── components/    # React components
│   │   ├── globals.css    # Global styles
│   │   ├── layout.tsx     # Root layout
│   │   └── page.tsx       # Main page
│   └── lib/
│       ├── types.ts       # TypeScript types
│       └── utils.ts       # Utility functions
├── data/
│   └── tabs.json         # Configuration file
├── Dockerfile            # Docker build config
├── docker-compose.yml    # Docker Compose config
└── package.json          # Dependencies
```

### Tech Stack

- **Frontend**: Next.js 14, React 18, TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Headless UI, Heroicons
- **Drag & Drop**: @hello-pangea/dnd
- **Deployment**: Docker, Docker Compose

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Troubleshooting

### Common Issues

**Apps not loading in iframe**:
- Check if the target app allows iframe embedding
- Some apps block iframe access for security
- Use "Open in New Tab" button as alternative

**Configuration not persisting**:
- Ensure `./data` directory has write permissions
- Check Docker volume mounts are correct
- Verify `tabs.json` file is not read-only

**Status checks failing**:
- Ensure target apps are accessible from the Portal container
- Check network connectivity and firewall rules
- Some apps may block HEAD requests used for status checks

### Logs

View container logs:
```bash
docker-compose logs portal
```

## License

MIT License - see LICENSE file for details.

## Support

- **Issues**: Report bugs and feature requests on GitHub
- **Discussions**: Join community discussions
- **Documentation**: Check the wiki for advanced configuration

---

**Portal** - Your apps, organized. 🚀
