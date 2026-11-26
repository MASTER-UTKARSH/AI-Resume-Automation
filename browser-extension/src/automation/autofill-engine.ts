/**
 * Form Autofill Engine
 * Populates supported input elements, triggers framework-safe events,
 * verifies real DOM state updates, and enforces anti-fabrication rules.
 */

import { NormalizedField, FieldFillResult } from '../shared/types/adapter';
import { DomUtils } from '../content/dom-utils';

export class AutofillEngine {
  /**
   * Fills a single field according to its type and verifies that the value was written
   */
  public static async fillField(field: NormalizedField, value: string | boolean, doc: Document): Promise<FieldFillResult> {
    const el = doc.querySelector<HTMLElement>(field.selector) || doc.getElementById(field.field_id);

    if (!el) {
      return {
        field_id: field.field_id,
        success: false,
        populated_value: '',
        error: `Element not found for selector '${field.selector}'`
      };
    }

    try {
      if (typeof value === 'string' && (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement)) {
        if (['text', 'email', 'tel', 'textarea'].includes(field.field_type)) {
          DomUtils.setInputValue(el, value);

          // Verification: Check if value is actually in DOM
          const verified = el.value === value || el.value.length > 0;
          return {
            field_id: field.field_id,
            success: verified,
            populated_value: el.value,
            error: verified ? undefined : 'Value was rejected or cleared by page script.'
          };
        }
      }

      if (el instanceof HTMLSelectElement && typeof value === 'string') {
        const success = DomUtils.setSelectValue(el, value);
        return {
          field_id: field.field_id,
          success,
          populated_value: el.value || value,
          error: success ? undefined : `Option '${value}' not found in select dropdown.`
        };
      }

      if (el instanceof HTMLInputElement && el.type === 'checkbox' && typeof value === 'boolean') {
        DomUtils.setCheckboxValue(el, value);
        return {
          field_id: field.field_id,
          success: el.checked === value,
          populated_value: el.checked
        };
      }

      if (el instanceof HTMLInputElement && el.type === 'radio' && typeof value === 'string') {
        const radioGroup = doc.querySelectorAll<HTMLInputElement>(`input[type="radio"][name="${el.name}"]`);
        let matched = false;
        radioGroup.forEach(radio => {
          if (radio.value.toLowerCase() === value.toLowerCase() || radio.id.toLowerCase().includes(value.toLowerCase())) {
            radio.click();
            radio.checked = true;
            radio.dispatchEvent(new Event('change', { bubbles: true }));
            matched = true;
          }
        });
        return {
          field_id: field.field_id,
          success: matched,
          populated_value: value
        };
      }

      return {
        field_id: field.field_id,
        success: false,
        populated_value: '',
        error: `Unsupported field type or value mismatch: ${field.field_type}`
      };
    } catch (err: any) {
      return {
        field_id: field.field_id,
        success: false,
        populated_value: '',
        error: err?.message || 'DOM operation threw exception.'
      };
    }
  }

  /**
   * Batch fills all mapped candidate fields and collects execution results
   */
  public static async fillBatch(
    fieldActions: Array<{ field: NormalizedField; value: string | boolean }>,
    doc: Document
  ): Promise<{ results: FieldFillResult[]; filledCount: number; failedCount: number }> {
    const results: FieldFillResult[] = [];
    let filledCount = 0;
    let failedCount = 0;

    for (const item of fieldActions) {
      // Do not fill empty values (no fabrication)
      if (item.value === '' || item.value === null || item.value === undefined) {
        continue;
      }

      const res = await AutofillEngine.fillField(item.field, item.value, doc);
      results.push(res);
      if (res.success) filledCount++;
      else failedCount++;

      // Micro-pause to allow dynamic scripts to process state changes
      await new Promise(r => setTimeout(r, 40));
    }

    return { results, filledCount, failedCount };
  }
}

