import { describe, it, expect } from 'vitest';
import { WebSocketManager } from '../../src/background/websocket-manager';
import { EXTENSION_CONFIG } from '../../src/config/extension-config';
import { EventType } from '../../src/shared/types/events';

describe('WebSocketProtocol and Manager', () => {
  it('constructs well-formed event envelopes with strict schema headers', () => {
    const envelope = WebSocketManager.createEnvelope('EXTENSION_CONNECTED' as EventType, {
      session_id: 'sess-123',
      platform: 'Linux'
    });

    expect(envelope.event_type).toBe('EXTENSION_CONNECTED');
    expect(envelope.workflow_id).toBeDefined();
    expect(envelope.task_id).toMatch(/^tsk-/);
    expect(new Date(envelope.timestamp).getTime()).toBeGreaterThan(0);
    expect(envelope.payload).toEqual({
      session_id: 'sess-123',
      platform: 'Linux'
    });
  });

  it('serializes envelope to valid JSON string', () => {
    const envelope = WebSocketManager.createEnvelope('FORM_FILLED' as EventType, {
      task_id: 'task-789',
      status: 'SUCCESS'
    });

    const serialized = WebSocketManager.serializeEnvelope(envelope);
    expect(typeof serialized).toBe('string');

    const parsed = WebSocketManager.parseEnvelope(serialized);
    expect(parsed?.event_type).toBe('FORM_FILLED');
    expect(parsed?.payload).toEqual({
      task_id: 'task-789',
      status: 'SUCCESS'
    });
  });

  it('computes exponential backoff with jitter bounded by min and max intervals', () => {
    const wsManager = new WebSocketManager();

    for (let attempt = 1; attempt <= 10; attempt++) {
      const delay = wsManager.calculateBackoffDelay(attempt);
      expect(delay).toBeGreaterThanOrEqual(EXTENSION_CONFIG.RECONNECT.INITIAL_DELAY_MS);
      expect(delay).toBeLessThanOrEqual(EXTENSION_CONFIG.RECONNECT.MAX_DELAY_MS * 1.5);
    }
  });

  it('correctly handles parsing invalid json string gracefully', () => {
    const invalidJson = '{ not valid json ::: }';
    const parsed = WebSocketManager.parseEnvelope(invalidJson);
    expect(parsed).toBeNull();
  });
});
