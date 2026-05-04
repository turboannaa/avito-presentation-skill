from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/presentations',
    'https://www.googleapis.com/auth/drive'
]

TEMPLATE_ID = '1rSns7QMIMcMAfh77gGQK9V878caYyWLJxJ7WJ55DbCA'

creds = Credentials.from_authorized_user_file('token.json', SCOPES)
service = build('slides', 'v1', credentials=creds)

presentation = service.presentations().get(
    presentationId=TEMPLATE_ID
).execute()

slides = presentation.get('slides', [])
print(f"Слайдов в шаблоне: {len(slides)}\n")

for i, slide in enumerate(slides):
    slide_id = slide['objectId']
    elements = slide.get('pageElements', [])
    print(f"Слайд {i+1} (id: {slide_id})")
    print(f"  Элементов: {len(elements)}")

    for el in elements:
        if 'shape' in el and 'text' in el.get('shape', {}):
            texts = el['shape']['text']['textElements']
            text = ''.join(
                t.get('textRun', {}).get('content', '')
                for t in texts
            ).strip()
            if text:
                print(f"  Текст: {text[:80]}")
    print()
