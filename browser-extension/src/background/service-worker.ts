/**
 * Clyde AI Browser Agent - Background Service Worker (Manifest V3)
 * Handles background lifecycle, WebSocket communication with the backend,
 * and command routing to content scripts.
 */

import { WebSocketManager } from './websocket-manager';
import { MessageRouter } from './message-router';
import { taskManager } from './task-manager';
import { EXTENSION_CONFIG } from '../config/extension-config';

console.log('[Clyde Service Worker] Initializing Manifest V3 execution layer...');

const wsManager = new WebSocketManager();
const messageRouter = new MessageRouter(wsManager);

// Forward incoming backend WebSocket instructions to MessageRouter
wsManager.onMessage((envelope) => {
  messageRouter.handleBackendEvent(envelope);
});

// Broadcast connection status to popup
wsManager.onStatusChange((status) => {
  chrome.runtime.sendMessage({ type: 'WS_STATUS_UPDATE', status }).catch(() => {
    // Popup might not be open, which is normal
  });
});

// Auto-connect on service worker startup
async function initSession() {
  try {
    // Attempt to fetch short-lived extension token from local backend if needed
    const res = await fetch(`${EXTENSION_CONFIG.DEFAULT_HTTP_BASE}/extension/token`);
    if (res.ok) {
      const data = await res.json();
      if (data.access_token) {
        await wsManager.setAuthToken(data.access_token);
        console.log('[Clyde Service Worker] Authenticated session token obtained.');
      }
    }
  } catch (err) {
    console.warn('[Clyde Service Worker] Local backend token lookup skipped (backend offline or remote):', err);
  }

  // Connect WebSocket
  wsManager.connect();
}

initSession();

// Listen for messages from Popup UI or Content Scripts
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  const { type, payload } = message;

  switch (type) {
    case 'GET_STATUS':
      sendResponse({
        isConnected: wsManager.isConnected(),
        activeTask: taskManager.getActiveTask(),
        version: EXTENSION_CONFIG.VERSION
      });
      break;

    case 'CONNECT_WS':
      wsManager.connect();
      sendResponse({ success: true });
      break;

    case 'DISCONNECT_WS':
      wsManager.disconnect();
      sendResponse({ success: true });
      break;

    case 'APPROVE_SUBMISSION':
      if (payload?.application_id && payload?.approval_token) {
        taskManager.recordApproval(payload.application_id, payload.approval_token);
        console.log(`[Clyde Service Worker] User approved submission for application ${payload.application_id}`);

        // Notify content script to execute submission
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
          if (tabs && tabs[0]?.id) {
            chrome.tabs.sendMessage(tabs[0].id, {
              type: 'CMD_SUBMIT_APPLICATION',
              approval: taskManager.verifyApproval(payload.application_id)
            });
          }
        });
        sendResponse({ success: true });
      }
      break;

    case 'CANCEL_CURRENT_TASK':
      taskManager.clearActiveTask();
      sendResponse({ success: true });
      break;

    case 'CONTENT_LOG':
      chrome.runtime.sendMessage({
        type: 'LOG_EVENT',
        message: payload?.message,
        level: payload?.level || 'info'
      }).catch(() => {});
      break;

    default:
      break;
  }

  return true; // Keep async response channel open
});

// Tab lifecycle management: clear task state if active tab is closed
chrome.tabs.onRemoved.addListener((tabId) => {
  const active = taskManager.getActiveTask();
  if (active) {
    console.log(`[Clyde Service Worker] Tab ${tabId} closed while task ${active.task_id} was active.`);
  }
});
