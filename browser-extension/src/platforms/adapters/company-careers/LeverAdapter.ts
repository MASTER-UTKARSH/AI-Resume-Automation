/**
 * Lever ATS Platform Adapter
 * Specialized adapter for Lever job postings (jobs.lever.co).
 */

import { GenericJobAdapter } from '../generic/GenericJobAdapter';
import { PlatformCategory, PageInspectionResult } from '../../../shared/types/adapter';

export class LeverAdapter extends GenericJobAdapter {
  public override name = 'Lever ATS';
  public override platformCategory: PlatformCategory = 'COMPANY_CAREERS';
  public override supportedDomains = ['jobs.lever.co'];

  public override detect(url: string, doc: Document): boolean {
    return (
      /jobs\.lever\.co/i.test(url) ||
      Boolean(doc.querySelector('form.application-form, .lever-job-title, .postings-btn-wrapper'))
    );
  }

  public override async inspectPage(doc: Document): Promise<PageInspectionResult> {
    const base = await super.inspectPage(doc);
    const leverTitle = doc.querySelector('.posting-headline h2, .lever-job-title');
    const leverCompany = doc.querySelector('.main-header-logo img[alt], .posting-headline .company-name');

    return {
      ...base,
      platform_name: this.name,
      platform_category: this.platformCategory,
      job_title: leverTitle?.textContent?.trim() || base.job_title,
      company_name: leverCompany?.getAttribute('alt') || leverCompany?.textContent?.trim() || base.company_name
    };
  }
}

