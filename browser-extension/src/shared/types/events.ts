/**
 * Standardized Event Protocol Definitions
 * Strongly typed events exchanged between Backend Agent and Chrome Browser Extension.
 */

export type BackendToExtensionEventType =
  | 'FIND_JOB'
  | 'PREPARE_APPLICATION'
  | 'INSPECT_PAGE'
  | 'FILL_FORM'
  | 'UPLOAD_RESUME'
  | 'UPLOAD_COVER_LETTER'
  | 'SUBMIT_APPLICATION'
  | 'CANCEL_TASK'
  | 'HEALTH_CHECK';

export type ExtensionToBackendEventType =
  | 'EXTENSION_CONNECTED'
  | 'EXTENSION_DISCONNECTED'
  | 'PAGE_DETECTED'
  | 'PAGE_INSPECTED'
  | 'FORM_MAPPED'
  | 'FORM_FILLED'
  | 'RESUME_UPLOADED'
  | 'COVER_LETTER_UPLOADED'
  | 'APPLICATION_READY'
  | 'APPROVAL_REQUIRED'
  | 'APPLICATION_COMPLETED'
  | 'APPLICATION_FAILED'
  | 'USER_ACTION_REQUIRED'
  | 'TASK_CANCELLED'
  | 'HEALTH_CHECK_ACK';

export type EventType = BackendToExtensionEventType | ExtensionToBackendEventType;

export interface EventEnvelope<T = Record<string, unknown>> {
  event_id: string;
  event_type: EventType;
  workflow_id: string;
  task_id: string;
  application_id?: string;
  timestamp: string;
  payload: T;
  correlation_id?: string;
}

export type ApplicationStatus =
  | 'PREPARING'
  | 'READY_FOR_REVIEW'
  | 'AWAITING_APPROVAL'
  | 'SUBMITTING'
  | 'APPLIED'
  | 'FAILED'
  | 'NEEDS_USER_ACTION'
  | 'UNSUPPORTED';

export type AutomationErrorCode =
  | 'SITE_UNSUPPORTED'
  | 'FORM_NOT_FOUND'
  | 'FIELD_MAPPING_FAILED'
  | 'FIELD_VALIDATION_FAILED'
  | 'RESUME_UPLOAD_FAILED'
  | 'COVER_LETTER_UPLOAD_FAILED'
  | 'APPROVAL_NOT_FOUND'
  | 'APPROVAL_EXPIRED'
  | 'APPROVAL_MISMATCH'
  | 'SUBMISSION_FAILED'
  | 'WEBSOCKET_DISCONNECTED'
  | 'TASK_TIMEOUT'
  | 'USER_ACTION_REQUIRED';

export interface StructuredError {
  error_code: AutomationErrorCode;
  message: string;
  workflow_id: string;
  task_id: string;
  timestamp: string;
  recoverable: boolean;
  suggested_action?: string;
  details?: Record<string, unknown>;
}

