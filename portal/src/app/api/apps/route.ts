import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';
import { App, Config, ApiResponse } from '@/lib/types';
import { getDefaultConfig, generateId, validateAppData } from '@/lib/utils';

const DATA_DIR = path.join(process.cwd(), 'data');
const CONFIG_FILE = path.join(DATA_DIR, 'tabs.json');

async function ensureDataDir() {
  try {
    await fs.access(DATA_DIR);
  } catch {
    await fs.mkdir(DATA_DIR, { recursive: true });
  }
}

async function readConfig(): Promise<Config> {
  try {
    await ensureDataDir();
    const data = await fs.readFile(CONFIG_FILE, 'utf-8');
    return JSON.parse(data);
  } catch (error) {
    // If file doesn't exist or is invalid, return default config
    const defaultConfig = getDefaultConfig();
    await writeConfig(defaultConfig);
    return defaultConfig;
  }
}

async function writeConfig(config: Config): Promise<void> {
  await ensureDataDir();
  
  // Create backup
  try {
    await fs.access(CONFIG_FILE);
    const backup = CONFIG_FILE + '.bak';
    await fs.copyFile(CONFIG_FILE, backup);
  } catch {
    // No existing file to backup
  }

  // Write new config atomically
  const tempFile = CONFIG_FILE + '.tmp';
  await fs.writeFile(tempFile, JSON.stringify(config, null, 2));
  await fs.rename(tempFile, CONFIG_FILE);
}

// GET /api/apps - Get all apps
export async function GET(): Promise<NextResponse<ApiResponse<App[]>>> {
  try {
    const config = await readConfig();
    return NextResponse.json({
      success: true,
      data: config.apps,
    });
  } catch (error) {
    console.error('Error reading apps:', error);
    return NextResponse.json({
      success: false,
      error: 'Failed to read apps',
    }, { status: 500 });
  }
}

// POST /api/apps - Add new app
export async function POST(request: NextRequest): Promise<NextResponse<ApiResponse<App>>> {
  try {
    const body = await request.json();
    const validation = validateAppData(body);
    
    if (!validation.valid) {
      return NextResponse.json({
        success: false,
        error: validation.errors.join(', '),
      }, { status: 400 });
    }

    const config = await readConfig();
    const newApp: App = {
      id: generateId(),
      name: body.name,
      url: body.url,
      icon: body.icon,
      group: body.group || undefined,
      order: body.order ?? config.apps.length,
      status: 'unknown',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    config.apps.push(newApp);
    
    // Add group if it doesn't exist
    if (newApp.group && !config.groups.includes(newApp.group)) {
      config.groups.push(newApp.group);
    }

    await writeConfig(config);

    return NextResponse.json({
      success: true,
      data: newApp,
    });
  } catch (error) {
    console.error('Error adding app:', error);
    return NextResponse.json({
      success: false,
      error: 'Failed to add app',
    }, { status: 500 });
  }
}

// PUT /api/apps - Update app order (for reordering)
export async function PUT(request: NextRequest): Promise<NextResponse<ApiResponse<App[]>>> {
  try {
    const body = await request.json();
    const { apps } = body;

    if (!Array.isArray(apps)) {
      return NextResponse.json({
        success: false,
        error: 'Apps array is required',
      }, { status: 400 });
    }

    const config = await readConfig();
    
    // Replace the entire apps array with the reordered one
    // This ensures the order is properly maintained in the JSON file
    const updatedApps = apps.map((app, index) => {
      const existingApp = config.apps.find(a => a.id === app.id);
      if (existingApp) {
        return {
          ...existingApp,
          order: index,
          updatedAt: new Date().toISOString(),
        };
      }
      return app;
    });

    // Update the config with the new order
    config.apps = updatedApps;
    await writeConfig(config);

    return NextResponse.json({
      success: true,
      data: config.apps,
    });
  } catch (error) {
    console.error('Error reordering apps:', error);
    return NextResponse.json({
      success: false,
      error: 'Failed to reorder apps',
    }, { status: 500 });
  }
}
