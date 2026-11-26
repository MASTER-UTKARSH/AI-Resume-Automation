/**
 * Form Mapper Engine
 * Deterministically maps DOM application form inputs to normalized candidate profile keys.
 * Implements the 8-level strategy hierarchy defined in Section 4.E.
 */

import { NormalizedField, FieldInputType, ValidationResult } from '../shared/types/adapter';
import { CandidateProfileKey, CandidateProfile } from '../shared/types/candidate';
import { DomUtils } from '../content/dom-utils';

interface DetectionRule {
  key: CandidateProfileKey;
  patterns: RegExp[];
  confidence: number;
}

export class FormMapper {
  private static rules: DetectionRule[] = [
    {
      key: 'full_name',
      patterns: [/full[_\s-]?name/i, /^name$/i, /your[_\s-]?name/i, /candidate[_\s-]?name/i],
      confidence: 0.95
    },
    {
      key: 'first_name',
      patterns: [/first[_\s-]?name/i, /given[_\s-]?name/i, /fname/i],
      confidence: 0.95
    },
    {
      key: 'last_name',
      patterns: [/last[_\s-]?name/i, /surname/i, /family[_\s-]?name/i, /lname/i],
      confidence: 0.95
    },
    {
      key: 'email',
      patterns: [/e[_\s-]?mail/i, /email[_\s-]?address/i],
      confidence: 0.98
    },
    {
      key: 'phone',
      patterns: [/phone/i, /mobile/i, /cell/i, /contact[_\s-]?number/i, /tel\b/i],
      confidence: 0.95
    },
    {
      key: 'cover_letter',
      patterns: [/cover[_\s-]?letter/i, /note[_\s-]?to[_\s-]?hiring[_\s-]?manager/i, /additional[_\s-]?information/i, /statement[_\s-]?of[_\s-]?interest/i],
      confidence: 0.94
    },
    {
      key: 'location',
      patterns: [/location/i, /\bcity\b/i, /\baddress\b/i, /\bstate\b/i, /\bcountry\b/i, /residence/i],
      confidence: 0.85
    },
    {
      key: 'linkedin_url',
      patterns: [/linkedin/i, /linkedin\.com/i, /social[_\s-]?linkedin/i],
      confidence: 0.98
    },
    {
      key: 'github_url',
      patterns: [/github/i, /github\.com/i, /git/i],
      confidence: 0.98
    },
    {
      key: 'portfolio_url',
      patterns: [/portfolio/i, /website/i, /personal[_\s-]?site/i, /blog/i],
      confidence: 0.90
    },
    {
      key: 'institution',
      patterns: [/university/i, /college/i, /institution/i, /school/i],
      confidence: 0.90
    },
    {
      key: 'degree',
      patterns: [/degree/i, /major/i, /field[_\s-]?of[_\s-]?study/i, /discipline/i],
      confidence: 0.88
    },
    {
      key: 'graduation_year',
      patterns: [/graduat/i, /completion[_\s-]?year/i, /end[_\s-]?year/i, /passing[_\s-]?year/i],
      confidence: 0.88
    },
    {
      key: 'gpa',
      patterns: [/\bgpa\b/i, /cgpa/i, /percentage/i, /score/i],
      confidence: 0.85
    },
    {
      key: 'work_authorization',
      patterns: [/authoriz/i, /legally[_\s-]?eligible/i, /work[_\s-]?permit/i, /right[_\s-]?to[_\s-]?work/i],
      confidence: 0.90
    },
    {
      key: 'requires_sponsorship',
      patterns: [/sponsor/i, /visa/i, /require[_\s-]?sponsorship/i],
      confidence: 0.90
    },
    {
      key: 'cover_letter',
      patterns: [/cover[_\s-]?letter/i, /note[_\s-]?to[_\s-]?hiring[_\s-]?manager/i, /additional[_\s-]?information/i],
      confidence: 0.92
    },
    {
      key: 'resume_file',
      patterns: [/resume/i, /cv\b/i, /curriculum[_\s-]?vitae/i],
      confidence: 0.96
    }
  ];

  /**
   * Scans a container (or document) and identifies all interactive application form fields
   */
  public static extractFormFields(container: HTMLElement | Document): NormalizedField[] {
    const selector = 'input, textarea, select';
    const rawElements = Array.from(container.querySelectorAll<HTMLElement>(selector));
    const fields: NormalizedField[] = [];

    rawElements.forEach((el, index) => {
      // Ignore hidden inputs, buttons, submits
      if (el instanceof HTMLInputElement && ['hidden', 'submit', 'button', 'reset', 'image'].includes(el.type)) {
        return;
      }
      if (!DomUtils.isVisible(el)) {
        return;
      }

      const field = FormMapper.inspectElement(el, index);
      fields.push(field);
    });

    return fields;
  }

  /**
   * Inspects a single DOM element using the 8-strategy hierarchy
   */
  public static inspectElement(el: HTMLElement, index: number): NormalizedField {
    const inputEl = el as HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement;
    const fieldId = el.id || el.getAttribute('name') || `field-${index}`;
    const fieldType = FormMapper.determineFieldType(el);
    const isRequired = el.hasAttribute('required') || el.getAttribute('aria-required') === 'true';
    const doc = el.ownerDocument || document;

    // 8-Level Detection Strategy
    // Strategy 1 & 2: Associated <label for="..."> element
    let labelText = '';
    if (el.id) {
      const associatedLabel = doc.querySelector(`label[for="${el.id}"]`);
      if (associatedLabel) {
        labelText = DomUtils.cleanText(associatedLabel.textContent);
      }
    }

    // Strategy 1 (cont): Enclosing <label>
    if (!labelText) {
      const parentLabel = el.closest('label');
      if (parentLabel) {
        labelText = DomUtils.cleanText(parentLabel.textContent);
      }
    }

    // Strategy 3: Placeholder
    const placeholder = el.getAttribute('placeholder') || '';

    // Strategy 4 & 5: Name and ID attributes
    const nameAttr = el.getAttribute('name') || '';
    const idAttr = el.id || '';

    // Strategy 6: ARIA labels
    const ariaLabel = el.getAttribute('aria-label') || '';
    let ariaLabelledBy = '';
    const labelledById = el.getAttribute('aria-labelledby');
    if (labelledById) {
      const labelRef = doc.getElementById(labelledById);
      if (labelRef) ariaLabelledBy = DomUtils.cleanText(labelRef.textContent);
    }

    // Strategy 7: Sibling and Parent DOM relationships (e.g. preceding text or fieldset legend)
    let siblingText = '';
    const prev = el.previousElementSibling;
    if (prev && ['LABEL', 'SPAN', 'P', 'DIV', 'H3', 'H4'].includes(prev.tagName)) {
      siblingText = DomUtils.cleanText(prev.textContent);
    }

    // Best label candidate
    const effectiveLabel = labelText || ariaLabel || ariaLabelledBy || siblingText || placeholder || nameAttr || idAttr;

    // Evaluate matching against rules
    const match = FormMapper.matchCandidateKey({
      labelText,
      placeholder,
      nameAttr,
      idAttr,
      ariaLabel,
      ariaLabelledBy,
      siblingText
    });

    return {
      field_id: fieldId,
      field_type: fieldType,
      label: effectiveLabel || 'Unlabeled Field',
      placeholder,
      required: isRequired,
      current_value: inputEl.value || (inputEl instanceof HTMLInputElement && inputEl.type === 'checkbox' ? inputEl.checked : ''),
      confidence_score: match ? match.confidence : 0.1,
      candidate_profile_key: match ? match.key : undefined,
      selector: FormMapper.generateSelector(el)
    };
  }

  private static determineFieldType(el: HTMLElement): FieldInputType {
    if (el instanceof HTMLTextAreaElement) return 'textarea';
    if (el instanceof HTMLSelectElement) return 'select';
    if (el instanceof HTMLInputElement) {
      const t = el.type.toLowerCase();
      if (['text', 'email', 'tel', 'checkbox', 'radio', 'file'].includes(t)) {
        return t as FieldInputType;
      }
    }
    return 'text';
  }

  private static matchCandidateKey(candidates: {
    labelText: string;
    placeholder: string;
    nameAttr: string;
    idAttr: string;
    ariaLabel: string;
    ariaLabelledBy: string;
    siblingText: string;
  }): { key: CandidateProfileKey; confidence: number } | null {
    const combinedTexts = [
      { text: candidates.labelText, weight: 1.0 },
      { text: candidates.ariaLabel || candidates.ariaLabelledBy, weight: 0.95 },
      { text: candidates.placeholder, weight: 0.90 },
      { text: candidates.nameAttr, weight: 0.85 },
      { text: candidates.idAttr, weight: 0.80 },
      { text: candidates.siblingText, weight: 0.70 }
    ];

    for (const rule of FormMapper.rules) {
      for (const item of combinedTexts) {
        if (!item.text) continue;
        for (const pattern of rule.patterns) {
          if (pattern.test(item.text)) {
            const finalConfidence = Math.round(rule.confidence * item.weight * 100) / 100;
            return { key: rule.key, confidence: finalConfidence };
          }
        }
      }
    }

    return null;
  }

  public static generateSelector(el: HTMLElement): string {
    if (el.id) return `#${el.id}`;
    if (el.getAttribute('name')) return `${el.tagName.toLowerCase()}[name="${el.getAttribute('name')}"]`;
    if (el.getAttribute('data-automation-id')) return `[data-automation-id="${el.getAttribute('data-automation-id')}"]`;
    return el.tagName.toLowerCase();
  }

  /**
   * Translates detected fields into fill actions mapped against candidate profile
   */
  public static mapCandidateToForm(fields: NormalizedField[], profile: CandidateProfile): {
    fields_to_fill: Array<{ field_id: string; value: string | boolean }>;
    unmapped_fields: NormalizedField[];
  } {
    const fields_to_fill: Array<{ field_id: string; value: string | boolean }> = [];
    const unmapped_fields: NormalizedField[] = [];

    for (const field of fields) {
      if (field.candidate_profile_key) {
        const value = FormMapper.resolveProfileValue(field.candidate_profile_key, profile);
        if (value !== '' && value !== undefined) {
          fields_to_fill.push({ field_id: field.field_id, value });
        }
      } else {
        unmapped_fields.push(field);
      }
    }

    return { fields_to_fill, unmapped_fields };
  }

  /**
   * Validates form fields and identifies unfilled required fields
   */
  public static validateForm(fields: NormalizedField[]): ValidationResult {
    const unfilledRequired = fields.filter(f => f.required && (!f.current_value || f.current_value === ''));
    return {
      is_valid: unfilledRequired.length === 0,
      unfilled_required_fields: unfilledRequired,
      warnings: unfilledRequired.map(f => `Required field '${f.label}' is not yet populated.`)
    };
  }

  /**
   * Resolves normalized field values from candidate profile
   */
  public static resolveProfileValue(key: CandidateProfileKey, profile: CandidateProfile): string | boolean {
    switch (key) {
      case 'full_name': return profile.full_name;
      case 'first_name': return profile.first_name;
      case 'last_name': return profile.last_name;
      case 'email': return profile.email;
      case 'phone': return profile.phone;
      case 'location': return profile.location;
      case 'headline': return profile.headline;
      case 'summary': return profile.summary;
      case 'linkedin_url': return profile.linkedin_url || '';
      case 'github_url': return profile.github_url || '';
      case 'portfolio_url': return profile.portfolio_url || '';
      case 'work_authorization': return profile.work_authorization || 'Yes';
      case 'requires_sponsorship': return profile.requires_sponsorship || 'No';
      case 'institution': return profile.education[0]?.institution || '';
      case 'degree': return profile.education[0]?.degree || '';
      case 'graduation_year': return profile.education[0]?.graduation_year || '';
      case 'gpa': return profile.education[0]?.gpa || '';
      case 'skills': return profile.skills.join(', ');
      case 'cover_letter':
        return (profile as any).cover_letter || `Dear Hiring Team,\n\nI am writing to express my strong interest in this engineering role. With verified production experience in Python, FastAPI, PyTorch, FAISS vector indexing, and Docker containerization, I am confident in delivering high impact to your technical team.\n\nSincerely,\n${profile.full_name || 'Utkarsh Shah'}`;
      default: return '';
    }
  }
}
