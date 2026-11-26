/**
 * Platform Adapter Interface and Normalization Types
 * Defines the contract for all supported job portals and ATS systems.
 */

import { CandidateProfile, CandidateProfileKey } from './candidate';
import { ApplicationStatus } from './events';

export type PlatformCategory = 'COMPANY_CAREERS' | 'JOB_BOARD' | 'INTERNSHIP_PLATFORM' | 'GENERIC';

export type FieldInputType =
  | 'text'
  | 'email'
  | 'tel'
  | 'textarea'
  | 'select'
  | 'radio'
  | 'checkbox'
  | 'file'
  | 'unknown';

export interface NormalizedField {
  field_id: string;
  field_type: FieldInputType;
  label: string;
  placeholder?: string;
  required: boolean;
  current_value?: string | boolean;
  confidence_score: number; // 0.0 to 1.0
  candidate_profile_key?: CandidateProfileKey;
  selector: string;
  is_custom_dropdown?: boolean;
  options?: string[];
}

export interface FieldActionItem {
  field: NormalizedField;
  value_to_fill: string | boolean;
  strategy: 'native_input' | 'react_synthetic' | 'select_option' | 'checkbox_toggle' | 'file_transfer';
}

export interface FieldActionPlan {
  actions: FieldActionItem[];
  unmapped_fields: NormalizedField[];
  missing_profile_keys: CandidateProfileKey[];
  overall_confidence: number;
}

export interface FieldFillResult {
  field_id: string;
  success: boolean;
  populated_value: string | boolean;
  error?: string;
}

export interface PageInspectionResult {
  platform_name: string;
  platform_category: PlatformCategory;
  is_supported: boolean;
  is_application_page: boolean;
  job_title?: string;
  company_name?: string;
  form_detected: boolean;
  total_fields: number;
  has_file_upload: boolean;
  has_captcha: boolean;
  capabilities: string[];
}

export interface UploadResult {
  success: boolean;
  file_name: string;
  field_id?: string;
  error?: string;
}

export interface ValidationResult {
  is_valid: boolean;
  unfilled_required_fields: NormalizedField[];
  warnings: string[];
}

export interface ApplicationPreview {
  application_id: string;
  company_name: string;
  job_title: string;
  job_url: string;
  fields_populated: Array<{ label: string; value: string }>;
  unmapped_required_fields: string[];
  resume_attached: string;
  cover_letter_attached?: string;
  warnings: string[];
  requires_user_approval: boolean;
  preview_timestamp: string;
}

export interface SubmissionApproval {
  application_id: string;
  workflow_id: string;
  approved_by_user: boolean;
  approval_token: string;
  timestamp: string;
}

export interface ApplicationResult {
  status: ApplicationStatus;
  confirmation_message?: string;
  confirmation_url?: string;
  timestamp: string;
  platform: string;
  job_title?: string;
  company_name?: string;
  error_reason?: string;
}

export interface PlatformAdapter {
  name: string;
  platformCategory: PlatformCategory;
  supportedDomains: string[];

  detect(url: string, document: Document): boolean;
  inspectPage(document: Document): Promise<PageInspectionResult>;
  extractFormFields(document: Document): Promise<NormalizedField[]>;
  mapFields(fields: NormalizedField[], profile: CandidateProfile): FieldActionPlan;
  fillField(field: NormalizedField, value: string | boolean, document: Document): Promise<FieldFillResult>;
  uploadResume(fileBlob: Blob, fileName: string, document: Document): Promise<UploadResult>;
  uploadCoverLetter(contentOrBlob: string | Blob, fileName: string, document: Document): Promise<UploadResult>;
  validateForm(document: Document): Promise<ValidationResult>;
  submitApplication(document: Document, approval: SubmissionApproval): Promise<ApplicationResult>;
  getApplicationResult(document: Document): Promise<ApplicationResult>;
}

