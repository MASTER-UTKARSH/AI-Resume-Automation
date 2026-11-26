import { describe, it, expect, beforeEach } from 'vitest';
import { AutofillEngine } from '../../src/automation/autofill-engine';
import { NormalizedField } from '../../src/shared/types/adapter';

describe('AutofillEngine', () => {
  let doc: Document;

  beforeEach(() => {
    doc = document.implementation.createHTMLDocument('Autofill Form Test');
    doc.body.innerHTML = `
      <form id="test-autofill-form">
        <input type="text" id="cand-name" name="name" />
        <input type="email" id="cand-email" name="email" />
        <textarea id="cand-cover" name="cover"></textarea>
        
        <select id="cand-country" name="country">
          <option value="">Select country</option>
          <option value="in">India</option>
          <option value="us">United States</option>
        </select>

        <input type="checkbox" id="cand-auth" name="authorized" />

        <input type="radio" id="gender-m" name="gender" value="male" />
        <input type="radio" id="gender-f" name="gender" value="female" />
      </form>
    `;
  });

  it('populates text input and verifies actual DOM value', async () => {
    const field: NormalizedField = {
      field_id: 'cand-name',
      field_type: 'text',
      label: 'Name',
      required: true,
      current_value: '',
      confidence_score: 0.95,
      candidate_profile_key: 'full_name',
      selector: '#cand-name'
    };

    const result = await AutofillEngine.fillField(field, 'Utkarsh Shah', doc);
    expect(result.success).toBe(true);
    expect(result.populated_value).toBe('Utkarsh Shah');

    const input = doc.getElementById('cand-name') as HTMLInputElement;
    expect(input.value).toBe('Utkarsh Shah');
  });

  it('populates textarea input and verifies DOM update', async () => {
    const field: NormalizedField = {
      field_id: 'cand-cover',
      field_type: 'textarea',
      label: 'Cover Letter',
      required: false,
      current_value: '',
      confidence_score: 0.9,
      candidate_profile_key: 'cover_letter',
      selector: '#cand-cover'
    };

    const result = await AutofillEngine.fillField(field, 'Excited to apply for this engineering role.', doc);
    expect(result.success).toBe(true);

    const textarea = doc.getElementById('cand-cover') as HTMLTextAreaElement;
    expect(textarea.value).toBe('Excited to apply for this engineering role.');
  });

  it('selects option in select dropdown', async () => {
    const field: NormalizedField = {
      field_id: 'cand-country',
      field_type: 'select',
      label: 'Country',
      required: true,
      current_value: '',
      confidence_score: 0.85,
      selector: '#cand-country'
    };

    const result = await AutofillEngine.fillField(field, 'India', doc);
    expect(result.success).toBe(true);

    const select = doc.getElementById('cand-country') as HTMLSelectElement;
    expect(select.value).toBe('in');
  });

  it('sets checkbox checked state accurately', async () => {
    const field: NormalizedField = {
      field_id: 'cand-auth',
      field_type: 'checkbox',
      label: 'Authorized',
      required: true,
      current_value: false,
      confidence_score: 0.9,
      selector: '#cand-auth'
    };

    const result = await AutofillEngine.fillField(field, true, doc);
    expect(result.success).toBe(true);

    const checkbox = doc.getElementById('cand-auth') as HTMLInputElement;
    expect(checkbox.checked).toBe(true);
  });

  it('handles missing elements gracefully without crashing', async () => {
    const field: NormalizedField = {
      field_id: 'non-existent-input',
      field_type: 'text',
      label: 'Ghost Field',
      required: false,
      current_value: '',
      confidence_score: 0.5,
      selector: '#non-existent-input'
    };

    const result = await AutofillEngine.fillField(field, 'Sample Value', doc);
    expect(result.success).toBe(false);
    expect(result.error).toContain('Element not found');
  });
});

