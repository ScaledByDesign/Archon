import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';
import { App, Config, ApiResponse } from '@/lib/types';
import { validateAppData } from '@/lib/utils';

const DATA_DIR = path.join(process.cwd(), 'data');
const CONFIG_FILE = path.join(DATA_DIR, 'tabs.json');

async function readConfig(): Promise<Config> {
  try {
    const data = await fs.readFile(CONFIG_FILE, 'utf-8');
    return JSON.parse(data);
  } catch (error) {
    throw new Error('Failed to read config');
  }
}

async function writeConfig(config: Config): Promise<void> {
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

// GET /api/apps/[id] - Get specific app
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
): Promise<NextResponse<ApiResponse<App>>> {
  const { id } = await params;
  try {
    const config = await readConfig();
    const app = config.apps.find(a => a.id === id);
    
    if (!app) {
      return NextResponse.json({
        success: false,
        error: 'App not found',
      }, { status: 404 });
    }

    return NextResponse.json({
      success: true,
      data: app,
    });
  } catch (error) {
    console.error('Error reading app:', error);
    return NextResponse.json({
      success: false,
      error: 'Failed to read app',
    }, { status: 500 });
  }
}

// PUT /api/apps/[id] - Update app
export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
): Promise<NextResponse<ApiResponse<App>>> {
  const { id } = await params;
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
    const appIndex = config.apps.findIndex(a => a.id === id);
    
    if (appIndex === -1) {
      return NextResponse.json({
        success: false,
        error: 'App not found',
      }, { status: 404 });
    }

    const existingApp = config.apps[appIndex];
    const updatedApp: App = {
      ...existingApp,
      name: body.name,
      url: body.url,
      icon: body.icon,
      group: body.group || undefined,
      updatedAt: new Date().toISOString(),
    };

    config.apps[appIndex] = updatedApp;
    
    // Add group if it doesn't exist
    if (updatedApp.group && !config.groups.includes(updatedApp.group)) {
      config.groups.push(updatedApp.group);
    }

    // Remove group if no apps use it anymore
    if (existingApp.group && existingApp.group !== updatedApp.group) {
      const groupStillUsed = config.apps.some(app => 
        app.id !== id && app.group === existingApp.group
      );
      if (!groupStillUsed) {
        config.groups = config.groups.filter(g => g !== existingApp.group);
      }
    }

    await writeConfig(config);

    return NextResponse.json({
      success: true,
      data: updatedApp,
    });
  } catch (error) {
    console.error('Error updating app:', error);
    return NextResponse.json({
      success: false,
      error: 'Failed to update app',
    }, { status: 500 });
  }
}

// DELETE /api/apps/[id] - Delete app
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
): Promise<NextResponse<ApiResponse<void>>> {
  const { id } = await params;
  try {
    const config = await readConfig();
    const appIndex = config.apps.findIndex(a => a.id === id);
    
    if (appIndex === -1) {
      return NextResponse.json({
        success: false,
        error: 'App not found',
      }, { status: 404 });
    }

    const deletedApp = config.apps[appIndex];
    config.apps.splice(appIndex, 1);

    // Remove group if no apps use it anymore
    if (deletedApp.group) {
      const groupStillUsed = config.apps.some(app => app.group === deletedApp.group);
      if (!groupStillUsed) {
        config.groups = config.groups.filter(g => g !== deletedApp.group);
      }
    }

    await writeConfig(config);

    return NextResponse.json({
      success: true,
    });
  } catch (error) {
    console.error('Error deleting app:', error);
    return NextResponse.json({
      success: false,
      error: 'Failed to delete app',
    }, { status: 500 });
  }
}
