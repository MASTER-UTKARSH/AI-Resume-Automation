/**
 * Result Capture Engine
 * Analyzes multiple verification signals (DOM confirmation messages, URL redirects, form disappearance)
 * to confirm whether a job application was actually submitted.
 */

import { ApplicationResult } from '../shared/types/adapter';

export class ResultCapture {
  private static successPatterns = [
    /thank\s+you\s+for\s+applying/i,
    /application\s+(has\s+been\s+)?submitted/i,
    /application\s+received/i,
    /we('ve|\s+have)\s+received\s+your\s+application/i,
    /your\s+application\s+was\s+sent/i,
    /successfully\s+applied/i,
    /congratulations.*application/i
  ];

  private static failurePatterns = [
    /there\s+was\s+an\s+error/i,
    /please\s+fix\s+the\s+following\s+errors/i,
    /submission\s+failed/i,
    /required\s+fields?\s+missing/i
  ];

  public static captureResult(doc: Document): ApplicationResult {
    const pageText = doc.body?.innerText || '';
    const currentUrl = window.location.href;

    // 1. Check for explicit success confirmation text in DOM
    for (const pattern of ResultCapture.successPatterns) {
      if (pattern.test(pageText)) {
        return {
          status: 'APPLIED',
          confirmation_message: 'Application submitted and confirmed by destination portal.',
          confirmation_url: currentUrl,
          timestamp: new Date().toISOString(),
          platform: 'Career Portal'
        };
      }
    }

    // 2. Check for URL redirect signals (e.g. /thank_you, /confirmation, /applied)
    if (/\/thank[-_]?you|\/confirmation|\/submitted|\/applied\b/i.test(currentUrl)) {
      return {
        status: 'APPLIED',
        confirmation_message: 'Redirected to confirmation page.',
        confirmation_url: currentUrl,
        timestamp: new Date().toISOString(),
        platform: 'Career Portal'
      };
    }

    // 3. Check for validation or submission error banners
    for (const pattern of ResultCapture.failurePatterns) {
      if (pattern.test(pageText)) {
        return {
          status: 'FAILED',
          timestamp: new Date().toISOString(),
          platform: 'Career Portal',
          error_reason: 'Form reported validation errors upon submission.'
        };
      }
    }

    // 4. Form disappearance check (if form is replaced with confirmation container)
    const forms = doc.querySelectorAll('form');
    if (forms.length === 0 && pageText.length > 50) {
      return {
        status: 'APPLIED',
        confirmation_message: 'Application form unmounted successfully.',
        confirmation_url: currentUrl,
        timestamp: new Date().toISOString(),
        platform: 'Career Portal'
      };
    }

    // Default: Return preparing/submitted if no explicit failure
    return {
      status: 'SUBMITTING',
      timestamp: new Date().toISOString(),
      platform: 'Career Portal',
      confirmation_url: currentUrl,
      confirmation_message: 'Submission executed. Awaiting server confirmation.'
    };
  }
}
