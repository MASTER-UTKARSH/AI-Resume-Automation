/**
 * LinkedIn Jobs Adapter
 * Specialized adapter for LinkedIn job view and Easy Apply modals.
 */

import { GenericJobAdapter } from '../generic/GenericJobAdapter';
import { PlatformCategory, PageInspectionResult } from '../../../shared/types/adapter';

export class LinkedInJobsAdapter extends GenericJobAdapter {
  public override name = 'LinkedIn Jobs';
  public override platformCategory: PlatformCategory = 'JOB_BOARD';
  public override supportedDomains = ['linkedin.com'];

  public override detect(url: string, doc: Document): boolean {
    return (
      /linkedin\.com\/jobs/i.test(url) ||
      Boolean(doc.querySelector('.jobs-apply-button, .jobs-easy-apply-modal, [data-job-id]'))
    );
  }

  public override async inspectPage(doc: Document): Promise<PageInspectionResult> {
    const base = await super.inspectPage(doc);
    const liTitle = doc.querySelector('.job-details-jobs-unified-top-card__job-title, .top-card-layout__title');
    const liCompany = doc.querySelector('.job-details-jobs-unified-top-card__company-name, .topcard__org-name-link');

    return {
      ...base,
      platform_name: this.name,
      platform_category: this.platformCategory,
      job_title: liTitle?.textContent?.trim() || base.job_title,
      company_name: liCompany?.textContent?.trim() || base.company_name,
      capabilities: ['EASY_APPLY_DETECT', 'FIELD_MAPPING', 'AUTOFILL']
    };
  }
}

