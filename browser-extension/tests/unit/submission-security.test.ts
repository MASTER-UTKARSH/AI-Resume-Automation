import { describe, it, expect, beforeEach } from 'vitest';
import { SubmissionEngine } from '../../src/automation/submission-engine';
import { SubmissionApproval, ValidationResult } from '../../src/shared/types/adapter';

describe('SubmissionEngine Security Verification', () => {
  let doc: Document;

  beforeEach(() => {
    doc = document.implementation.createHTMLDocument('Job Application');
    doc.body.innerHTML = `
      <form id="job-form">
        <label for="name">Name</label>
        <input type="text" id="name" name="name" value="Utkarsh Shah" />
        <label for="email">Email</label>
        <input type="email" id="email" name="email" value="utkarsh@example.com" />
        <button type="submit" id="submit-btn">Submit Application</button>
      </form>
    `;
  });

  it('rejects submission when explicit user approval is missing (AWAITING_APPROVAL)', async () => {
    const unapproved: SubmissionApproval = {
      application_id: 'app-100',
      workflow_id: 'wf-1',
      approved_by_user: false,
      approval_token: '',
      timestamp: new Date().toISOString()
    };

    const result = await SubmissionEngine.executeSubmission(doc, unapproved, 'app-100');
    expect(result.status).toBe('AWAITING_APPROVAL');
    expect(result.error_reason).toContain('Explicit user approval was not granted');
  });

  it('rejects submission when approval application_id does not match active job (FAILED)', async () => {
    const mismatchedApproval: SubmissionApproval = {
      application_id: 'app-DIFFERENT-ID',
      workflow_id: 'wf-1',
      approved_by_user: true,
      approval_token: 'auth-token-valid',
      timestamp: new Date().toISOString()
    };

    const result = await SubmissionEngine.executeSubmission(doc, mismatchedApproval, 'app-100');
    expect(result.status).toBe('FAILED');
    expect(result.error_reason).toContain('Security mismatch');
  });

  it('detects CAPTCHA or Cloudflare challenges and halts submission (NEEDS_USER_ACTION)', async () => {
    // Inject Turnstile iframe into DOM
    const captchaDiv = doc.createElement('div');
    captchaDiv.className = 'cf-turnstile';
    const iframe = doc.createElement('iframe');
    iframe.src = 'https://challenges.cloudflare.com/cdn-cgi/challenge-platform/h/b/turnstile/if/ov2';
    captchaDiv.appendChild(iframe);
    doc.body.appendChild(captchaDiv);

    const validApproval: SubmissionApproval = {
      application_id: 'app-100',
      workflow_id: 'wf-1',
      approved_by_user: true,
      approval_token: 'valid-token',
      timestamp: new Date().toISOString()
    };

    const result = await SubmissionEngine.executeSubmission(doc, validApproval, 'app-100');
    expect(result.status).toBe('NEEDS_USER_ACTION');
    expect(result.error_reason).toContain('Human verification required');
  });

  it('generates a complete application preview for human-in-the-loop inspection', () => {
    const mockValidation: ValidationResult = {
      is_valid: true,
      unfilled_required_fields: [],
      warnings: ['Phone number was optional but left blank']
    };

    const preview = SubmissionEngine.generatePreview(
      'app-100',
      'Google',
      'Software Engineer',
      'https://careers.google.com/jobs/100',
      doc,
      'Utkarsh_Shah_Resume.pdf',
      mockValidation
    );

    expect(preview.application_id).toBe('app-100');
    expect(preview.company_name).toBe('Google');
    expect(preview.resume_attached).toBe('Utkarsh_Shah_Resume.pdf');
    expect(preview.requires_user_approval).toBe(true);
    expect(preview.fields_populated.length).toBeGreaterThanOrEqual(2);
    expect(preview.warnings).toContain('Phone number was optional but left blank');
  });
});
