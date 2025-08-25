const { chromium } = require('playwright');

async function testUIDirectly() {
  console.log('🧪 Testing UI directly - checking WebSocket message flow');

  const browser = await chromium.launch({
    headless: false, // Show browser so we can see what happens
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  // Enhanced console logging
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('WebSocket') || text.includes('assistant') || text.includes('final') || text.includes('MCP')) {
      console.log(`📡 Browser: [${new Date().toLocaleTimeString()}] ${text}`);
    }
  });

  try {
    console.log('🌐 Navigating to Zoi interface...');
    await page.goto('http://localhost:7000');
    
    // Wait for the interface to load
    await page.waitForSelector('#textInput', { timeout: 10000 });
    await page.waitForSelector('#sendBtn', { timeout: 5000 });
    console.log('✅ Interface loaded');

    // Wait for WebSocket connection
    await page.waitForFunction(() => {
      return window.socket && window.socket.readyState === WebSocket.OPEN;
    }, { timeout: 10000 });
    console.log('🔌 WebSocket connected');

    // Set up message monitoring
    await page.evaluate(() => {
      window.messageLog = [];
      
      // Override the handleJSONMessage function to log all messages
      const originalHandler = window.handleJSONMessage;
      window.handleJSONMessage = function(msg) {
        window.messageLog.push({
          timestamp: new Date().toISOString(),
          type: msg.type,
          content: msg.content
        });
        console.log('📨 WebSocket Message:', msg.type, msg.content);
        return originalHandler.call(this, msg);
      };
    });

    // Send a simple health check query
    const testQuery = "check system health";
    console.log(`📝 Sending query: "${testQuery}"`);
    
    await page.fill('#textInput', testQuery);
    await page.click('#sendBtn');

    // Wait and monitor for responses
    console.log('⏳ Waiting for responses...');
    await page.waitForTimeout(30000); // Wait 30 seconds

    // Check what messages we received
    const messages = await page.evaluate(() => window.messageLog || []);
    console.log('\n📋 Messages received:');
    messages.forEach((msg, i) => {
      console.log(`  ${i + 1}. [${msg.timestamp}] ${msg.type}: ${JSON.stringify(msg.content).substring(0, 100)}...`);
    });

    // Check if we got a final_assistant_answer
    const finalAnswers = messages.filter(msg => msg.type === 'final_assistant_answer');
    console.log(`\n🎯 Final assistant answers received: ${finalAnswers.length}`);
    
    if (finalAnswers.length > 0) {
      console.log('✅ SUCCESS: Final assistant answer was received!');
      finalAnswers.forEach((answer, i) => {
        console.log(`   Answer ${i + 1}: ${answer.content}`);
      });
    } else {
      console.log('❌ ISSUE: No final_assistant_answer messages received');
      
      // Check what we did get
      const messageTypes = [...new Set(messages.map(msg => msg.type))];
      console.log(`   Message types received: ${messageTypes.join(', ')}`);
    }

    // Check the chat history in the UI
    const chatHistory = await page.evaluate(() => {
      return window.chatHistory || [];
    });
    console.log(`\n💬 Chat history entries: ${chatHistory.length}`);
    chatHistory.forEach((entry, i) => {
      console.log(`   ${i + 1}. ${entry.role}: ${entry.content.substring(0, 100)}...`);
    });

  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    console.log('\n🏁 Test completed');
    await browser.close();
  }
}

testUIDirectly().catch(console.error);
