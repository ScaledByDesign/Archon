(function() {
  const originalLog = console.log.bind(console);
  console.log = (...args) => {
    const now = new Date();
    const hh = String(now.getHours()).padStart(2, '0');
    const mm = String(now.getMinutes()).padStart(2, '0');
    const ss = String(now.getSeconds()).padStart(2, '0');
    const ms = String(now.getMilliseconds()).padStart(3, '0');
    originalLog(
      `[${hh}:${mm}:${ss}.${ms}]`,
      ...args
    );
  };
})();

const statusDiv = document.getElementById("status");
const messagesDiv = document.getElementById("messages");
const speedSlider = document.getElementById("speedSlider");
const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");
const wakeWordHint = document.getElementById("wakeWordHint");
speedSlider.disabled = true;  // start disabled

// Status management
function updateStatus(status, message) {
  if (statusDiv) statusDiv.textContent = message;
  if (statusText) statusText.textContent = status;

  if (statusDot) {
    statusDot.className = 'status-dot';
    switch (status.toLowerCase()) {
      case 'connected':
      case 'ready':
        statusDot.classList.add('active');
        break;
      case 'listening':
        statusDot.classList.add('pulse');
        break;
      case 'initializing':
      case 'connecting':
        statusDot.classList.add('pulse');
        break;
      default:
        statusDot.classList.add('inactive');
    }
  }
}

// Wake word detection
function detectWakeWord(text) {
  const lowerText = text.toLowerCase().trim();
  console.log("Checking for wake word in:", lowerText);

  for (const wakeWord of WAKE_WORDS) {
    if (lowerText.includes(wakeWord)) {
      console.log("Wake word detected:", wakeWord);
      return true;
    }
  }
  return false;
}

function activateConversationMode() {
  console.log("🎤 Activating conversation mode");
  isListeningForWakeWord = false;
  isInActiveConversation = true;
  updateStatus("Listening", "Zoi is listening...");

  // Hide wake word hint
  if (wakeWordHint) {
    wakeWordHint.style.display = 'none';
  }

  // Clear any existing timeout
  if (conversationTimeout) {
    clearTimeout(conversationTimeout);
  }

  // Set timeout to return to wake word mode after silence
  conversationTimeout = setTimeout(() => {
    deactivateConversationMode();
  }, WAKE_WORD_TIMEOUT);
}

function deactivateConversationMode() {
  console.log("💤 Returning to wake word mode");
  isListeningForWakeWord = true;
  isInActiveConversation = false;
  updateStatus("Ready", "Say 'Hey Zoi' to start");

  // Show wake word hint
  if (wakeWordHint) {
    wakeWordHint.style.display = 'inline';
  }

  if (conversationTimeout) {
    clearTimeout(conversationTimeout);
    conversationTimeout = null;
  }
}

function resetConversationTimeout() {
  if (conversationTimeout) {
    clearTimeout(conversationTimeout);
    conversationTimeout = setTimeout(() => {
      deactivateConversationMode();
    }, WAKE_WORD_TIMEOUT);
  }
}

let socket = null;
let audioContext = null;
let mediaStream = null;
let micWorkletNode = null;
let ttsWorkletNode = null;

let isTTSPlaying = false;
let ignoreIncomingTTS = false;

// Wake word detection state
let isListeningForWakeWord = true;
let isInActiveConversation = false;
let wakeWordBuffer = [];
let conversationTimeout = null;
let WAKE_WORD_TIMEOUT = 30000; // 30 seconds of silence to return to wake word mode (modifiable)
const WAKE_WORDS = ['hey zoi', 'hi zoi', 'hello zoi', 'zoi'];

let chatHistory = [];
let typingUser = "";
let typingAssistant = "";

// --- batching + fixed 8‑byte header setup ---
const BATCH_SAMPLES = 2048;
const HEADER_BYTES  = 8;
const FRAME_BYTES   = BATCH_SAMPLES * 2;
const MESSAGE_BYTES = HEADER_BYTES + FRAME_BYTES;

const bufferPool = [];
let batchBuffer = null;
let batchView = null;
let batchInt16 = null;
let batchOffset = 0;

function initBatch() {
  if (!batchBuffer) {
    batchBuffer = bufferPool.pop() || new ArrayBuffer(MESSAGE_BYTES);
    batchView   = new DataView(batchBuffer);
    batchInt16  = new Int16Array(batchBuffer, HEADER_BYTES);
    batchOffset = 0;
  }
}

function flushBatch() {
  const ts = Date.now() & 0xFFFFFFFF;
  batchView.setUint32(0, ts, false);
  const flags = isTTSPlaying ? 1 : 0;
  batchView.setUint32(4, flags, false);

  socket.send(batchBuffer);

  bufferPool.push(batchBuffer);
  batchBuffer = null;
}

function flushRemainder() {
  if (batchOffset > 0) {
    for (let i = batchOffset; i < BATCH_SAMPLES; i++) {
      batchInt16[i] = 0;
    }
    flushBatch();
  }
}

function initAudioContext() {
  if (!audioContext) {
    audioContext = new AudioContext();
  }
  // Resume audio context if suspended (required by browser policies)
  if (audioContext.state === 'suspended') {
    audioContext.resume();
  }
}

function base64ToInt16Array(b64) {
  const raw = atob(b64);
  const buf = new ArrayBuffer(raw.length);
  const view = new Uint8Array(buf);
  for (let i = 0; i < raw.length; i++) {
    view[i] = raw.charCodeAt(i);
  }
  return new Int16Array(buf);
}

async function startRawPcmCapture() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        sampleRate: { ideal: 24000 },
        channelCount: 1,
        echoCancellation: true,
        // autoGainControl: true,
        noiseSuppression: true
      }
    });
    mediaStream = stream;
    initAudioContext();
    await audioContext.audioWorklet.addModule('/static/pcmWorkletProcessor.js');
    micWorkletNode = new AudioWorkletNode(audioContext, 'pcm-worklet-processor');

    micWorkletNode.port.onmessage = ({ data }) => {
      const incoming = new Int16Array(data);
      let read = 0;
      while (read < incoming.length) {
        initBatch();
        const toCopy = Math.min(
          incoming.length - read,
          BATCH_SAMPLES - batchOffset
        );
        batchInt16.set(
          incoming.subarray(read, read + toCopy),
          batchOffset
        );
        batchOffset += toCopy;
        read       += toCopy;
        if (batchOffset === BATCH_SAMPLES) {
          flushBatch();
        }
      }
    };

    const source = audioContext.createMediaStreamSource(stream);
    source.connect(micWorkletNode);
    statusDiv.textContent = "Recording...";
  } catch (err) {
    statusDiv.textContent = "Mic access denied.";
    console.error(err);
  }
}

async function setupTTSPlayback() {
  // Ensure audio context is initialized even if mic access failed
  initAudioContext();
  await audioContext.audioWorklet.addModule('/static/ttsPlaybackProcessor.js');
  ttsWorkletNode = new AudioWorkletNode(
    audioContext,
    'tts-playback-processor'
  );

  ttsWorkletNode.port.onmessage = (event) => {
    const { type } = event.data;
    if (type === 'ttsPlaybackStarted') {
      if (!isTTSPlaying && socket && socket.readyState === WebSocket.OPEN) {
        isTTSPlaying = true;
        console.log(
          "TTS playback started. Reason: ttsWorkletNode Event ttsPlaybackStarted."
        );
        socket.send(JSON.stringify({ type: 'tts_start' }));
      }
    } else if (type === 'ttsPlaybackStopped') {
      if (isTTSPlaying && socket && socket.readyState === WebSocket.OPEN) {
        isTTSPlaying = false;
        console.log(
          "TTS playback stopped. Reason: ttsWorkletNode Event ttsPlaybackStopped."
        );
        socket.send(JSON.stringify({ type: 'tts_stop' }));
      }
    }
  };
  ttsWorkletNode.connect(audioContext.destination);
}

function cleanupAudio() {
  if (micWorkletNode) {
    micWorkletNode.disconnect();
    micWorkletNode = null;
  }
  if (ttsWorkletNode) {
    ttsWorkletNode.disconnect();
    ttsWorkletNode = null;
  }
  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }
  if (mediaStream) {
    mediaStream.getAudioTracks().forEach(track => track.stop());
    mediaStream = null;
  }
}

function renderMessages() {
  messagesDiv.innerHTML = "";
  chatHistory.forEach(msg => {
    const bubble = document.createElement("div");
    bubble.className = `bubble ${msg.role}`;
    bubble.textContent = msg.content;
    messagesDiv.appendChild(bubble);
  });
  if (typingUser) {
    const typing = document.createElement("div");
    typing.className = "bubble user typing";
    typing.innerHTML = typingUser + '<span style="opacity:.6;">✏️</span>';
    messagesDiv.appendChild(typing);
  }
  if (typingAssistant) {
    const typing = document.createElement("div");
    typing.className = "bubble assistant typing";
    typing.innerHTML = typingAssistant + '<span style="opacity:.6;">✏️</span>';
    messagesDiv.appendChild(typing);
  }
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function handleJSONMessage({ type, content }) {
  if (type === "partial_user_request") {
    const trimmedContent = content?.trim() || "";

    // Wake word detection mode
    if (isListeningForWakeWord && trimmedContent) {
      if (detectWakeWord(trimmedContent)) {
        activateConversationMode();
        // Don't show the wake word in chat
        return;
      }
      // In wake word mode, don't show partial transcriptions
      return;
    }

    // Active conversation mode
    if (isInActiveConversation && trimmedContent) {
      resetConversationTimeout();
      typingUser = escapeHtml(trimmedContent);
      renderMessages();
    }
    return;
  }

  if (type === "final_user_request") {
    const trimmedContent = content?.trim() || "";

    // Wake word detection mode
    if (isListeningForWakeWord && trimmedContent) {
      if (detectWakeWord(trimmedContent)) {
        activateConversationMode();
        // Don't add wake word to chat history
        return;
      }
      // Ignore non-wake-word utterances in wake word mode
      return;
    }

    // Active conversation mode
    if (isInActiveConversation && trimmedContent) {
      resetConversationTimeout();
      chatHistory.push({ role: "user", content: trimmedContent, type: "final" });
    }

    typingUser = "";
    renderMessages();
    return;
  }
  if (type === "partial_assistant_answer") {
    typingAssistant = content?.trim() ? escapeHtml(content) : "";
    renderMessages();
    return;
  }
  if (type === "final_assistant_answer") {
    if (content?.trim()) {
      chatHistory.push({ role: "assistant", content, type: "final" });
    }
    typingAssistant = "";
    renderMessages();
    return;
  }
  if (type === "tts_chunk") {
    if (ignoreIncomingTTS) return;
    const int16Data = base64ToInt16Array(content);
    if (ttsWorkletNode) {
      ttsWorkletNode.port.postMessage(int16Data);
    }
    return;
  }
  if (type === "tts_interruption") {
    if (ttsWorkletNode) {
      ttsWorkletNode.port.postMessage({ type: "clear" });
    }
    isTTSPlaying = false;
    ignoreIncomingTTS = false;
    return;
  }
  if (type === "stop_tts") {
    if (ttsWorkletNode) {
      ttsWorkletNode.port.postMessage({ type: "clear" });
    }
    isTTSPlaying = false;
    ignoreIncomingTTS = true;
    console.log("TTS playback stopped. Reason: tts_interruption.");
    socket.send(JSON.stringify({ type: 'tts_stop' }));
    return;
  }
}

function escapeHtml(str) {
  return (str ?? '')
    .replace(/&/g, "&amp;")
    .replace(/</g, "<")
    .replace(/>/g, ">")
    .replace(/"/g, "&quot;");
}

// UI Controls

document.getElementById("clearBtn").onclick = () => {
  chatHistory = [];
  typingUser = typingAssistant = "";
  renderMessages();
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ type: 'clear_history' }));
  }
};

speedSlider.addEventListener("input", (e) => {
  const speedValue = parseInt(e.target.value);
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({
      type: 'set_speed',
      speed: speedValue
    }));
  }
  console.log("Speed setting changed to:", speedValue);
});

// Auto-start connection function
async function initializeZoi() {
  if (socket && socket.readyState === WebSocket.OPEN) {
    updateStatus("Ready", "Zoi is ready");
    return;
  }

  updateStatus("Connecting", "Establishing connection...");

  const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  socket = new WebSocket(`${wsProto}//${location.host}/ws`);

  socket.onopen = async () => {
    updateStatus("Initializing", "Activating systems...");
    try {
      await startRawPcmCapture();
      await setupTTSPlayback();
      // Start in wake word detection mode
      isListeningForWakeWord = true;
      isInActiveConversation = false;
      updateStatus("Ready", "Say 'Hey Zoi' to start");

      // Show wake word hint
      if (wakeWordHint) {
        wakeWordHint.style.display = 'inline';
      }

      speedSlider.disabled = false;
    } catch (error) {
      console.error("Failed to initialize audio:", error);
      updateStatus("Error", "Audio initialization failed");
    }
  };

  socket.onmessage = (evt) => {
    if (typeof evt.data === "string") {
      try {
        const msg = JSON.parse(evt.data);
        handleJSONMessage(msg);
      } catch (e) {
        console.error("Error parsing message:", e);
      }
    }
  };

  socket.onclose = () => {
    updateStatus("Disconnected", "Connection lost");
    flushRemainder();
    cleanupAudio();
    speedSlider.disabled = true;
  };

  socket.onerror = (err) => {
    updateStatus("Error", "Connection failed");
    cleanupAudio();
    console.error(err);
    speedSlider.disabled = true;
  };
}

// Legacy start button (hidden but functional)
document.getElementById("startBtn").onclick = initializeZoi;

// Settings panel functionality
const settingsOverlay = document.getElementById("settingsOverlay");
const settingsBtn = document.getElementById("settingsBtn");
const settingsClose = document.getElementById("settingsClose");

// Settings controls
const wakeWordSensitivity = document.getElementById("wakeWordSensitivity");
const wakeWordValue = document.getElementById("wakeWordValue");
const conversationTimeoutSlider = document.getElementById("conversationTimeout");
const timeoutValue = document.getElementById("timeoutValue");
const responseSpeed = document.getElementById("responseSpeed");
const speedValue = document.getElementById("speedValue");
const voiceVolume = document.getElementById("voiceVolume");
const volumeValue = document.getElementById("volumeValue");
const continuousListening = document.getElementById("continuousListening");
const debugMode = document.getElementById("debugMode");

// Settings panel open/close
settingsBtn.onclick = () => {
  settingsOverlay.classList.add("active");
};

settingsClose.onclick = () => {
  settingsOverlay.classList.remove("active");
};

settingsOverlay.onclick = (e) => {
  if (e.target === settingsOverlay) {
    settingsOverlay.classList.remove("active");
  }
};

// Settings controls
wakeWordSensitivity.oninput = () => {
  wakeWordValue.textContent = wakeWordSensitivity.value + "%";
};

conversationTimeoutSlider.oninput = () => {
  const value = conversationTimeoutSlider.value;
  timeoutValue.textContent = value + "s";
  // Update the actual timeout value
  WAKE_WORD_TIMEOUT = value * 1000;
};

responseSpeed.oninput = () => {
  speedValue.textContent = responseSpeed.value + "%";
};

voiceVolume.oninput = () => {
  volumeValue.textContent = voiceVolume.value + "%";
};

// Toggle controls
continuousListening.onclick = () => {
  continuousListening.classList.toggle("active");
};

debugMode.onclick = () => {
  debugMode.classList.toggle("active");
};

document.getElementById("stopBtn").onclick = () => {
  if (socket && socket.readyState === WebSocket.OPEN) {
    flushRemainder();
    socket.close();
  }
  cleanupAudio();
  statusDiv.textContent = "Stopped.";
};

document.getElementById("copyBtn").onclick = () => {
  const text = chatHistory
    .map(msg => `${msg.role.charAt(0).toUpperCase() + msg.role.slice(1)}: ${msg.content}`)
    .join('\n');

  navigator.clipboard.writeText(text)
    .then(() => console.log("Conversation copied to clipboard"))
    .catch(err => console.error("Copy failed:", err));
};

document.getElementById("testVoiceBtn").onclick = () => {
  if (socket && socket.readyState === WebSocket.OPEN) {
    // Temporarily activate conversation mode for test
    const wasInWakeWordMode = isListeningForWakeWord;
    if (wasInWakeWordMode) {
      activateConversationMode();
    }

    const testMessage = {
      type: "text_input",
      text: "Hello! I am Zoi, your sovereign intelligence. Let's shape the future together."
    };
    socket.send(JSON.stringify(testMessage));
    console.log("Zoi voice test initiated");
    updateStatus("Speaking", "Zoi is speaking...");

    // Return to wake word mode after a delay if we were in that mode
    if (wasInWakeWordMode) {
      setTimeout(() => {
        deactivateConversationMode();
      }, 10000); // 10 seconds
    }
  } else {
    console.log("WebSocket not connected. Initializing...");
    initializeZoi();
  }
};

// Auto-start Zoi on page load
document.addEventListener('DOMContentLoaded', () => {
  console.log("Zoi interface loaded - auto-initializing...");
  updateStatus("Initializing", "Starting Zoi...");

  // Small delay to ensure DOM is fully ready
  setTimeout(() => {
    initializeZoi();
  }, 500);
});

// First render
renderMessages();
