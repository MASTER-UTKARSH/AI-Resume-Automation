# Platform Adapter System Guide

## 1. Overview

The Clyde Browser Extension uses a modular **Platform Adapter Pattern**. Every job site or ATS (Applicant Tracking System) implements the standard `PlatformAdapter` interface.

```
src/platforms/
├── core/
│   ├── PlatformAdapter.ts   # Interface contract
│   ├── PlatformDetector.ts  # URL & DOM rule matcher
│   └── PlatformRegistry.ts  # Global singleton registry
└── adapters/
    ├── company-careers/
    │   ├── GreenhouseAdapter.ts
    │   ├── LeverAdapter.ts
    │   └── WorkdayAdapter.ts
    ├── job-board/
    │   └── LinkedInJobsAdapter.ts
    ├── internship-platform/
    │   └── SimplifyJobsAdapter.ts
    └── generic/
        └── GenericJobAdapter.ts
```

---

## 2. Implementing a New Adapter

To add support for a new job portal (e.g., Ashby, SmartRecruiters, Indeed):

### Step 1: Create the Adapter Class
Implement `PlatformAdapter`:

```typescript
import { PlatformAdapter, PageInspectionResult, NormalizedField, FieldActionPlan, ValidationResult, ApplicationResult, SubmissionApproval } from '../../core/PlatformAdapter';
import { CandidateProfile } from '../../../shared/types/candidate';
import { FormMapper } from '../../../automation/form-mapper';
import { AutofillEngine } from '../../../automation/autofill-engine';
import { SubmissionEngine } from '../../../automation/submission-engine';

export class AshbyAdapter implements PlatformAdapter {
  public readonly platformName = 'Ashby ATS';
  public readonly platformCategory = 'COMPANY_CAREERS';

  public async detect(url: string, doc: Document): Promise<boolean> {
    return /jobs\.ashbyhq\.com/i.test(url) || Boolean(doc.querySelector('[data-ashby-application-form]'));
  }

  public async inspectPage(doc: Document): Promise<PageInspectionResult> {
    const fields = await this.extractFormFields(doc);
    return {
      platform_name: this.platformName,
      platform_category: this.platformCategory,
      is_supported: true,
      is_application_page: /application|apply/i.test(window.location.href),
      form_detected: fields.length > 0,
      total_fields: fields.length,
      has_file_upload: Boolean(doc.querySelector('input[type="file"]')),
      has_captcha: SubmissionEngine.detectCaptchaOrMFA(doc),
      capabilities: ['AUTOFILL', 'RESUME_UPLOAD', 'SUBMISSION_VERIFY']
    };
  }

  public async extractFormFields(doc: Document): Promise<NormalizedField[]> {
    return FormMapper.extractFormFields(doc);
  }

  public mapFields(fields: NormalizedField[], profile: CandidateProfile): FieldActionPlan {
    // Return action plan using FormMapper
    ...
  }

  public async fillField(field: NormalizedField, value: string | boolean, doc: Document) {
    return AutofillEngine.fillField(field, value, doc);
  }

  public async validateForm(doc: Document): Promise<ValidationResult> {
    const fields = await this.extractFormFields(doc);
    return FormMapper.validateForm(fields);
  }

  public async submitApplication(doc: Document, approval: SubmissionApproval): Promise<ApplicationResult> {
    return SubmissionEngine.executeSubmission(doc, approval, approval.application_id);
  }
}
```

### Step 2: Register in `PlatformRegistry`
Add the adapter instance into `src/platforms/core/PlatformRegistry.ts`:

```typescript
this.register(new AshbyAdapter());
```

---

## 3. Best Practices for Adapters

1. **Selector Isolation**: Never hardcode fragile full XPath selectors. Prefer `name`, `aria-*`, `data-automation-id`, or associated `<label>` text.
2. **Synthetic Events**: Use `DomUtils.setInputValue` to ensure framework state tracks value changes.
3. **Anti-Bot Gating**: Always call `SubmissionEngine.detectCaptchaOrMFA(doc)` in `inspectPage` and `submitApplication`.
4. **Approval Enforcement**: Forward the user's `approval_token` to `SubmissionEngine.executeSubmission`.

