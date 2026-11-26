/**
 * Platform Detector
 * Identifies supported job application platforms, ATS systems, and job boards.
 * Evaluates both URL patterns and DOM structural fingerprints.
 */

import { PlatformCategory } from '../../shared/types/adapter';

export interface PlatformDetectionRule {
  name: string;
  category: PlatformCategory;
  urlPatterns: RegExp[];
  domFingerprints?: Array<(doc: Document) => boolean>;
  isApplicationPage: (url: string, doc: Document) => boolean;
}

export class PlatformDetector {
  private static rules: PlatformDetectionRule[] = [
    {
      name: 'Greenhouse ATS',
      category: 'COMPANY_CAREERS',
      urlPatterns: [
        /boards\.greenhouse\.io/i,
        /job-boards\.greenhouse\.io/i,
        /gh_jid=/i
      ],
      domFingerprints: [
        (doc) => Boolean(doc.querySelector('form#application_form, div#application, div#app_body[data-controller*="greenhouse"]'))
      ],
      isApplicationPage: (url, doc) => {
        return /jobs\/|#app|gh_jid=/i.test(url) || Boolean(doc.querySelector('form#application_form, #application'));
      }
    },
    {
      name: 'Lever ATS',
      category: 'COMPANY_CAREERS',
      urlPatterns: [
        /jobs\.lever\.co/i
      ],
      domFingerprints: [
        (doc) => Boolean(doc.querySelector('.application-form, .postings-btn-wrapper, .lever-job-title'))
      ],
      isApplicationPage: (url, doc) => {
        return /\/apply\b/i.test(url) || Boolean(doc.querySelector('form.application-form, #application-form'));
      }
    },
    {
      name: 'Workday ATS',
      category: 'COMPANY_CAREERS',
      urlPatterns: [
        /myworkdayjobs\.com/i,
        /wd\d+\.myworkday\.com/i
      ],
      domFingerprints: [
        (doc) => Boolean(doc.querySelector('[data-automation-id*="workday"], [id*="workdayApplication"], div[data-automation-id="jobPostingPage"]'))
      ],
      isApplicationPage: (url, doc) => {
        return /\/apply\b|\/job\//i.test(url) || Boolean(doc.querySelector('[data-automation-id="applyButton"], form[data-automation-id*="apply"]'));
      }
    },
    {
      name: 'LinkedIn Jobs',
      category: 'JOB_BOARD',
      urlPatterns: [
        /linkedin\.com\/jobs/i
      ],
      domFingerprints: [
        (doc) => Boolean(doc.querySelector('.jobs-apply-button, .jobs-easy-apply-modal, [data-job-id]'))
      ],
      isApplicationPage: (url, doc) => {
        return /\/view\/|\/collections\/|currentJobId=/i.test(url) || Boolean(doc.querySelector('.jobs-easy-apply-content, .jobs-apply-button'));
      }
    },
    {
      name: 'SimplifyJobs Platform',
      category: 'INTERNSHIP_PLATFORM',
      urlPatterns: [
        /simplify\.jobs/i
      ],
      domFingerprints: [
        (doc) => Boolean(doc.querySelector('[data-simplify-application], .simplify-job-card, #simplify-apply'))
      ],
      isApplicationPage: (url, doc) => {
        return /\/jobs\/|\/applications\//i.test(url) || Boolean(doc.querySelector('[data-simplify-application]'));
      }
    }
  ];

  public static registerRule(rule: PlatformDetectionRule): void {
    this.rules.unshift(rule);
  }

  public static detect(url: string, doc: Document): {
    name: string;
    category: PlatformCategory;
    isSupported: boolean;
    isApplicationPage: boolean;
  } {
    for (const rule of this.rules) {
      const urlMatch = rule.urlPatterns.some(pattern => pattern.test(url));
      const domMatch = rule.domFingerprints ? rule.domFingerprints.some(fn => {
        try { return fn(doc); } catch { return false; }
      }) : false;

      if (urlMatch || domMatch) {
        let isApp = false;
        try {
          isApp = rule.isApplicationPage(url, doc);
        } catch {
          isApp = false;
        }

        return {
          name: rule.name,
          category: rule.category,
          isSupported: true,
          isApplicationPage: isApp
        };
      }
    }

    // Generic form fallback check
    const hasApplicationForm = Boolean(
      doc.querySelector('form[action*="apply"], form[id*="job"], form[class*="application"], form[class*="apply"]')
    );

    return {
      name: hasApplicationForm ? 'Generic Job Application' : 'Standard Webpage',
      category: 'GENERIC',
      isSupported: hasApplicationForm,
      isApplicationPage: hasApplicationForm
    };
  }
}

