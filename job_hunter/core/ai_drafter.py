import anthropic


SYSTEM_PROMPT = """You are an expert career coach and email writer. You draft cold outreach emails
for job applications that are:
- Concise (under 200 words for the body)
- Professional but warm
- Specifically tailored to the job description
- Highlighting the most relevant skills from the candidate's resume
- Including a clear call to action
- NOT generic or template-sounding

You return JSON with exactly two keys: "subject" and "body".
The body should NOT include the subject line.
The body should end with the candidate's name and contact info.
Do not use markdown formatting in the email body — plain text only."""


def draft_email(
    job_title: str,
    company: str,
    job_description: str,
    resume_text: str,
    candidate_name: str,
    candidate_email: str,
    candidate_linkedin: str,
    api_key: str,
) -> dict:
    client = anthropic.Anthropic(api_key=api_key)

    user_prompt = f"""Draft a personalized cold email for this job application.

JOB TITLE: {job_title}
COMPANY: {company or 'Unknown'}
JOB DESCRIPTION:
{job_description[:3000]}

CANDIDATE RESUME:
{resume_text[:4000]}

CANDIDATE INFO:
- Name: {candidate_name}
- Email: {candidate_email}
- LinkedIn: {candidate_linkedin}

Return valid JSON with "subject" and "body" keys only. No markdown."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    import json
    text = response.content[0].text
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        return json.loads(text[start:end])

    return {
        "subject": f"Application for {job_title} - {candidate_name}",
        "body": text,
    }
