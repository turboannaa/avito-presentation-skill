"""Показывает точные позиции и размеры элементов через transform + size."""
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/presentations']
TEMPLATE_ID = '1rSns7QMIMcMAfh77gGQK9V878caYyWLJxJ7WJ55DbCA'
EMU = 914400  # EMU per inch
CM = EMU / 2.54

TARGET = ["p", "g344d1e4037f_7_2026", "g344d1e4037f_7_389", "g344d1e4037f_7_566",
          "g344d1e4037f_7_374", "g344d1e4037f_7_344", "g344d1e4037f_7_522",
          "g344d1e4037f_7_1069", "g344d1e4037f_7_1448", "g344d1e4037f_7_1169",
          "g36d6423304e_1_0"]

creds = Credentials.from_authorized_user_file('token.json', SCOPES)
service = build('slides', 'v1', credentials=creds)
pres = service.presentations().get(presentationId=TEMPLATE_ID).execute()

slide_w = pres['pageSize']['width']['magnitude']
slide_h = pres['pageSize']['height']['magnitude']
print(f"Слайд: {slide_w/CM:.1f} × {slide_h/CM:.1f} см ({slide_w} × {slide_h} EMU)\n")

for slide in pres.get('slides', []):
    if slide['objectId'] not in TARGET:
        continue
    print(f"\n{'='*70}")
    print(f"СЛАЙД: {slide['objectId']}")
    print('='*70)

    for el in slide.get('pageElements', []):
        obj_id = el['objectId']
        t = el.get('transform', {})
        sx = t.get('scaleX', 1)
        sy = t.get('scaleY', 1)
        tx = t.get('translateX', 0)
        ty = t.get('translateY', 0)
        s = el.get('size', {})
        ew = s.get('width', {}).get('magnitude', 0)
        eh = s.get('height', {}).get('magnitude', 0)
        # visual size in cm
        vw = round(ew * sx / CM, 2)
        vh = round(eh * sy / CM, 2)
        x = round(tx / CM, 2)
        y = round(ty / CM, 2)

        shape = el.get('shape', {})
        text = ''
        if 'text' in shape:
            text = ''.join(
                te.get('textRun', {}).get('content', '')
                for te in shape['text']['textElements']
            ).strip()[:50]

        kind = 'TEXT' if text else ('IMG' if 'image' in el else 'SHAPE')
        print(f"  [{obj_id}] {kind}")
        print(f"    pos: x={x} y={y} cm | size: {vw}×{vh} cm")
        print(f"    emu: tx={int(tx)} ty={int(ty)} w={int(ew*sx)} h={int(eh*sy)}")
        if text:
            print(f"    текст: {text!r}")
