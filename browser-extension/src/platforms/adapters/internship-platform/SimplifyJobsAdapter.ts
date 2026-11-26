/**
 * SimplifyJobs Platform Adapter
 * Specialized adapter for Simplify.jobs application portal and internship aggregator.
 */

import { GenericJobAdapter } from '../generic/GenericJobAdapter';
import { PlatformCategory, PageInspectionResult } from '../../../shared/types/adapter';

export class SimplifyJobsAdapter extends GenericJobAdapter {
  public override name = 'SimplifyJobs Platform';
  public override platformCategory: PlatformCategory = 'INTERNSHIP_PLATFORM';
  public override supportedDomains = ['simplify.jobs'];

  public override detect(url: string, doc: Document): boolean {
    return (
      /simplify\.jobs/i.test(url) ||
      Boolean(doc.querySelector('[data-simplify-application], .simplify-job-card'))
    );
  }

  public override async inspectPage(doc: Document): Promise<PageInspectionResult> {
    const base = await super.inspectPage(doc);
    const title = doc.querySelector('h1, [data-simplify-title]');
    const company = doc.querySelector('[data-simplify-company]');

    return {
      ...base,
      platform_name: this.name,
      platform_category: this.platformCategory,
      job_title: title?.textContent?.trim() || base.job_title,
      company_name: company?.textContent?.trim() || base.company_name
    };
  }
}

