/**
 * Greenhouse ATS Platform Adapter
 * Specialized adapter for Greenhouse job boards (boards.greenhouse.io).
 */

import { GenericJobAdapter } from '../generic/GenericJobAdapter';
import { PlatformCategory, PageInspectionResult } from '../../../shared/types/adapter';

export class GreenhouseAdapter extends GenericJobAdapter {
  public override name = 'Greenhouse ATS';
  public override platformCategory: PlatformCategory = 'COMPANY_CAREERS';
  public override supportedDomains = ['boards.greenhouse.io', 'job-boards.greenhouse.io'];

  public override detect(url: string, doc: Document): boolean {
    return (
      /greenhouse\.io/i.test(url) ||
      Boolean(doc.querySelector('form#application_form, div#application, meta[content*="greenhouse" i]'))
    );
  }

  public override async inspectPage(doc: Document): Promise<PageInspectionResult> {
    const base = await super.inspectPage(doc);
    const ghTitle = doc.querySelector('.app-title, h1.heading, #header .app-title');
    const ghCompany = doc.querySelector('.company-name, #header .company-name');

    return {
      ...base,
      platform_name: this.name,
      platform_category: this.platformCategory,
      job_title: ghTitle?.textContent?.trim() || base.job_title,
      company_name: ghCompany?.textContent?.trim() || base.company_name
    };
  }
}

