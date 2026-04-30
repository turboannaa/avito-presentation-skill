"""
Показывает детальную структуру нужных слайдов шаблона:
objectId каждого элемента, его текст и размер блока.
"""
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/presentations',
    'https://www.googleapis.com/auth/drive'
]

TEMPLATE_ID = '1rSns7QMIMcMAfh77gGQK9V878caYyWLJxJ7WJ55DbCA'

# Слайды которые используем в презентации
TARGET_SLIDE_IDS = [
    "p",                        # титульный
    "g36d6423304e_1_0",         # спикер
    "g344d1e4037f_7_389",       # важная мысль 1
    "g344d1e4037f_7_374",       # 3 нумерованных пункта
    "g344d1e4037f_7_566",       # важная мысль 2
    "g344d1e4037f_7_522",       # 3 буллета без картинки
    "g344d1e4037f_7_331",       # раздел
    "g344d1e4037f_7_344",       # 2 нумерованных пункта
    "g344d1e4037f_7_1169",      # 4 нумерованных блока
    "g344d1e4037f_7_1069",      # плюсы/минусы
    "g344d1e4037f_7_1448",      # 3 важные цифры
    "g344d1e4037f_7_2026",      # контакты 1
]

creds = Credentials.from_authorized_user_file('token.json', SCOPES)
service = build('slides', 'v1', credentials=creds)

pres = service.presentations().get(presentationId=TEMPLATE_ID).execute()
slides = pres.get('slides', [])

for slide in slides:
    slide_id = slide['objectId']
    if slide_id not in TARGET_SLIDE_IDS:
        continue

    print(f"\n{'='*60}")
    print(f"СЛАЙД: {slide_id}")
    print('='*60)

    for el in slide.get('pageElements', []):
        obj_id = el['objectId']
        # размер блока (в EMU, делим на 914400 для дюймов, на ~36000 для ~символов)
        size = el.get('size', {})
        w = size.get('width', {}).get('magnitude', 0)
        h = size.get('height', {}).get('magnitude', 0)
        w_cm = round(w / 914400 * 2.54, 1)
        h_cm = round(h / 914400 * 2.54, 1)

        if 'shape' in el and 'text' in el.get('shape', {}):
            text_runs = []
            for te in el['shape']['text']['textElements']:
                content = te.get('textRun', {}).get('content', '')
                if content.strip():
                    text_runs.append(content.strip())
            text = ' | '.join(text_runs)[:100]

            # примерная вместимость в символах (очень грубо по ширине)
            capacity = int(w_cm * 8)

            print(f"  [{obj_id}]")
            print(f"    размер: {w_cm}×{h_cm} см (~{capacity} симв)")
            print(f"    текст:  {text!r}")
