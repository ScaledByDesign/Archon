#!/usr/bin/env node

/**
 * Simple Webhook Server for Grafana Alerts
 * Receives and logs alerts to console for the Zoi AI Platform
 */

const http = require('http');
const url = require('url');

const PORT = 3000;
const HOST = '0.0.0.0';

// ANSI color codes for console output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

function formatAlert(alert) {
  const timestamp = new Date().toISOString();
  const status = alert.status || 'unknown';
  const severity = alert.labels?.severity || 'unknown';
  const component = alert.labels?.component || 'unknown';
  const alertname = alert.labels?.alertname || 'Unknown Alert';
  
  let statusColor = colors.blue;
  if (status === 'firing') statusColor = colors.red;
  if (status === 'resolved') statusColor = colors.green;
  
  let severityColor = colors.blue;
  if (severity === 'critical') severityColor = colors.red;
  if (severity === 'warning') severityColor = colors.yellow;
  
  return `${colors.bright}[${timestamp}]${colors.reset} ` +
         `${statusColor}${status.toUpperCase()}${colors.reset} ` +
         `${severityColor}${severity.toUpperCase()}${colors.reset} ` +
         `${colors.cyan}${component}${colors.reset} ` +
         `${colors.bright}${alertname}${colors.reset}\n` +
         `  ${colors.magenta}Description:${colors.reset} ${alert.annotations?.description || 'No description'}\n` +
         `  ${colors.magenta}Started:${colors.reset} ${alert.startsAt || 'Unknown'}\n`;
}

const server = http.createServer((req, res) => {
  const parsedUrl = url.parse(req.url, true);
  
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  // Handle preflight requests
  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }
  
  // Health check endpoint
  if (parsedUrl.pathname === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ 
      status: 'healthy', 
      service: 'Zoi Alert Webhook Server',
      timestamp: new Date().toISOString()
    }));
    return;
  }
  
  // Webhook endpoint for alerts
  if (parsedUrl.pathname === '/webhook/console' && req.method === 'POST') {
    let body = '';
    
    req.on('data', chunk => {
      body += chunk.toString();
    });
    
    req.on('end', () => {
      try {
        const alertData = JSON.parse(body);
        
        console.log(`\n${colors.bright}${colors.blue}=== ZOI AI PLATFORM ALERT ===${colors.reset}`);
        
        if (alertData.alerts && Array.isArray(alertData.alerts)) {
          alertData.alerts.forEach(alert => {
            console.log(formatAlert(alert));
          });
        } else {
          console.log(formatAlert(alertData));
        }
        
        console.log(`${colors.bright}${colors.blue}================================${colors.reset}\n`);
        
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ 
          status: 'received', 
          alertCount: alertData.alerts?.length || 1,
          timestamp: new Date().toISOString()
        }));
        
      } catch (error) {
        console.error(`${colors.red}Error parsing alert webhook:${colors.reset}`, error.message);
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ 
          status: 'error', 
          message: 'Invalid JSON payload' 
        }));
      }
    });
    
    return;
  }
  
  // Default 404 response
  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ 
    status: 'not_found', 
    message: 'Endpoint not found' 
  }));
});

server.listen(PORT, HOST, () => {
  console.log(`${colors.bright}${colors.green}🚀 Zoi Alert Webhook Server running on http://${HOST}:${PORT}${colors.reset}`);
  console.log(`${colors.cyan}Health check: http://${HOST}:${PORT}/health${colors.reset}`);
  console.log(`${colors.cyan}Webhook endpoint: http://${HOST}:${PORT}/webhook/console${colors.reset}`);
  console.log(`${colors.yellow}Waiting for alerts from Grafana...${colors.reset}\n`);
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log(`\n${colors.yellow}Shutting down Zoi Alert Webhook Server...${colors.reset}`);
  server.close(() => {
    console.log(`${colors.green}Server closed gracefully${colors.reset}`);
    process.exit(0);
  });
});

process.on('SIGTERM', () => {
  console.log(`\n${colors.yellow}Received SIGTERM, shutting down...${colors.reset}`);
  server.close(() => {
    console.log(`${colors.green}Server closed gracefully${colors.reset}`);
    process.exit(0);
  });
});
