import { describe, it, expect, beforeEach } from 'vitest';
import { FormMapper } from '../../src/automation/form-mapper';
import { CandidateProfile } from '../../src/shared/types/candidate';

describe('FormMapper Engine', () => {
  let doc: Document;

  beforeEach(() => {
    doc = document.implementation.createHTMLDocument('Standard Application');
    doc.body.innerHTML = `
      <form id="test-form">
        <label for="full_name">Full Name *</label>
        <input type="text" id="full_name" name="candidate_name" required />

        <label for="email">Email Address *</label>
        <input type="email" id="email" name="user_email" placeholder="name@domain.com" required />

        <label for="phone">Contact Number</label>
        <input type="tel" id="phone" name="phone_number" placeholder="+91 98765 43210" />

        <label for="linkedin_url">LinkedIn Profile</label>
        <input type="text" id="linkedin_url" name="linkedin" />

        <label for="github_url">GitHub URL</label>
        <input type="text" id="github_url" name="github" />

        <label for="work_auth">Are you authorized to work in India?</label>
        <select id="work_auth" name="work_authorization">
          <option value="">Select</option>
          <option value="yes">Yes</option>
          <option value="no">No</option>
        </select>

        <label for="resume">Attach Resume *</label>
        <input type="file" id="resume" name="resume_file" accept=".pdf,.docx" required />

        <label for="cover_letter">Cover Letter</label>
        <textarea id="cover_letter" name="cover_letter_notes"></textarea>
      </form>
    `;
  });

  it('extracts and maps standard form fields deterministically', () => {
    const fields = FormMapper.extractFormFields(doc);
    expect(fields.length).toBeGreaterThanOrEqual(7);

    const nameField = fields.find(f => f.field_id === 'full_name');
    expect(nameField).toBeDefined();
    expect(nameField?.candidate_profile_key).toBe('full_name');
    expect(nameField?.confidence_score).toBeGreaterThanOrEqual(0.7);
    expect(nameField?.required).toBe(true);

    const emailField = fields.find(f => f.field_id === 'email');
    expect(emailField).toBeDefined();
    expect(emailField?.candidate_profile_key).toBe('email');
    expect(emailField?.field_type).toBe('email');

    const phoneField = fields.find(f => f.field_id === 'phone');
    expect(phoneField).toBeDefined();
    expect(phoneField?.candidate_profile_key).toBe('phone');

    const linkedinField = fields.find(f => f.field_id === 'linkedin_url');
    expect(linkedinField).toBeDefined();
    expect(linkedinField?.candidate_profile_key).toBe('linkedin_url');
  });

  it('maps candidate profile values to detected form fields without hallucinating', () => {
    const mockProfile: CandidateProfile = {
      candidate_id: 'usr-1',
      full_name: 'Utkarsh Shah',
      first_name: 'Utkarsh',
      last_name: 'Shah',
      email: 'utkarsh@example.com',
      phone: '+91 99999 88888',
      location: 'Bengaluru, India',
      headline: 'Full-Stack Developer',
      summary: 'Experienced developer',
      linkedin_url: 'https://linkedin.com/in/utkarshshah',
      github_url: 'https://github.com/utkarshshah',
      education: [],
      skills: ['Python', 'FastAPI', 'React', 'Docker'],
      experience: [],
      projects: [],
      work_authorization: 'Yes',
      requires_sponsorship: 'No'
    };

    const detectedFields = FormMapper.extractFormFields(doc);
    const actionPlan = FormMapper.mapCandidateToForm(detectedFields, mockProfile);

    expect(actionPlan.fields_to_fill.length).toBeGreaterThanOrEqual(5);

    const nameAction = actionPlan.fields_to_fill.find(f => f.field_id === 'full_name');
    expect(nameAction?.value).toBe('Utkarsh Shah');

    const emailAction = actionPlan.fields_to_fill.find(f => f.field_id === 'email');
    expect(emailAction?.value).toBe('utkarsh@example.com');

    // Missing profile keys should not be fabricated
    const gpaAction = actionPlan.fields_to_fill.find(f => f.field_id === 'gpa');
    expect(gpaAction).toBeUndefined();
  });

  it('identifies unmapped required fields during form validation', () => {
    const fields = FormMapper.extractFormFields(doc);
    const validation = FormMapper.validateForm(fields);

    // Form has unfilled required name, email, resume
    expect(validation.unfilled_required_fields.length).toBeGreaterThanOrEqual(1);
    expect(validation.is_valid).toBe(false);
  });
});
