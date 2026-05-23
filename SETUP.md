# Job Hunter - Automated Job Application Tool

An automated pipeline that scans job boards and LinkedIn hiring posts, extracts contact emails, drafts personalized application emails using AI, and sends them with your resume attached.

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│                    JOB SOURCES                          │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│ Remotive │ Adzuna   │ Arbeitnow│ The Muse │ RSS Feeds   │
│ (free)   │ (free)   │ (free)   │ (free)   │ (free)      │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│              LINKEDIN POST FINDERS                      │
├──────────┬──────────┬───────────────────────────────────┤
│ Google   │ SerpAPI  │ LinkedIn Email Alerts (Gmail)     │
│ Search   │          │ (parse job alert emails)          │
├──────────┴──────────┴───────────────────────────────────┤
│              MANUAL SOURCES                             │
├─────────────────────────────────────────────────────────┤
│ Paste file (job_posts.txt) │ CLI paste command          │
└───────────────┬─────────────────────────────────────────┘
                │
                ▼
        ┌───────────────┐
        │ Email Extractor│──── Finds emails in job descriptions
        └───────┬───────┘
                │
                ▼
        ┌───────────────┐
        │  AI Drafter   │──── Claude drafts personalized email
        └───────┬───────┘
                │
                ▼
        ┌───────────────┐
        │  Email Sender │──── Sends via Gmail + resume attachment
        └───────────────┘
```

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up your resume
Place your resume PDF as `resume.pdf` in the project root.
Create a text version for AI processing:
```bash
# Option A: manually create resume.txt with your resume content
# Option B: extract from PDF
pip install pymupdf
python -c "import fitz; doc=fitz.open('resume.pdf'); open('resume.txt','w').write(''.join(p.get_text() for p in doc))"
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 4. Run
```bash
# Single scan (dry run - no emails sent)
python -m job_hunter run

# Single scan (live - drafts + sends emails)
python -m job_hunter run --live --auto-send

# Continuous scanning every 60 minutes
python -m job_hunter loop

# Paste a LinkedIn post manually
python -m job_hunter paste

# Review drafted emails before sending
python -m job_hunter review --send

# Check stats
python -m job_hunter stats
```

## API Keys Setup (Priority Order)

### Must Have
1. **Anthropic API Key** - For AI email drafting
   - Get it at: https://console.anthropic.com/
   - Cost: ~$0.01 per email drafted

### Highly Recommended (LinkedIn Post Discovery)
2. **SerpAPI Key** OR **Google Custom Search API**
   - SerpAPI: https://serpapi.com/ (100 free searches/month)
   - Google CSE: https://programmablesearchengine.google.com/ (100 free queries/day)
   - These find LinkedIn "I'm hiring" posts with email addresses

### Optional (More Job Sources)
3. **Adzuna API** - https://developer.adzuna.com/ (250 free requests/month)
4. **Gmail IMAP** - For parsing LinkedIn job alert emails
   - Enable at: https://myaccount.google.com/apppasswords

### Email Sending
5. **Gmail App Password** - For sending application emails
   - Create at: https://myaccount.google.com/apppasswords
   - Requires 2FA enabled on your Google account

## LinkedIn Hiring Post Strategy

Since LinkedIn's API is locked down, we use these approaches to find hiring posts:

1. **Google/SerpAPI Search** - Searches `site:linkedin.com/posts` for hiring-related keywords with email addresses
2. **LinkedIn Job Alerts → Email** - Set up job alerts on LinkedIn, they email you, we parse those emails
3. **Manual Paste** - When you spot a good post while scrolling, copy-paste it

### Maximizing LinkedIn Post Coverage

On LinkedIn, set up job alerts for:
- "AI Engineer"
- "Machine Learning"
- "Data Scientist"
- "Python Developer"
- Your other target roles

Set alert frequency to "Daily" so we get fresh posts every day.

## Commands

| Command | Description |
|---------|-------------|
| `python -m job_hunter run` | Run one scan cycle (dry run) |
| `python -m job_hunter run --live` | Run one scan cycle (live) |
| `python -m job_hunter run --auto-send` | Scan + auto-send emails |
| `python -m job_hunter loop` | Continuous scanning |
| `python -m job_hunter paste` | Process a pasted job post |
| `python -m job_hunter review` | Review drafted emails |
| `python -m job_hunter review --send` | Review + option to send |
| `python -m job_hunter stats` | Show statistics |

## Modes

- **Dry Run** (default): Scans and drafts emails but doesn't send them
- **Live**: Drafts emails and saves them for review
- **Auto-send**: Drafts and sends emails automatically

## Safety Features

- Deduplication: Never processes the same job twice
- Email blacklist: Filters out noreply, system, and generic addresses
- Rate limiting: Configurable max emails per run
- Dry run default: Won't send anything until you explicitly enable it
- Review mode: Check every email before sending
