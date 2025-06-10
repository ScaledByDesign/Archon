/**
 * Test Environment Setup and Verification Script
 * 
 * This script verifies that the testing environment is properly configured
 * for Authentik/Traefik integration testing.
 */

const { exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

async function checkDockerServices() {
  console.log('🔍 Checking Docker services...');
  
  try {
    const { stdout } = await execAsync('docker-compose -f ../docker-compose.core.yml ps --services --filter "status=running"');
    const runningServices = stdout.trim().split('\n').filter(s => s);
    
    const requiredServices = [
      'traefik',
      'authentik-server', 
      'authentik-worker',
      'dashy',
      'postgres',
      'redis'
    ];
    
    const missingServices = requiredServices.filter(service => !runningServices.includes(service));
    
    if (missingServices.length > 0) {
      console.log('❌ Missing services:', missingServices.join(', '));
      console.log('💡 Run: docker-compose -f docker-compose.core.yml up -d');
      return false;
    }
    
    console.log('✅ All required Docker services are running');
    return true;
    
  } catch (error) {
    console.log('❌ Error checking Docker services:', error.message);
    return false;
  }
}

async function checkServiceHealth() {
  console.log('🏥 Checking service health...');
  
  const healthChecks = [
    { name: 'Traefik', url: 'http://localhost:8080/ping' },
    { name: 'Authentik', url: 'http://localhost:9000/if/flow/default-authentication-flow/' },
    { name: 'Dashy', url: 'http://localhost:4001' }
  ];
  
  const results = [];
  
  for (const check of healthChecks) {
    try {
      const fetch = (await import('node-fetch')).default;
      const response = await fetch(check.url, { 
        timeout: 5000,
        headers: { 'User-Agent': 'test-setup-script' }
      });
      
      if (response.status < 400) {
        console.log(`✅ ${check.name} is healthy (${response.status})`);
        results.push(true);
      } else {
        console.log(`⚠️ ${check.name} returned ${response.status}`);
        results.push(false);
      }
    } catch (error) {
      console.log(`❌ ${check.name} health check failed:`, error.message);
      results.push(false);
    }
  }
  
  return results.every(r => r);
}

async function checkHostsFile() {
  console.log('🌐 Checking hosts file configuration...');
  
  try {
    const fs = require('fs');
    const hostsContent = fs.readFileSync('/etc/hosts', 'utf8');
    
    const requiredHosts = [
      'dashy.localhost',
      'auth.localhost', 
      'traefik.localhost',
      'api.localhost',
      'llm.localhost'
    ];
    
    const missingHosts = requiredHosts.filter(host => !hostsContent.includes(host));
    
    if (missingHosts.length > 0) {
      console.log('⚠️ Missing localhost entries in /etc/hosts:');
      console.log('💡 Add these lines to /etc/hosts:');
      missingHosts.forEach(host => {
        console.log(`   127.0.0.1 ${host}`);
      });
      return false;
    }
    
    console.log('✅ All required localhost entries found in hosts file');
    return true;
    
  } catch (error) {
    console.log('⚠️ Could not check hosts file (may require sudo):', error.message);
    console.log('💡 Ensure these entries exist in /etc/hosts:');
    console.log('   127.0.0.1 dashy.localhost auth.localhost traefik.localhost api.localhost llm.localhost');
    return true; // Don't fail, just warn
  }
}

async function checkEnvironmentVariables() {
  console.log('🔧 Checking environment variables...');
  
  const envVars = {
    'BASE_URL': process.env.BASE_URL || 'https://dashy.localhost',
    'AUTHENTIK_USER': process.env.AUTHENTIK_USER || 'admin',
    'AUTHENTIK_PASSWORD': process.env.AUTHENTIK_PASSWORD || 'admin123!'
  };
  
  console.log('📋 Environment configuration:');
  Object.entries(envVars).forEach(([key, value]) => {
    if (key === 'AUTHENTIK_PASSWORD') {
      console.log(`   ${key}: ${'*'.repeat(value.length)}`);
    } else {
      console.log(`   ${key}: ${value}`);
    }
  });
  
  return true;
}

async function generateTestReport() {
  console.log('\n📊 Test Environment Report');
  console.log('=' * 50);
  
  const checks = [
    { name: 'Docker Services', fn: checkDockerServices },
    { name: 'Service Health', fn: checkServiceHealth },
    { name: 'Hosts Configuration', fn: checkHostsFile },
    { name: 'Environment Variables', fn: checkEnvironmentVariables }
  ];
  
  const results = [];
  
  for (const check of checks) {
    console.log(`\n🔍 ${check.name}:`);
    const result = await check.fn();
    results.push({ name: check.name, success: result });
  }
  
  console.log('\n📈 Summary:');
  let allPassed = true;
  results.forEach(result => {
    const status = result.success ? '✅' : '❌';
    console.log(`   ${status} ${result.name}`);
    if (!result.success) allPassed = false;
  });
  
  if (allPassed) {
    console.log('\n🎉 Environment is ready for testing!');
    console.log('💡 Run tests with: npm test');
  } else {
    console.log('\n⚠️ Some issues found. Please address them before running tests.');
  }
  
  return allPassed;
}

// Main execution
if (require.main === module) {
  generateTestReport().then(success => {
    process.exit(success ? 0 : 1);
  }).catch(error => {
    console.error('❌ Setup check failed:', error);
    process.exit(1);
  });
}

module.exports = {
  checkDockerServices,
  checkServiceHealth,
  checkHostsFile,
  checkEnvironmentVariables,
  generateTestReport
}; 