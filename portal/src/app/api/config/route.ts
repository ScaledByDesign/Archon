import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';
import { Config, ApiResponse } from '@/lib/types';
import { getDefaultConfig, importConfig } from '@/lib/utils';

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

// GET /api/config - Get full config
export async function GET(): Promise<NextResponse<ApiResponse<Config>>> {
  try {
    const config = await readConfig();
    return NextResponse.json({
      success: true,
      data: config,
    });
  } catch (error) {
    console.error('Error reading config:', error);
    return NextResponse.json({
      success: false,
      error: 'Failed to read config',
    }, { status: 500 });
  }
}

// POST /api/config - Import config
export async function POST(request: NextRequest): Promise<NextResponse<ApiResponse<Config>>> {
  try {
    const body = await request.json();
    const { config: configData } = body;

    if (!configData) {
      return NextResponse.json({
        success: false,
        error: 'Config data is required',
      }, { status: 400 });
    }

    const importResult = importConfig(typeof configData === 'string' ? configData : JSON.stringify(configData));
    
    if (!importResult.valid) {
      return NextResponse.json({
        success: false,
        error: importResult.error || 'Invalid config format',
      }, { status: 400 });
    }

    await writeConfig(importResult.config!);

    return NextResponse.json({
      success: true,
      data: importResult.config!,
    });
  } catch (error) {
    console.error('Error importing config:', error);
    return NextResponse.json({
      success: false,
      error: 'Failed to import config',
    }, { status: 500 });
  }
}

// PUT /api/config - Update config settings
export async function PUT(request: NextRequest): Promise<NextResponse<ApiResponse<Config>>> {
  try {
    const body = await request.json();
    const { settings } = body;

    if (!settings) {
      return NextResponse.json({
        success: false,
        error: 'Settings are required',
      }, { status: 400 });
    }

    const config = await readConfig();
    config.settings = {
      ...config.settings,
      ...settings,
    };

    await writeConfig(config);

    return NextResponse.json({
      success: true,
      data: config,
    });
  } catch (error) {
    console.error('Error updating config:', error);
    return NextResponse.json({
      success: false,
      error: 'Failed to update config',
    }, { status: 500 });
  }
}
