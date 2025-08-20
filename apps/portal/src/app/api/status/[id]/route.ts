import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';
import { Config, ApiResponse, StatusCheckResult } from '@/lib/types';

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

async function checkAppStatus(url: string): Promise<{ status: 'online' | 'offline'; responseTime?: number }> {
  const startTime = Date.now();
  
  try {
    // Use fetch with timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

    const response = await fetch(url, {
      method: 'HEAD',
      signal: controller.signal,
      headers: {
        'User-Agent': 'Portal-App-Organizer/1.0',
      },
    });

    clearTimeout(timeoutId);
    const responseTime = Date.now() - startTime;

    return {
      status: response.ok ? 'online' : 'offline',
      responseTime,
    };
  } catch (error) {
    return {
      status: 'offline',
      responseTime: Date.now() - startTime,
    };
  }
}

// GET /api/status/[id] - Check app status
export async function GET(
  request: NextRequest,
  context: { params: Promise<{ id: string }> }
): Promise<NextResponse<ApiResponse<StatusCheckResult>>> {
  try {
    const params = await context.params;
    const config = await readConfig();
    const app = config.apps.find(a => a.id === params.id);
    
    if (!app) {
      return NextResponse.json({
        success: false,
        error: 'App not found',
      }, { status: 404 });
    }

    const statusCheck = await checkAppStatus(app.url);
    const result: StatusCheckResult = {
      id: app.id,
      status: statusCheck.status,
      responseTime: statusCheck.responseTime,
      lastChecked: new Date().toISOString(),
    };

    // Update app status in config
    app.status = statusCheck.status;
    app.updatedAt = new Date().toISOString();
    await writeConfig(config);

    return NextResponse.json({
      success: true,
      data: result,
    });
  } catch (error) {
    console.error('Error checking app status:', error);
    return NextResponse.json({
      success: false,
      error: 'Failed to check app status',
    }, { status: 500 });
  }
}

// POST /api/status/[id] - Force status check
export async function POST(
  request: NextRequest,
  context: { params: Promise<{ id: string }> }
): Promise<NextResponse<ApiResponse<StatusCheckResult>>> {
  // Same as GET but explicitly for forcing a check
  return GET(request, context);
}
