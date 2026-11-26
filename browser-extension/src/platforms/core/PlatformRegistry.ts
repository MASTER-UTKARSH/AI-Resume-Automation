/**
 * Platform Adapter Registry
 * Central registry maintaining platform adapters and selecting the best adapter for the active page.
 */

import { PlatformAdapter } from '../../shared/types/adapter';
import { GreenhouseAdapter } from '../adapters/company-careers/GreenhouseAdapter';
import { LeverAdapter } from '../adapters/company-careers/LeverAdapter';
import { WorkdayAdapter } from '../adapters/company-careers/WorkdayAdapter';
import { LinkedInJobsAdapter } from '../adapters/job-board/LinkedInJobsAdapter';
import { SimplifyJobsAdapter } from '../adapters/internship-platform/SimplifyJobsAdapter';
import { GenericJobAdapter } from '../adapters/generic/GenericJobAdapter';

export class PlatformRegistry {
  private static adapters: PlatformAdapter[] = [
    new GreenhouseAdapter(),
    new LeverAdapter(),
    new WorkdayAdapter(),
    new LinkedInJobsAdapter(),
    new SimplifyJobsAdapter(),
    new GenericJobAdapter() // Always last as fallback
  ];

  public static registerAdapter(adapter: PlatformAdapter): void {
    // Insert before fallback
    this.adapters.splice(this.adapters.length - 1, 0, adapter);
  }

  public static getAdapterForPage(url: string, doc: Document): PlatformAdapter {
    for (const adapter of this.adapters) {
      try {
        if (adapter.detect(url, doc)) {
          return adapter;
        }
      } catch (err) {
        console.error(`[PlatformRegistry] Error in detect() for ${adapter.name}:`, err);
      }
    }
    return this.adapters[this.adapters.length - 1]; // Return GenericJobAdapter
  }

  public static getAllAdapters(): PlatformAdapter[] {
    return [...this.adapters];
  }
}

