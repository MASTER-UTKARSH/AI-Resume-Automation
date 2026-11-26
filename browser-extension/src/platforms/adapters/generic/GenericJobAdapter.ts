/**
 * Generic Job Adapter
 * Provides robust default behavior for standard HTML/React application forms.
 */

import {
  PlatformAdapter,
  PlatformCategory,
  PageInspectionResult,
  NormalizedField,
  FieldActionPlan,
  FieldFillResult,
  UploadResult,
  ValidationResult,
  SubmissionApproval,
  ApplicationResult
} from '../../../shared/types/adapter';
import { CandidateProfile } from '../../../shared/types/candidate';
import { FormMapper } from '../../../automation/form-mapper';
import { AutofillEngine } from '../../../automation/autofill-engine';
import { ResumeUploadEngine } from '../../../automation/resume-upload';
import { CoverLetterUploadEngine } from '../../../automation/cover-letter-upload';
import { SubmissionEngine } from '../../../automation/submission-engine';
import { ResultCapture } from '../../../automation/result-capture';

export class GenericJobAdapter implements PlatformAdapter {
  public name = 'Generic Application Portal';
  public platformCategory: PlatformCategory = 'GENERIC';
  public supportedDomains = ['*'];

  public detect(_url: string, doc: Document): boolean {
    return Boolean(
      doc.querySelector('form[action*="apply"], form[id*="job"], form[class*="application"], form[class*="apply"], input[type="file"]')
    );
  }

  public async inspectPage(doc: Document): Promise<PageInspectionResult> {
    const fields = await this.extractFormFields(doc);
    const titleEl = doc.querySelector('h1, .job-title, [data-automation-id="jobPostingHeader"]');
    const companyEl = doc.querySelector('.company-name, .employer, [data-automation-id="companyName"]');
    const hasUpload = fields.some(f => f.field_type === 'file');
    const hasCaptcha = SubmissionEngine.detectCaptchaOrMFA(doc);

    return {
      platform_name: this.name,
      platform_category: this.platformCategory,
      is_supported: true,
      is_application_page: fields.length >= 2,
      job_title: titleEl?.textContent?.trim() || doc.title || 'Software Engineer',
      company_name: companyEl?.textContent?.trim() || 'Hiring Enterprise',
      form_detected: fields.length > 0,
      total_fields: fields.length,
      has_file_upload: hasUpload,
      has_captcha: hasCaptcha,
      capabilities: ['AUTOFILL', 'RESUME_UPLOAD', 'COVER_LETTER_UPLOAD', 'SUBMISSION_VERIFY']
    };
  }

  public async extractFormFields(doc: Document): Promise<NormalizedField[]> {
    return FormMapper.extractFormFields(doc);
  }

  public mapFields(fields: NormalizedField[], profile: CandidateProfile): FieldActionPlan {
    const actions: FieldActionPlan['actions'] = [];
    const unmapped: NormalizedField[] = [];
    let matchedScores = 0;

    for (const field of fields) {
      if (field.candidate_profile_key) {
        const val = FormMapper.resolveProfileValue(field.candidate_profile_key, profile);
        actions.push({
          field,
          value_to_fill: val,
          strategy: field.field_type === 'select' ? 'select_option' : 'native_input'
        });
        matchedScores += field.confidence_score;
      } else {
        unmapped.push(field);
      }
    }

    const overallConfidence = fields.length > 0 ? Math.round((matchedScores / fields.length) * 100) / 100 : 0.0;

    return {
      actions,
      unmapped_fields: unmapped,
      missing_profile_keys: [],
      overall_confidence: overallConfidence
    };
  }

  public async fillField(field: NormalizedField, value: string | boolean, doc: Document): Promise<FieldFillResult> {
    return AutofillEngine.fillField(field, value, doc);
  }

  public async uploadResume(fileBlob: Blob, fileName: string, doc: Document): Promise<UploadResult> {
    return ResumeUploadEngine.uploadResume(fileBlob, fileName, doc);
  }

  public async uploadCoverLetter(contentOrBlob: string | Blob, fileName: string, doc: Document): Promise<UploadResult> {
    return CoverLetterUploadEngine.uploadCoverLetter(contentOrBlob, fileName, doc);
  }

  public async validateForm(doc: Document): Promise<ValidationResult> {
    const fields = await this.extractFormFields(doc);
    const unfilledRequired = fields.filter(f => f.required && (!f.current_value || f.current_value === ''));
    return {
      is_valid: unfilledRequired.length === 0,
      unfilled_required_fields: unfilledRequired,
      warnings: unfilledRequired.map(f => `Required field '${f.label}' is not yet populated.`)
    };
  }

  public async submitApplication(doc: Document, approval: SubmissionApproval): Promise<ApplicationResult> {
    return SubmissionEngine.executeSubmission(doc, approval, approval.application_id);
  }

  public async getApplicationResult(doc: Document): Promise<ApplicationResult> {
    return ResultCapture.captureResult(doc);
  }
}

