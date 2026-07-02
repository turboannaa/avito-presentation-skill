# Avito Presentation Skill — Agent Instructions

This repository contains a skill for creating Avito-branded Google Slides presentations.
When the user asks to create a presentation, deck, or slides — follow the instructions below exactly.

---

## Setup check (run once per environment)

Before creating any presentation, verify the environment is ready:

```bash
# Check Python dependencies
python3 -c "import googleapiclient, google.oauth2" 2>/dev/null || pip3 install google-api-python-client google-auth google-auth-oauthlib

# Check that Google token exists
ls google_token.json 2>/dev/null || echo "MISSING: run python3 scripts/auth.py first"
```

If `google_token.json` is missing, tell the user to run `python3 scripts/auth.py` locally and commit the resulting token — the agent cannot complete browser-based OAuth.

---

## How to create a presentation

### Step 1 — Understand the request

From the user's message, determine:
- **Topic** of the presentation
- **Number of slides** (default: 8–12 if not specified)
- **Speaker name and role** for the title slide
- **Source document** — if the user provides a file or URL, read it carefully and use its exact content

### Step 2 — Choose slide layouts

Pick layouts that fit the content type:

| Template ID | When to use |
|-------------|-------------|
| `p` | Title slide (always first) |
| `g344d1e4037f_7_331` | Section divider / chapter break |
| `g344d1e4037f_7_389` | Single key message, no graphic |
| `g344d1e4037f_7_579` | Single key message with graphic (prefer this over _389 to avoid text overlap) |
| `g344d1e4037f_7_344` | 2 numbered points with descriptions |
| `g344d1e4037f_7_374` | 3 numbered points with descriptions |
| `g344d1e4037f_7_1169` | 4 numbered blocks with descriptions |
| `g344d1e4037f_7_522` | 3 bullet points (format: `"Title\nDescription"`) |
| `g344d1e4037f_7_1069` | Pros and cons (left 5 items / right 5 items) |
| `g344d1e4037f_7_1448` | 3 key stats / numbers |
| `g344d1e4037f_7_403` | Title + description left + **large image right** |
| `g344d1e4037f_7_2026` | Contacts / Q&A (always last) |

**Rules:**
- Use `_374` (3 points) or `_1169` (4 blocks) for most content — they're the most versatile
- Use `_403` only when there is an actual image to show (`image_url` provided or a screenshot to insert)
- Use `_522` when items are bullets with sub-descriptions, not numbered steps
- Use `_1448` only when there are exactly 3 key numbers/metrics

### Step 3 — Write content

Keep text concise — these are slides, not documents:
- Titles: 4–7 words
- Descriptions: 1–2 sentences per block (max ~120 characters)
- Bullet points: 1 line each

### Step 4 — Build plan.json

Write the complete plan to `plan.json`. Format:

```json
{
  "title": "Presentation title",
  "slides": [
    {
      "template_id": "TEMPLATE_ID",
      "description": "Short description of this slide",
      "element_replacements": {
        "ELEMENT_ID": "Text content"
      },
      "image_url": "https://publicly-accessible-url.com/image.png",
      "delete_elements": ["ELEMENT_ID_TO_REMOVE"]
    }
  ]
}
```

**Element IDs by template:**

**Title slide (`p`):**
```
g3a04f21b846_0_0  — main title
g3a04f21b846_0_1  — subtitle
g3a04f21b846_0_2  — speaker 1 name
g3a04f21b846_0_4  — speaker 1 role
g3a04f21b846_0_3  — speaker 2 name (set "" if unused)
g3a04f21b846_0_5  — speaker 2 role (set "" if unused)
```

**Section divider (`_331`):**
```
g3a04f21b846_0_5252  — section title (use \n for line break)
```

**Key message no graphic (`_389`):**
```
g3a04f21b846_0_5283  — big text
g3a04f21b846_0_5282  — comment / explanation
```

**Key message graphic bottom-right (`_579`):**
```
g3a04f21b846_0_5442  — big text
g3a04f21b846_0_5441  — comment / explanation
```

**2 numbered points (`_344`):**
```
g3a04f21b846_0_5268  — title
g3a04f21b846_0_5261  — subtitle
g3a04f21b846_0_5262  — point 1 title
g3a04f21b846_0_5263  — point 1 description
g3a04f21b846_0_5264  — point 2 title
g3a04f21b846_0_5265  — point 2 description
```

**3 numbered points (`_374`):**
```
g3a04f21b846_0_5271  — title
g3a04f21b846_0_5270  — subtitle
g3a04f21b846_0_5275  — point 1 title
g3a04f21b846_0_5276  — point 1 description
g3a04f21b846_0_5277  — point 2 title
g3a04f21b846_0_5278  — point 2 description
g3a04f21b846_0_5279  — point 3 title
g3a04f21b846_0_5280  — point 3 description
```

**4 numbered blocks (`_1169`):**
```
g3a04f21b846_0_5887  — block 1 title
g3a04f21b846_0_5888  — block 1 description
g3a04f21b846_0_5889  — block 2 title
g3a04f21b846_0_5890  — block 2 description
g3a04f21b846_0_5891  — block 3 title
g3a04f21b846_0_5892  — block 3 description
g3a04f21b846_0_5893  — block 4 title
g3a04f21b846_0_5894  — block 4 description
```

**3 bullet points (`_522`):**
```
g3a04f21b846_0_5373  — title
g3a04f21b846_0_5374  — subtitle
g3a04f21b846_0_5375  — bullet 1 ("Title\nDescription")
g3d7faa4bf74_1_67    — bullet 2 ("Title\nDescription")
g3d7faa4bf74_1_68    — bullet 3 ("Title\nDescription")
```

**Pros and cons (`_1069`):**
```
g3a04f21b846_0_5789  — left column header
g3a04f21b846_0_5800  — right column header
Left column (top→bottom):  5794, 5793, 5790, 5792, 5791
Right column (top→bottom): 5799, 5798, 5797, 5796, 5795
```
Max ~15 characters per item. Prefix with full element ID: `g3a04f21b846_0_5794`.

**3 key stats (`_1448`):**
```
g3a04f21b846_0_6036  — slide title
g3a04f21b846_0_6037  — stat 1 number
g3a04f21b846_0_6034  — stat 1 label
g3a04f21b846_0_6033  — stat 1 description
g3a04f21b846_0_6038  — stat 2 number
g3a04f21b846_0_6032  — stat 2 label
g3a04f21b846_0_6040  — stat 2 description
g3a04f21b846_0_6039  — stat 3 number
g3a04f21b846_0_6035  — stat 3 label
g3a04f21b846_0_6041  — stat 3 description
```

**Title + image right (`_403`):**
```
g3a04f21b846_0_5286  — title
g3a04f21b846_0_5285  — subtitle
g3a04f21b846_0_5287  — description text
image_url             — publicly accessible direct image URL
```
Do NOT include `g3a04f21b846_0_5288` in element_replacements when image_url is set.

**Contacts (`_2026`):**
```
g3a04f21b846_0_6436  — heading (e.g. "Вопросы?")
g3a04f21b846_0_6437  — subheading
g3a04f21b846_0_6440  — speaker name
g3a04f21b846_0_6439  — speaker title / role
g3a04f21b846_0_6441  — contact (Telegram or email)
delete_elements: ["g3a088af7fa0_0_7", "g3a088af7fa0_0_8"]  — remove both icons if no contact
```

### Step 5 — Run the script

```bash
python3 scripts/create_presentation.py plan.json
```

The script prints a Google Slides link on success. Give this link to the user.

If the token is expired, the script will throw `invalid_grant`. Tell the user to run `python3 scripts/auth.py` and try again.

---

## Image handling

- `image_url` must be a **publicly accessible** direct URL (no login, no redirect)
- Google Drive share links do NOT work — use `https://drive.google.com/uc?export=download&id=FILE_ID`
- If the user provides a source Google Slides presentation and wants diagrams inserted as screenshots:
  1. Use the Slides API to get thumbnails: `presentations().pages().getThumbnail(...)`
  2. Download each thumbnail and upload to Drive with public read permission
  3. Use the resulting Drive download URL as `image_url`

---

## Source presentation workflow

When the user provides a Google Slides URL as source:

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

creds = Credentials.from_authorized_user_file('google_token.json',
    ['https://www.googleapis.com/auth/presentations',
     'https://www.googleapis.com/auth/drive'])
service = build('slides', 'v1', credentials=creds)
pres = service.presentations().get(presentationId='PRESENTATION_ID').execute()

for i, slide in enumerate(pres['slides']):
    for elem in slide.get('pageElements', []):
        text = elem.get('shape', {}).get('text', {})
        content = ''.join(r.get('textRun', {}).get('content', '') for r in text.get('textElements', []))
        if content.strip():
            print(f'Slide {i+1}: {content[:200]}')
```

---

## Важно / Important

- Do not commit `google_token.json`, `google_credentials.json`, or `credentials.json` — they are personal OAuth tokens
- Do not include personal user data or confidential corporate information in presentations — content goes through the Google Slides API
- The template ID is hardcoded in `scripts/create_presentation.py` — do not change it
