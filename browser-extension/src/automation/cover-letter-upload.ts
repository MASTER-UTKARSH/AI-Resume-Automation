/**
 * Cover Letter Upload Engine
 * Handles both file upload inputs and textareas for tailored cover letters.
 */

import { UploadResult } from '../shared/types/adapter';
import { DomUtils } from '../content/dom-utils';

export class CoverLetterUploadEngine {
  private static textSelectors = [
    'textarea[name*="cover" i]',
    'textarea[id*="cover" i]',
    'textarea[aria-label*="cover" i]',
    'textarea[placeholder*="cover" i]',
    'textarea[name*="letter" i]'
  ];

  private static fileSelectors = [
    'input[type="file"][name*="cover" i]',
    'input[type="file"][id*="cover" i]',
    'input[type="file"][aria-label*="cover" i]'
  ];

  public static async uploadCoverLetter(
    contentOrBlob: string | Blob,
    fileName: string,
    doc: Document
  ): Promise<UploadResult> {
    // 1. Check for dedicated textarea
    if (typeof contentOrBlob === 'string') {
      for (const sel of CoverLetterUploadEngine.textSelectors) {
        const textarea = doc.querySelector<HTMLTextAreaElement>(sel);
        if (textarea && DomUtils.isVisible(textarea)) {
          DomUtils.setInputValue(textarea, contentOrBlob);
          return {
            success: textarea.value === contentOrBlob,
            file_name: 'cover_letter_text.txt',
            field_id: textarea.id || textarea.name
          };
        }
      }
    }

    // 2. Check for cover letter file input
    for (const sel of CoverLetterUploadEngine.fileSelectors) {
      const fileInput = doc.querySelector<HTMLInputElement>(sel);
      if (fileInput && fileInput.type === 'file') {
        const blob = typeof contentOrBlob === 'string'
          ? new Blob([contentOrBlob], { type: 'text/plain' })
          : contentOrBlob;

        const file = new File([blob], fileName, { type: blob.type || 'application/pdf' });
        const attached = DomUtils.attachFileToInput(fileInput, file);

        return {
          success: attached,
          file_name: fileName,
          field_id: fileInput.id || fileInput.name,
          error: attached ? undefined : 'Failed to attach cover letter file.'
        };
      }
    }

    return {
      success: false,
      file_name: fileName,
      error: 'No suitable cover letter field or upload input found.'
    };
  }
}

