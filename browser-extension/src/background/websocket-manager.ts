/**
 * WebSocket Manager for Chrome Extension Manifest V3 Background Service Worker
 * Features:
 * - Exponential backoff reconnection with jitter
 * - Short-lived session token authentication
 * - Heartbeat / Ping-Pong monitoring
 * - Safe lifecycle handling (Manifest V3 idle termination aware)
 */

import { EXTENSION_CONFIG } from '../config/extension-config';
import { EventEnvelope, EventType } from '../shared/types/events';

export type WebSocketMessageHandler = (event: EventEnvelope<any>) => void;
export type ConnectionStatusChangeHandler = (status: 'CONNECTED' | 'DISCONNECTED' | 'RECONNECTING') => void;

export class WebSocketManager {
  private ws: WebSocket | null = null;
  private isConnecting = false;
  private reconnectAttempts = 0;
  private reconnectTimer: any = null;
  private pingIntervalTimer: any = null;
  private messageHandlers: WebSocketMessageHandler[] = [];
  private statusHandlers: ConnectionStatusChangeHandler[] = [];
  private token: string | null = null;
  private clientId: string;

  constructor(clientId?: string) {
    this.clientId = clientId || `ext-client-${Math.random().toString(36).substring(2, 10)}`;
  }

  public onMessage(handler: WebSocketMessageHandler): void {
    this.messageHandlers.push(handler);
  }

  public onStatusChange(handler: ConnectionStatusChangeHandler): void {
    this.statusHandlers.push(handler);
  }

  private notifyStatus(status: 'CONNECTED' | 'DISCONNECTED' | 'RECONNECTING'): void {
    this.statusHandlers.forEach(h => {
      try { h(status); } catch (e) { console.error('Status handler error:', e); }
    });
  }

  public async setAuthToken(token: string): Promise<void> {
    this.token = token;
    if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
      await chrome.storage.local.set({ [EXTENSION_CONFIG.STORAGE_KEYS.AUTH_TOKEN]: token });
    }
  }

  public async connect(): Promise<void> {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    if (this.isConnecting) return;
    this.isConnecting = true;
    this.notifyStatus('RECONNECTING');

    // Retrieve token if not in memory
    if (!this.token && typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
      const data = await chrome.storage.local.get(EXTENSION_CONFIG.STORAGE_KEYS.AUTH_TOKEN);
      this.token = data[EXTENSION_CONFIG.STORAGE_KEYS.AUTH_TOKEN] || null;
    }

    const wsUrl = new URL(EXTENSION_CONFIG.DEFAULT_WS_URL);
    wsUrl.searchParams.set('client_id', this.clientId);
    if (this.token) {
      wsUrl.searchParams.set('token', this.token);
    }

    try {
      this.ws = new WebSocket(wsUrl.toString());

      this.ws.onopen = () => {
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.notifyStatus('CONNECTED');
        this.startHeartbeat();
        console.log(`[Clyde WS] Connected to backend at ${wsUrl.host}`);

        // Dispatch initial handshake
        this.send('EXTENSION_CONNECTED', {
          client_id: this.clientId,
          version: EXTENSION_CONFIG.VERSION,
          user_agent: navigator.userAgent
        });
      };

      this.ws.onmessage = (event: MessageEvent) => {
        try {
          const envelope: EventEnvelope<any> = JSON.parse(event.data);
          this.messageHandlers.forEach(handler => {
            try { handler(envelope); } catch (e) { console.error('Message handler error:', e); }
          });
        } catch (err) {
          console.error('[Clyde WS] Failed to parse incoming WebSocket message:', event.data, err);
        }
      };

      this.ws.onclose = () => {
        this.isConnecting = false;
        this.stopHeartbeat();
        this.notifyStatus('DISCONNECTED');
        console.warn('[Clyde WS] Connection closed. Scheduling reconnection...');
        this.scheduleReconnect();
      };

      this.ws.onerror = (err) => {
        console.error('[Clyde WS] Connection error:', err);
        // onclose will trigger and schedule reconnect
      };
    } catch (err) {
      this.isConnecting = false;
      this.notifyStatus('DISCONNECTED');
      console.error('[Clyde WS] Exception creating WebSocket:', err);
      this.scheduleReconnect();
    }
  }

  public disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close(1000, 'User initiated disconnect');
      this.ws = null;
    }
    this.notifyStatus('DISCONNECTED');
  }

  public send(eventType: EventType, payload: Record<string, unknown>, taskId?: string, workflowId?: string): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn(`[Clyde WS] Cannot send event '${eventType}': WebSocket not connected.`);
      return false;
    }

    const envelope = WebSocketManager.createEnvelope(eventType, payload, taskId, workflowId);

    try {
      this.ws.send(WebSocketManager.serializeEnvelope(envelope));
      return true;
    } catch (err) {
      console.error(`[Clyde WS] Send error for event '${eventType}':`, err);
      return false;
    }
  }

  public static createEnvelope<T = Record<string, unknown>>(
    eventType: EventType,
    payload: T,
    taskId?: string,
    workflowId?: string,
    applicationId?: string
  ): EventEnvelope<T> {
    return {
      event_id: `evt-${Math.random().toString(36).substring(2, 11)}`,
      event_type: eventType,
      workflow_id: workflowId || 'wf-browser-session',
      task_id: taskId || `tsk-${Date.now()}`,
      application_id: applicationId,
      timestamp: new Date().toISOString(),
      payload,
      correlation_id: `corr-${Math.random().toString(36).substring(2, 9)}`
    };
  }

  public static serializeEnvelope<T = Record<string, unknown>>(envelope: EventEnvelope<T>): string {
    return JSON.stringify(envelope);
  }

  public static parseEnvelope<T = Record<string, unknown>>(json: string): EventEnvelope<T> | null {
    try {
      return JSON.parse(json) as EventEnvelope<T>;
    } catch {
      return null;
    }
  }

  public calculateBackoffDelay(attempt: number): number {
    const baseDelay = Math.min(
      EXTENSION_CONFIG.RECONNECT.INITIAL_DELAY_MS * Math.pow(1.8, attempt),
      EXTENSION_CONFIG.RECONNECT.MAX_DELAY_MS
    );
    const jitter = baseDelay * EXTENSION_CONFIG.RECONNECT.JITTER_FACTOR * (Math.random() - 0.5);
    return Math.max(1000, Math.floor(baseDelay + jitter));
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);

    if (this.reconnectAttempts >= EXTENSION_CONFIG.RECONNECT.MAX_RETRIES) {
      console.warn('[Clyde WS] Max reconnection attempts reached. Pausing auto-reconnect.');
      return;
    }

    const delay = this.calculateBackoffDelay(this.reconnectAttempts);
    this.reconnectAttempts++;
    console.log(`[Clyde WS] Reconnecting attempt ${this.reconnectAttempts} in ${delay}ms...`);

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.pingIntervalTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send('HEALTH_CHECK', { ping: Date.now() });
      }
    }, EXTENSION_CONFIG.HEARTBEAT.INTERVAL_MS);
  }

  private stopHeartbeat(): void {
    if (this.pingIntervalTimer) {
      clearInterval(this.pingIntervalTimer);
      this.pingIntervalTimer = null;
    }
  }

  public isConnected(): boolean {
    return Boolean(this.ws && this.ws.readyState === WebSocket.OPEN);
  }
}
