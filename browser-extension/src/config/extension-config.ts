/**
 * Extension Global Configuration
 * Centralized settings for backend URLs, timeouts, and storage keys.
 */

export const EXTENSION_CONFIG = {
  EXTENSION_NAME: 'Clyde AI Browser Agent',
  VERSION: '1.0.0',
  DEFAULT_WS_URL: 'ws://localhost:8000/api/extension/ws',
  DEFAULT_HTTP_BASE: 'http://localhost:8000/api',
  STORAGE_KEYS: {
    AUTH_TOKEN: 'clyde_ext_auth_token',
    USER_ID: 'clyde_ext_user_id',
    ACTIVE_APPLICATION: 'clyde_ext_active_app',
    SETTINGS: 'clyde_ext_settings',
    TASK_HISTORY: 'clyde_ext_history',
    AUTOMATION_STATE: 'clyde_ext_state'
  },
  RECONNECT: {
    INITIAL_DELAY_MS: 1000,
    MAX_DELAY_MS: 30000,
    JITTER_FACTOR: 0.3,
    MAX_RETRIES: 10
  },
  HEARTBEAT: {
    INTERVAL_MS: 20000,
    TIMEOUT_MS: 8000
  },
  AUTOMATION: {
    TYPING_DELAY_MS: 25,
    DOM_STABILITY_WAIT_MS: 500,
    MAX_STEP_TIMEOUT_MS: 20000,
    REQUIRE_EXPLICIT_APPROVAL: true
  }
} as const;

