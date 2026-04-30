"""Показывает ВСЕ элементы слайда (включая картинки, иконки, линии)."""
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/presentations']
TEMPLATE_ID = '1rSns7QMIMcMAfh77gGQK9V878caYyWLJxJ7WJ55DbCA'

TARGET = [
    "g344d1e4037f_7_2026",  # контакты
    "p",                    # титульный
]

creds = Credentials.from_authorized_user_file('token.json', SCOPES)
service = build('slides', 'v1', credentials=creds)
pres = service.presentations().get(presentationId=TEMPLATE_ID).execute()

for slide in pres.get('slides', []):
    if slide['objectId'] not in TARGET:
        continue
    print(f"\n{'='*60}")
    print(f"СЛАЙД: {slide['objectId']}")
    print('='*60)

    for el in slide.get('pageElements', []):
        obj_id = el['objectId']
        t = el.get('transform', {})
        x = round(t.get('translateX', 0) / 914400 * 2.54, 1)
        y = round(t.get('translateY', 0) / 914400 * 2.54, 1)
        size = el.get('size', {})
        w = round(size.get('width', {}).get('magnitude', 0) / 914400 * 2.54, 1)
        h = round(size.get('height', {}).get('magnitude', 0) / 914400 * 2.54, 1)

        if 'shape' in el:
            shape_type = el['shape'].get('shapeType', 'UNKNOWN')
            text = ''
            if 'text' in el['shape']:
                text = ''.join(
                    te.get('textRun', {}).get('content', '')
                    for te in el['shape']['text']['textElements']
                ).strip()[:60]
            print(f"  SHAPE [{obj_id}] type={shape_type}")
            print(f"    pos: ({x},{y}) size: {w}×{h} cm")
            if text:
                print(f"    текст: {text!r}")

        elif 'image' in el:
            src = el['image'].get('contentUrl', '')[:80]
            print(f"  IMAGE [{obj_id}]")
            print(f"    pos: ({x},{y}) size: {w}×{h} cm")
            print(f"    src: {src}")

        elif 'line' in el:
            print(f"  LINE  [{obj_id}] pos: ({x},{y}) size: {w}×{h} cm")

        elif 'elementGroup' in el:
            print(f"  GROUP [{obj_id}] pos: ({x},{y}) size: {w}×{h} cm")

        else:
            print(f"  OTHER [{obj_id}] keys={list(el.keys())}")
