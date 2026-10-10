# yaml-latex-cv-generator

Generating CVs and cover letters for job applications from one bilingual content source.

## Terms

**`variant`**: A CV version for a type of role (`developer`, `general`) built from the same content; defined in `variants/`.
_Do not confuse with_: `application` (one concrete job application).

**`application`**: A per-application override file in `applications/` that tailors title, summary, order and letter for one job.
_Related_: `APP_KEYS`, fact.

**fact**: Content that an application may never override: employers, roles, dates, education.

**language pair**: A `{en, hu}` value; both languages are required.

**variant value**: A `{"@developer": ..., "@general": ...}` value that differs by variant.

**`tags`**: The variants in which a CV item appears.

**fallback letter**: The cover letter body per variant in `content/cover_letter.yaml`, used when an application gives no `letter.body`.
