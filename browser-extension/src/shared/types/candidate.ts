/**
 * Candidate Profile Types
 * Standard normalized candidate attributes mapped to job application form fields.
 */

export interface CandidateEducation {
  institution: string;
  degree?: string;
  field_of_study?: string;
  graduation_year?: string;
  gpa?: string;
}

export interface CandidateExperience {
  company: string;
  role: string;
  start_date?: string;
  end_date?: string;
  description?: string;
}

export interface CandidateProject {
  title: string;
  technologies?: string;
  description?: string;
  link?: string;
}

export interface ActiveResumeRef {
  resume_id: string;
  pdf_url: string;
  latex_url?: string;
  file_name: string;
}

export interface CandidateProfile {
  candidate_id: string;
  full_name: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  location: string;
  headline: string;
  summary: string;
  linkedin_url?: string;
  github_url?: string;
  portfolio_url?: string;
  work_authorization?: string;
  requires_sponsorship?: string;
  education: CandidateEducation[];
  experience: CandidateExperience[];
  skills: string[];
  projects: CandidateProject[];
  active_resume?: ActiveResumeRef;
}

export type CandidateProfileKey =
  | 'full_name'
  | 'first_name'
  | 'last_name'
  | 'email'
  | 'phone'
  | 'location'
  | 'headline'
  | 'summary'
  | 'linkedin_url'
  | 'github_url'
  | 'portfolio_url'
  | 'work_authorization'
  | 'requires_sponsorship'
  | 'institution'
  | 'degree'
  | 'graduation_year'
  | 'gpa'
  | 'skills'
  | 'cover_letter'
  | 'resume_file';

