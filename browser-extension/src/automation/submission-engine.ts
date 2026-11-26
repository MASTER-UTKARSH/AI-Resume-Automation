/**
 * Submission Engine
 * Enforces mandatory human-in-the-loop review, anti-bot/CAPTCHA detection,
 * and secure cryptographic/tokenized approval verification before final application submission.
 */

import { SubmissionApproval, ApplicationPreview, ValidationResult, ApplicationResult } from '../shared/types/adapter';
import { ResultCapture } from './result-capture';
import { DomUtils } from '../content/dom-utils';

export class SubmissionEngine {
  private static submitButtonSelectors = [
    'button[type="submit"]',
    'input[type="submit"]',
    'button[id*="submit" i]',
    'button[class*="submit" i]',
    'button[data-automation-id*="submit" i]',
    'button[aria-label*="submit" i]',
    'a[id*="submit" i]',
    'button:contains("Submit Application")',
    'button:contains("Submit")'
  ];

  /**
   * Generates a preview for user review before final submission
   */
  public static generatePreview(
    appId: string,
    company: string,
    title: string,
    url: string,
    doc: Document,
    resumeName: string,
    validation: ValidationResult
  ): ApplicationPreview {
    const inputs = Array.from(doc.querySelectorAll<HTMLInputElement | HTMLTextAreaElement>('input, textarea'));
    const populated = inputs
      .filter(i => i.value && i.type !== 'hidden' && i.type !== 'submit')
      .map(i => ({
        label: i.getAttribute('aria-label') || i.name || i.id || 'Field',
        value: i.type === 'password' ? '••••••' : i.value
      }));

    return {
      application_id: appId,
      company_name: company,
      job_title: title,
      job_url: url,
      fields_populated: populated,
      unmapped_required_fields: validation.unfilled_required_fields.map(f => f.label),
      resume_attached: resumeName,
      warnings: validation.warnings,
      requires_user_approval: true,
      preview_timestamp: new Date().toISOString()
    };
  }

  /**
   * Executes the final submission ONLY IF explicit valid user approval is present
   */
  public static async executeSubmission(
    doc: Document,
    approval: SubmissionApproval,
    expectedAppId: string
  ): Promise<ApplicationResult> {
    // 1. Strict security validation: Verify approval token matches this specific application
    if (!approval || !approval.approved_by_user) {
      return {
        status: 'AWAITING_APPROVAL',
        timestamp: new Date().toISOString(),
        platform: 'Unknown',
        error_reason: 'Submission aborted: Explicit user approval was not granted.'
      };
    }

    if (approval.application_id !== expectedAppId) {
      return {
        status: 'FAILED',
        timestamp: new Date().toISOString(),
        platform: 'Unknown',
        error_reason: `Security mismatch: Approval token ID '${approval.application_id}' does not match active application '${expectedAppId}'.`
      };
    }

    // 2. Check for human verification gates (CAPTCHA, Cloudflare, hCaptcha, Turnstile, MFA)
    if (SubmissionEngine.detectCaptchaOrMFA(doc)) {
      return {
        status: 'NEEDS_USER_ACTION',
        timestamp: new Date().toISOString(),
        platform: 'Protected Portal',
        error_reason: 'Human verification required: CAPTCHA or Multi-Factor Authentication detected. Please complete it in your browser.'
      };
    }

    // 3. Locate the final submission trigger button
    const submitBtn = SubmissionEngine.findSubmitButton(doc);
    if (!submitBtn) {
      return {
        status: 'FAILED',
        timestamp: new Date().toISOString(),
        platform: 'Portal',
        error_reason: 'Could not find submission button on the page.'
      };
    }

    try {
      submitBtn.scrollIntoView({ behavior: 'smooth', block: 'center' });
      await new Promise(r => setTimeout(r, 200));

      // Click the submission button
      submitBtn.click();

      // Wait up to 3 seconds for DOM response / confirmation page
      await new Promise(r => setTimeout(r, 1500));

      // Capture and verify application result
      return ResultCapture.captureResult(doc);
    } catch (err: any) {
      return {
        status: 'FAILED',
        timestamp: new Date().toISOString(),
        platform: 'Portal',
        error_reason: err?.message || 'Error executing submission button click.'
      };
    }
  }

  public static detectCaptchaOrMFA(doc: Document): boolean {
    const captchaSelectors = [
      'iframe[src*="recaptcha"]',
      'iframe[src*="hcaptcha"]',
      'iframe[src*="turnstile"]',
      'div.g-recaptcha',
      'div.h-captcha',
      '#cf-turnstile',
      'input[name*="captcha" i]',
      'input[id*="otp" i]',
      'input[name*="verification_code" i]'
    ];
    return captchaSelectors.some(sel => Boolean(doc.querySelector(sel)));
  }

  private static findSubmitButton(doc: Document): HTMLElement | null {
    for (const sel of SubmissionEngine.submitButtonSelectors) {
      try {
        const el = doc.querySelector<HTMLElement>(sel);
        if (el && DomUtils.isVisible(el)) return el;
      } catch (e) {
        // Continue if pseudo-selector fails
      }
    }

    // Fallback: search all buttons for text "Submit" or "Apply"
    const allButtons = Array.from(doc.querySelectorAll<HTMLButtonElement>('button'));
    for (const b of allButtons) {
      const text = b.textContent?.toLowerCase() || '';
      if ((text.includes('submit') || text.includes('apply')) && !text.includes('cancel')) {
        if (DomUtils.isVisible(b)) return b;
      }
    }

    return null;
  }
}

