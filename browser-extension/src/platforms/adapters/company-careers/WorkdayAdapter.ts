/**
 * Workday ATS Platform Adapter
 * Specialized adapter for enterprise Workday portals (*.myworkdayjobs.com).
 */

import { GenericJobAdapter } from '../generic/GenericJobAdapter';
import { PlatformCategory, PageInspectionResult } from '../../../shared/types/adapter';

export class WorkdayAdapter extends GenericJobAdapter {
  public override name = 'Workday ATS';
  public override platformCategory: PlatformCategory = 'COMPANY_CAREERS';
  public override supportedDomains = ['myworkdayjobs.com', 'myworkday.com'];

  public override detect(url: string, doc: Document): boolean {
    return (
      /myworkdayjobs\.com/i.test(url) ||
      Boolean(doc.querySelector('[data-automation-id*="workday"], div[data-automation-id="jobPostingPage"]'))
    );
  }

  public override async inspectPage(doc: Document): Promise<PageInspectionResult> {
    const base = await super.inspectPage(doc);
    const wdTitle = doc.querySelector('[data-automation-id="jobPostingHeader"]');
    const wdCompany = doc.querySelector('[data-automation-id="companyName"]');

    return {
      ...base,
      platform_name: this.name,
      platform_category: this.platformCategory,
      job_title: wdTitle?.textContent?.trim() || base.job_title,
      company_name: wdCompany?.textContent?.trim() || base.company_name
    };
  }
}

