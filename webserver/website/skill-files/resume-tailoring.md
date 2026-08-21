---
name: resume-tailoring
description: Use this when the user wants to modify or create a resume.
---

## Context

This skill is used to modify, tailor, or create a new resume. Your task is to rewrite a user's entire resume to perfectly align with the target Job Description.

You must maintain strict honesty—do not invent new metrics, job titles, or technologies that the user does not possess. Focus entirely on rephrasing and keyword-matching.

## INSTRUCTIONS

1. **KEYWORD ALIGNMENT:**
    - Identify the primary technical skills, methodologies, and action verbs in the [TARGET JOB DESCRIPTION].
    - Weave these exact keywords into the user's Summary, Experience, Projects, and Skills sections where applicable.
2. **RE-PRIORITIZE BULLET POINTS:**
    - For each job role and project, move the bullet points that are most relevant to the [TARGET JOB DESCRIPTION] to the very top.
    - De-emphasize or shorten bullet points that are completely irrelevant to the target role.
3. **TONE AND STRUCTURE:**
    - Use strong, active verbs to start every bullet point (e.g., "Led," "Developed," "Optimized").
    - Keep sentences punchy and concise. Do not use passive language.
    - Maintain a professional, executive tone.
4. **CRITICAL RULES:**
    - Do NOT add certifications, degrees, or company names the user does not have.
    - Do NOT invent metrics (e.g., do not change "increased sales" to "increased sales by 45%" unless the user provided that number).
    - Use job experience provided in the user resume ONLY. **DO NOT** copy job experience from the target job description.

## OUTPUT FORMAT

Your output must contain ONLY the final tailored resume in clean Markdown. Adhere to the format given below. Do not include conversational filler like "Here is your tailored resume." Start immediately with the resume content.

Use the following strict structure:

# [User Name]
[Contact Info: Phone | Email | Github]

## Profile Summary
[A 3-4 sentence paragraph tailored to the target role. Highlight years of experience, core expertise matching the JD, and 1-2 major achievements.]

## Technical Skills
[INSTRUCTION FOR MODEL: Dynamically choose between 2 to 4 relevant categories from the list below based on the JD. Delete categories that do not apply. Do not create categories outside of this list unless strictly required by the JD.]

* **Software & Languages:** [e.g., Python, C++, ROS, MATLAB, PLC Programming - if applicable]
* **Mechanical & Hardware Design:** [e.g., CAD/SolidWorks, FEA, GD&T, Prototyping - if applicable]
* **Electrical & Embedded Systems:** [e.g., PCB Design, Altium, Microcontrollers, LabVIEW - if applicable]
* **Tools, Databases & Cloud:** [e.g., AWS, Git, Docker, Linux, JIRA - if applicable]
* **Methodologies & Testing:** [e.g., Agile, DevOps, Root Cause Analysis, DFM/DFA - if applicable]

## Work Experience
[INSTRUCTION FOR MODEL: Replicate the block below for EVERY job role listed in the user's CURRENT RESUME. Do not omit any relevant historical roles. Do NOT use the job titles or companies from the Target Job Description here. List 2-4 tailored sentences for each job. For less relevant jobs, reduce the sentences to make more room. Minimize descriptions that overlap in skill use when possible.]

### [Job Title from Current Resume] | [Company Name from Current Resume] | [Location] | [Start-End Date]
* [Tailored sentence describing various skills used]
* [Tailored sentence describing various skills used]
* [Tailored sentence describing various skills used]

## Projects
[INSTRUCTION FOR MODEL: Replicate the block below for EVERY project listed in the user's CURRENT RESUME. Do not drop projects unless they are completely blank or make the resume too long. For each project, list 3-5 tailored sentences. Minimize descriptions that overlap in skill use when possible.]

### [Project Title from Current Resume] | [List 5 most relevant skills used] | [Start-End Date]
* [tailored sentence describing various skills used]
* [tailored sentence describing various skills used]
* [tailored sentence describing various skills used]

## Education
### [University Name] | [Graduation Year]
* [Degree/Major]

## Certifications
* [Certification Name] | [Year of acquirement]

---
=========================================
      STOP HERE. DATA INGESTION BELOW.
=========================================
---

## INPUT DATA
[CRITICAL: Read the data below. The output resume must be built entirely out of the text in the CURRENT RESUME section, optimized using keywords from the TARGET JOB DESCRIPTION.]

[TARGET JOB DESCRIPTION]:
[To be pasted by user]

[CURRENT RESUME]:
[To be pasted by user]