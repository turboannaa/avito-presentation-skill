from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/presentations',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents.readonly'
]

DOC_ID = '1IsUPac0W86lbblq1eqaVTigHfd0JVyEp2IrraquXt2w'

creds = Credentials.from_authorized_user_file('token.json', SCOPES)
docs_service = build('docs', 'v1', credentials=creds)

doc = docs_service.documents().get(documentId=DOC_ID).execute()

text = ''
for element in doc.get('body', {}).get('content', []):
    for para_el in element.get('paragraph', {}).get('elements', []):
        text += para_el.get('textRun', {}).get('content', '')

with open('tz.txt', 'w', encoding='utf-8') as f:
    f.write(text)

print("Готово! Текст сохранён в tz.txt")
print(f"Символов: {len(text)}")
print("\nПервые 500 символов:")
print(text[:500])
