---
name: avito-presentation-skill
description: Creates Avito-branded Google Slides presentations from a template. Use when the user asks to create a presentation, deck, or slides on any topic. The skill selects appropriate slide layouts, writes content, and generates a ready-to-use Google Slides link automatically.
license: Proprietary
compatibility: Requires Python 3.9+, google-api-python-client, google-auth. Needs Google OAuth token (token.json) and credentials (credentials.json) set up via auth.py. Internet access required.
metadata:
  author: anndreevva
  version: "1.0"
allowed-tools: Bash Read Write
---

# Avito Presentation Skill

Creates a Google Slides presentation using the Avito DevRel template. The user provides a topic — the skill handles slide selection, content writing, and assembly.

## How it works

1. User describes the topic and approximate number of slides
2. The skill writes content and builds `plan.json` — a structured description of each slide
3. The script `create_presentation.py` uses Google Slides API to copy the template, remove unused slides, and fill in the content
4. The user receives a link to the finished presentation in Google Drive

## Available slide layouts

| Template ID | Layout |
|-------------|--------|
| `p` | Title slide |
| `g36d6423304e_1_0` | Speaker intro |
| `g344d1e4037f_7_331` | Section divider |
| `g344d1e4037f_7_389` | Key message (no graphic) |
| `g344d1e4037f_7_579` | Key message (graphic bottom-right) |
| `g344d1e4037f_7_344` | 2 numbered points |
| `g344d1e4037f_7_374` | 3 numbered points |
| `g344d1e4037f_7_1169` | 4 numbered blocks |
| `g344d1e4037f_7_522` | 3 bullet points |
| `g344d1e4037f_7_1069` | Pros and cons |
| `g344d1e4037f_7_1448` | 3 key numbers/stats |
| `g344d1e4037f_7_2026` | Contacts / Q&A |

## plan.json format

```json
{
  "title": "Presentation title",
  "slides": [
    {
      "template_id": "p",
      "description": "Title slide",
      "element_transforms": {
        "ELEMENT_ID": {"translateX": 154550, "translateY": 2520000}
      },
      "element_replacements": {
        "ELEMENT_ID": "Text to insert"
      },
      "delete_elements": ["ELEMENT_ID_TO_DELETE"]
    }
  ]
}
```

## Step-by-step instructions

### Step 1 — Understand the request

Ask the user (or infer from context):
- Topic of the presentation
- Number of slides (typically 6–12)
- Speaker name, title, and contact (Telegram or email) for the contacts slide
- Whether a speaker intro slide is needed

### Step 2 — Choose slide layouts

Select layouts that best fit the content. Recommended structure:
- Slide 1: Title (`p`)
- Slide 2: Speaker intro (optional, `g36d6423304e_1_0`)
- Slides 3–N: Content slides (choose from the table above based on content type)
- Last slide: Contacts (`g344d1e4037f_7_2026`)

**Layout selection rules:**
- Use key message slides (`_389` or `_579`) for important quotes or conclusions — prefer `_579` (graphic bottom-right) to avoid text overlapping the graphic
- Use numbered layouts for sequential steps or distinct categories
- Use pros/cons (`_1069`) for comparisons — left column 5 items, right column 5 items, max ~15 characters per item
- Use stats slide (`_1448`) when there are 3 key metrics or numbers

### Step 3 — Write content

Keep text short — these are presentation slides, not documents:
- Titles: 4–7 words
- Body text: 1–2 sentences per block
- Bullet points: 1 line each

### Step 4 — Build plan.json

Write the complete `plan.json` to disk. Use these element IDs:

**Title slide (p):**
- `g3a04f21b846_0_0` — main title
- `g3a04f21b846_0_1` — subtitle (move down: `translateY: 2520000`)
- `g3a04f21b846_0_2`, `_0_4` — speaker 1 name, role
- `g3a04f21b846_0_3`, `_0_5` — speaker 2 name, role (set to `""` if unused)

**Key message slides (_389 and _579):**
- Big text: `g3a04f21b846_0_5283` (slide _389) / `g3a04f21b846_0_5442` (slide _579)
  - Transform: `{"translateX": 154550, "translateY": 720000, "scaleX": 3.0, "scaleY": 1.2}`
- Comment: `g3a04f21b846_0_5282` (slide _389) / `g3a04f21b846_0_5441` (slide _579)
  - Transform: `{"translateX": 199900, "translateY": 3240000, "scaleX": 1.5, "scaleY": 1.8}`

**3 numbered points (_374):**
- `g3a04f21b846_0_5271` — title, `g3a04f21b846_0_5270` — subtitle
- `g3a04f21b846_0_5275/5277/5279` — point titles
- `g3a04f21b846_0_5276/5278/5280` — point descriptions

**2 numbered points (_344):**
- `g3a04f21b846_0_5268` — title, `g3a04f21b846_0_5261` — subtitle
- `g3a04f21b846_0_5262/5264` — point titles
- `g3a04f21b846_0_5263/5265` — point descriptions

**4 numbered blocks (_1169):**
- `g3a04f21b846_0_5887/5889/5891/5893` — block titles
- `g3a04f21b846_0_5888/5890/5892/5894` — block descriptions

**3 bullet points (_522):**
- `g3a04f21b846_0_5373` — title, `g3a04f21b846_0_5374` — subtitle
- `g3a04f21b846_0_5375` — bullet 1 (format: `"Title\nDescription"`)
- `g3d7faa4bf74_1_67` — bullet 2
- `g3d7faa4bf74_1_68` — bullet 3

**Pros and cons (_1069):**
- `g3a04f21b846_0_5789` — left header, `g3a04f21b846_0_5800` — right header
- Left column top→bottom: `5794`, `5793`, `5790`, `5792`, `5791`
- Right column top→bottom: `5799`, `5798`, `5797`, `5796`, `5795`

**3 stats (_1448):**
- `g3a04f21b846_0_6036` — slide title
- `g3a04f21b846_0_6037/6038/6039` — numbers
- `g3a04f21b846_0_6034/6032/6035` — stat labels
- `g3a04f21b846_0_6033/6040/6041` — stat descriptions
- Transforms for labels: `{"translateX": X, "translateY": 1958400, "scaleX": 1, "scaleY": 1.8}`
- Transforms for descriptions: `{"translateX": X, "translateY": 2772000}`
- X values: 165600 (col 1), 3067200 (col 2), 5986800 (col 3)

**Contacts (_2026):**
- `g3a04f21b846_0_6436` — heading ("Вопросы?")
- `g3a04f21b846_0_6437` — subheading (move: `{"translateX": 183525, "translateY": 1620000}`)
- `g3a04f21b846_0_6440` — speaker name
- `g3a04f21b846_0_6439` — speaker title
- `g3a04f21b846_0_6441` — contact (Telegram or email)
- If only Telegram: `"delete_elements": ["g3a088af7fa0_0_8"]` (removes email icon)
- If only email: `"delete_elements": ["g3a088af7fa0_0_7"]` (removes Telegram icon)

### Step 5 — Run the script

```bash
python3 scripts/create_presentation.py plan.json
```

The script will output a Google Slides link. Share it with the user.

## Setup (one-time)

See [README.md](README.md) for full installation and Google API setup instructions.
