/**
 * Message Router
 * Dispatches backend tasks to the appropriate browser tab and routes execution results back.
 */

import { EventEnvelope } from '../shared/types/events';
import { taskManager } from './task-manager';
import { WebSocketManager } from './websocket-manager';

export class MessageRouter {
  private wsManager: WebSocketManager;

  constructor(wsManager: WebSocketManager) {
    this.wsManager = wsManager;
  }

  public async handleBackendEvent(envelope: EventEnvelope<any>): Promise<void> {
    const { event_type, task_id, workflow_id, payload } = envelope;

    // 1. Deduplication check
    if (task_id && taskManager.isTaskDuplicate(task_id)) {
      console.warn(`[MessageRouter] Ignoring duplicate task '${task_id}'`);
      return;
    }

    // 2. Identify target browser tab
    const targetUrl = payload?.target_url || payload?.job_url;
    const tabs = await this.queryTargetTabs(targetUrl);
    if (!tabs || tabs.length === 0 || !tabs[0].id) {
      this.wsManager.send('APPLICATION_FAILED', {
        error_code: 'SITE_UNSUPPORTED',
        message: 'No active job portal tab found matching target URL.',
        task_id,
        workflow_id
      }, task_id, workflow_id);
      return;
    }

    const targetTabId = tabs[0].id;

    // 3. Dispatch specific command to content script
    switch (event_type) {
      case 'PREPARE_APPLICATION':
        taskManager.startTask(task_id, workflow_id, 'Preparing candidate profile for application...', { url: tabs[0].url });
        this.wsManager.send('APPLICATION_READY', { application_id: payload?.application_id, status: 'READY_FOR_REVIEW' }, task_id, workflow_id);
        break;

      case 'INSPECT_PAGE':
        taskManager.startTask(task_id, workflow_id, 'Inspecting job application page...', { url: tabs[0].url });
        try {
          const response = await this.sendTabMessageWithRetry(targetTabId, { type: 'CMD_INSPECT_PAGE', payload });
          this.wsManager.send('PAGE_INSPECTED', response, task_id, workflow_id);
        } catch (err: any) {
          this.wsManager.send('APPLICATION_FAILED', {
            error_code: 'FORM_NOT_FOUND',
            message: err?.message || 'Content script failed to respond.',
            task_id
          }, task_id, workflow_id);
        }
        break;

      case 'FILL_FORM':
        taskManager.startTask(task_id, workflow_id, 'Mapping and autofilling candidate details...', { url: tabs[0].url });
        taskManager.updateTaskProgress('PREPARING', 40, 'Mapping and autofilling candidate details...');
        try {
          const response = await this.sendTabMessageWithRetry(targetTabId, { type: 'CMD_FILL_FORM', payload });
          taskManager.updateTaskProgress('READY_FOR_REVIEW', 85, 'Form populated. Application preview ready for review.');
          this.wsManager.send('FORM_FILLED', response, task_id, workflow_id);
          this.wsManager.send('APPLICATION_READY', {
            application_id: payload?.application_id || 'app-ready',
            status: 'READY_FOR_REVIEW',
            preview: response?.preview
          }, task_id, workflow_id);
        } catch (err: any) {
          taskManager.failTask(task_id, {
            workflow_id: workflow_id || 'wf-default',
            task_id,
            error_code: 'FIELD_MAPPING_FAILED',
            message: err?.message || 'Form autofill failed.',
            timestamp: new Date().toISOString(),
            recoverable: false
          });
          this.wsManager.send('APPLICATION_FAILED', {
            error_code: 'FIELD_MAPPING_FAILED',
            message: err?.message || 'Form autofill failed.',
            task_id
          }, task_id, workflow_id);
        }
        break;

      case 'UPLOAD_RESUME':
        taskManager.updateTaskProgress('PREPARING', 65, 'Attaching verified ATS resume PDF...');
        try {
          const response = await this.sendTabMessageWithRetry(targetTabId, { type: 'CMD_UPLOAD_RESUME', payload });
          this.wsManager.send('RESUME_UPLOADED', response, task_id, workflow_id);
        } catch (err: any) {
          this.wsManager.send('APPLICATION_FAILED', {
            error_code: 'RESUME_UPLOAD_FAILED',
            message: err?.message || 'Resume upload failed.',
            task_id
          }, task_id, workflow_id);
        }
        break;

      case 'UPLOAD_COVER_LETTER':
        taskManager.updateTaskProgress('PREPARING', 80, 'Populating tailored cover letter...');
        try {
          const response = await this.sendTabMessageWithRetry(targetTabId, { type: 'CMD_UPLOAD_COVER_LETTER', payload });
          this.wsManager.send('COVER_LETTER_UPLOADED', response, task_id, workflow_id);
        } catch (err: any) {
          this.wsManager.send('APPLICATION_FAILED', {
            error_code: 'COVER_LETTER_UPLOAD_FAILED',
            message: err?.message || 'Cover letter upload failed.',
            task_id
          }, task_id, workflow_id);
        }
        break;

      case 'SUBMIT_APPLICATION':
        // CRITICAL SECURITY: Verify explicit user approval token
        const appId = payload?.application_id || 'app-default';
        const approval = taskManager.verifyApproval(appId);
        if (!approval) {
          console.error(`[Security Check Failed] Submission rejected: No valid user approval found for app ${appId}`);
          this.wsManager.send('APPROVAL_REQUIRED', {
            application_id: appId,
            message: 'Application requires explicit user confirmation before final submission.'
          }, task_id, workflow_id);
          return;
        }

        taskManager.updateTaskProgress('SUBMITTING', 90, 'Submitting approved application...');
        try {
          const response = await this.sendTabMessageWithRetry(targetTabId, { type: 'CMD_SUBMIT_APPLICATION', payload, approval });
          if (!response || response.status === 'FAILED') {
            this.wsManager.send('APPLICATION_FAILED', {
              error_code: 'SUBMISSION_FAILED',
              message: response?.error_reason || 'Submission failed.',
              task_id
            }, task_id, workflow_id);
          } else {
            taskManager.completeTask(task_id);
            this.wsManager.send('APPLICATION_COMPLETED', response, task_id, workflow_id);
          }
        } catch (err: any) {
          this.wsManager.send('APPLICATION_FAILED', {
            error_code: 'SUBMISSION_FAILED',
            message: err?.message || 'Submission failed.',
            task_id
          }, task_id, workflow_id);
        }
        break;

      case 'CANCEL_TASK':
        taskManager.clearActiveTask();
        chrome.tabs.sendMessage(targetTabId, { type: 'CMD_CANCEL_TASK' });
        this.wsManager.send('TASK_CANCELLED', { task_id }, task_id, workflow_id);
        break;

      default:
        console.warn(`[MessageRouter] Unhandled backend event type: ${event_type}`);
    }
  }

  private async sendTabMessageWithRetry(tabId: number, message: any, maxRetries = 6, delayMs = 400): Promise<any> {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        await this.ensureContentScriptInjected(tabId);
        const res = await new Promise((resolve, reject) => {
          chrome.tabs.sendMessage(tabId, message, (resp) => {
            if (chrome.runtime.lastError) {
              reject(new Error(chrome.runtime.lastError.message));
            } else {
              resolve(resp);
            }
          });
        });
        return res;
      } catch (err: any) {
        if (attempt === maxRetries) {
          throw err;
        }
        await new Promise(r => setTimeout(r, delayMs));
      }
    }
  }

  private async queryTargetTabs(targetUrl?: string): Promise<chrome.tabs.Tab[]> {
    if (typeof chrome === 'undefined' || !chrome.tabs) return [];

    const allTabs = await chrome.tabs.query({});

    if (targetUrl) {
      // 1. Exact or partial URL match across all open tabs
      const matched = allTabs.filter(t => t.url && (t.url === targetUrl || t.url.includes(targetUrl)));
      if (matched.length > 0) {
        chrome.tabs.update(matched[0].id!, { active: true });
        return matched;
      }

      // 2. Hostname/domain match
      try {
        const parsed = new URL(targetUrl);
        const hostMatched = allTabs.filter(t => t.url && t.url.includes(parsed.host));
        if (hostMatched.length > 0) {
          chrome.tabs.update(hostMatched[0].id!, { active: true });
          return hostMatched;
        }
      } catch {}

      // 3. Not found: Open target tab automatically in active window
      try {
        const newTab = await chrome.tabs.create({ url: targetUrl, active: true });
        await new Promise<void>((resolve) => {
          let resolved = false;
          const done = () => {
            if (!resolved) {
              resolved = true;
              chrome.tabs.onUpdated.removeListener(listener);
              resolve();
            }
          };
          const listener = (tabId: number, changeInfo: chrome.tabs.TabChangeInfo) => {
            if (tabId === newTab.id && changeInfo.status === 'complete') {
              done();
            }
          };
          chrome.tabs.onUpdated.addListener(listener);
          setTimeout(done, 3000);
        });
        return [newTab];
      } catch {}
    }

    // Fall back to active non-chrome tab
    const nonRestricted = allTabs.filter(t => t.url && !t.url.startsWith('chrome://') && !t.url.startsWith('chrome-extension://'));
    if (nonRestricted.length > 0) {
      const active = nonRestricted.find(t => t.active);
      return active ? [active] : [nonRestricted[0]];
    }

    return await chrome.tabs.query({ active: true, currentWindow: true });
  }

  private async ensureContentScriptInjected(tabId: number): Promise<void> {
    if (typeof chrome === 'undefined' || !chrome.scripting) return;
    try {
      const tab = await chrome.tabs.get(tabId);
      if (!tab.url || tab.url.startsWith('chrome://') || tab.url.startsWith('chrome-extension://')) {
        return;
      }
      await chrome.scripting.executeScript({
        target: { tabId },
        files: ['content.js']
      });
      await new Promise(r => setTimeout(r, 150));
    } catch {
      // Content script may already be injected or page is restricted
    }
  }
}

