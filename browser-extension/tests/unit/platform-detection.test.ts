import { describe, it, expect, beforeEach } from 'vitest';
import { PlatformDetector } from '../../src/platforms/core/PlatformDetector';

describe('PlatformDetector', () => {
  let doc: Document;

  beforeEach(() => {
    doc = document.implementation.createHTMLDocument('Test Document');
  });

  it('detects Greenhouse ATS from URL', () => {
    const result = PlatformDetector.detect('https://boards.greenhouse.io/stripe/jobs/1234567', doc);
    expect(result.name).toBe('Greenhouse ATS');
    expect(result.category).toBe('COMPANY_CAREERS');
    expect(result.isSupported).toBe(true);
    expect(result.isApplicationPage).toBe(true);
  });

  it('detects Lever ATS from URL', () => {
    const result = PlatformDetector.detect('https://jobs.lever.co/netflix/987-abc-xyz/apply', doc);
    expect(result.name).toBe('Lever ATS');
    expect(result.category).toBe('COMPANY_CAREERS');
    expect(result.isSupported).toBe(true);
    expect(result.isApplicationPage).toBe(true);
  });

  it('detects Workday ATS from URL', () => {
    const result = PlatformDetector.detect('https://marsh.wd3.myworkdayjobs.com/en-US/Careers/job/Mumbai/Software-Engineer_R123', doc);
    expect(result.name).toBe('Workday ATS');
    expect(result.category).toBe('COMPANY_CAREERS');
    expect(result.isSupported).toBe(true);
    expect(result.isApplicationPage).toBe(true);
  });

  it('detects LinkedIn Jobs from URL', () => {
    const result = PlatformDetector.detect('https://www.linkedin.com/jobs/view/4123456789/', doc);
    expect(result.name).toBe('LinkedIn Jobs');
    expect(result.category).toBe('JOB_BOARD');
    expect(result.isSupported).toBe(true);
    expect(result.isApplicationPage).toBe(true);
  });

  it('detects SimplifyJobs Platform from URL', () => {
    const result = PlatformDetector.detect('https://simplify.jobs/jobs/software-engineering-intern/apply', doc);
    expect(result.name).toBe('SimplifyJobs Platform');
    expect(result.category).toBe('INTERNSHIP_PLATFORM');
    expect(result.isSupported).toBe(true);
    expect(result.isApplicationPage).toBe(true);
  });

  it('falls back gracefully on unsupported or custom URLs', () => {
    const result = PlatformDetector.detect('https://careers.somecompany.io/roles/senior-dev', doc);
    expect(result.category).toBe('GENERIC');
    expect(result.isSupported).toBe(false);
    expect(['Standard Webpage', 'Generic Job Application']).toContain(result.name);
  });

  it('detects platform via DOM structural fingerprint when URL is masked', () => {
    const form = doc.createElement('form');
    form.id = 'application_form';
    doc.body.appendChild(form);

    const result = PlatformDetector.detect('https://custom-domain.careerportal.com/apply', doc);
    expect(result.name).toBe('Greenhouse ATS');
    expect(result.isSupported).toBe(true);
  });

  it('allows registering custom platform detection rules dynamically', () => {
    PlatformDetector.registerRule({
      name: 'Custom Startup Portal',
      category: 'COMPANY_CAREERS',
      urlPatterns: [/customstartup\.com\/jobs/i],
      isApplicationPage: (url) => url.includes('/apply')
    });

    const result = PlatformDetector.detect('https://customstartup.com/jobs/backend/apply', doc);
    expect(result.name).toBe('Custom Startup Portal');
    expect(result.isSupported).toBe(true);
    expect(result.isApplicationPage).toBe(true);
  });
});
