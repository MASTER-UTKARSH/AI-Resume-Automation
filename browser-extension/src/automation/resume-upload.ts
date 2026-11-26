/**
 * Resume Upload Engine
 * Transfers approved candidate resumes to job application file inputs.
 */

import { UploadResult } from '../shared/types/adapter';
import { DomUtils } from '../content/dom-utils';

export class ResumeUploadEngine {
  private static resumeSelectors = [
    'input[type="file"][name*="resume" i]',
    'input[type="file"][id*="resume" i]',
    'input[type="file"][aria-label*="resume" i]',
    'input[type="file"][name*="cv" i]',
    'input[type="file"][id*="cv" i]',
    'input[type="file"][data-automation-id*="resume" i]',
    'input[type="file"]' // generic fallback
  ];

  /**
   * Finds the resume file input and attaches the approved PDF/DOCX file
   */
  public static async uploadResume(
    fileBlob: Blob,
    fileName: string,
    doc: Document
  ): Promise<UploadResult> {
    const fileInput = ResumeUploadEngine.findFileInput(doc);

    if (!fileInput) {
      return {
        success: false,
        file_name: fileName,
        error: 'No resume file input element found on the application page.'
      };
    }

    try {
      const file = new File([fileBlob], fileName, {
        type: fileBlob.type || 'application/pdf',
        lastModified: Date.now()
      });

      const attached = DomUtils.attachFileToInput(fileInput, file);

      if (!attached) {
        return {
          success: false,
          file_name: fileName,
          field_id: fileInput.id || fileInput.name,
          error: 'DataTransfer attachment failed on input element.'
        };
      }

      // Allow 200ms for UI to register upload
      await new Promise(r => setTimeout(r, 200));

      const isVerified = Boolean(fileInput.files && fileInput.files.length > 0 && fileInput.files[0].name === fileName);

      return {
        success: isVerified,
        file_name: fileName,
        field_id: fileInput.id || fileInput.name,
        error: isVerified ? undefined : 'File input does not reflect attached resume.'
      };
    } catch (err: any) {
      return {
        success: false,
        file_name: fileName,
        error: err?.message || 'Exception during resume file attachment.'
      };
    }
  }

  public static findFileInput(doc: Document): HTMLInputElement | null {
    for (const sel of ResumeUploadEngine.resumeSelectors) {
      const el = doc.querySelector<HTMLInputElement>(sel);
      if (el && el.type === 'file') {
        return el;
      }
    }
    return null;
  }
}
