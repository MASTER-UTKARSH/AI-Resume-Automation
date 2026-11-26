/**
 * Page Inspector
 * Analyzes webpage structure, verifies application form status, and checks security gates.
 */

import { PageInspectionResult } from '../shared/types/adapter';
import { PlatformRegistry } from '../platforms/core/PlatformRegistry';
import { SubmissionEngine } from '../automation/submission-engine';

export class PageInspector {
  public static async inspect(doc: Document): Promise<PageInspectionResult> {
    const url = window.location.href;
    const adapter = PlatformRegistry.getAdapterForPage(url, doc);
    const result = await adapter.inspectPage(doc);

    // Security Gate check (CAPTCHA / MFA / Cloudflare Turnstile)
    const hasCaptcha = SubmissionEngine.detectCaptchaOrMFA(doc);
    result.has_captcha = hasCaptcha;

    return result;
  }
}

