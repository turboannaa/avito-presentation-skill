"""
Создаёт презентацию Avito по plan.json, используя шаблон из Google Slides.
Использование: python3 create_presentation.py plan.json
"""

import sys
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/presentations',
    'https://www.googleapis.com/auth/drive'
]

TEMPLATE_ID = '1rSns7QMIMcMAfh77gGQK9V878caYyWLJxJ7WJ55DbCA'


def copy_template(drive_service, title: str) -> str:
    try:
        copy = drive_service.files().copy(
            fileId=TEMPLATE_ID,
            body={"name": title}
        ).execute()
        return copy['id']
    except Exception as e:
        if '404' in str(e) or 'notFound' in str(e):
            print("\nОшибка: шаблон не найден.")
            print("Возможно, у вас нет доступа к шаблону Авито.")
            print(f"Попросите владельца открыть доступ к файлу: https://docs.google.com/presentation/d/{TEMPLATE_ID}")
        elif '403' in str(e):
            print("\nОшибка: нет прав на копирование шаблона.")
            print("Убедитесь, что вы прошли авторизацию: python3 scripts/auth.py")
        else:
            print(f"\nОшибка при копировании шаблона: {e}")
        raise


def get_all_slide_ids(slides_service, presentation_id: str) -> list[str]:
    pres = slides_service.presentations().get(
        presentationId=presentation_id
    ).execute()
    return [s["objectId"] for s in pres.get("slides", [])]


def delete_unused_slides(slides_service, presentation_id: str, wanted_ids: list[str]):
    all_ids = get_all_slide_ids(slides_service, presentation_id)
    to_delete = [sid for sid in all_ids if sid not in wanted_ids]
    if not to_delete:
        return
    requests = [{"deleteObject": {"objectId": oid}} for oid in to_delete]
    slides_service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={"requests": requests}
    ).execute()


def apply_element_transforms(slides_service, presentation_id: str, plan: dict):
    """Двигает и ресайзит элементы по objectId."""
    requests = []
    for slide in plan["slides"]:
        for element_id, t in slide.get("element_transforms", {}).items():
            req = {
                "updatePageElementTransform": {
                    "objectId": element_id,
                    "applyMode": "ABSOLUTE",
                    "transform": {
                        "scaleX":    t.get("scaleX", 1),
                        "scaleY":    t.get("scaleY", 1),
                        "shearX":    t.get("shearX", 0),
                        "shearY":    t.get("shearY", 0),
                        "translateX": t["translateX"],
                        "translateY": t["translateY"],
                        "unit": "EMU"
                    }
                }
            }
            requests.append(req)
    if requests:
        slides_service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={"requests": requests}
        ).execute()


def delete_elements(slides_service, presentation_id: str, plan: dict):
    """Удаляет ненужные элементы (иконки, картинки) по objectId."""
    to_delete = []
    for slide in plan["slides"]:
        to_delete.extend(slide.get("delete_elements", []))
    if not to_delete:
        return
    requests = [{"deleteObject": {"objectId": oid}} for oid in to_delete]
    slides_service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={"requests": requests}
    ).execute()


def replace_elements(slides_service, presentation_id: str, plan: dict):
    """Заменяет текст в конкретных элементах по objectId."""
    requests = []
    for slide in plan["slides"]:
        for element_id, new_text in slide.get("element_replacements", {}).items():
            requests.append({
                "deleteText": {
                    "objectId": element_id,
                    "textRange": {"type": "ALL"}
                }
            })
            if new_text:
                requests.append({
                    "insertText": {
                        "objectId": element_id,
                        "insertionIndex": 0,
                        "text": new_text
                    }
                })

    if requests:
        slides_service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={"requests": requests}
        ).execute()


def build_presentation(plan: dict) -> str:
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    slides_service = build('slides', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    title = plan.get("title", "Презентация Avito")
    print(f"Копирую шаблон: {title}")
    new_id = copy_template(drive_service, title)
    print(f"Создана копия: https://docs.google.com/presentation/d/{new_id}/edit")

    wanted_ids = [s["template_id"] for s in plan["slides"]]
    print(f"Удаляю лишние слайды (оставляю {len(wanted_ids)} из 111)...")
    delete_unused_slides(slides_service, new_id, wanted_ids)

    print("Двигаю и ресайзю элементы...")
    apply_element_transforms(slides_service, new_id, plan)

    print("Удаляю ненужные элементы (иконки и т.д.)...")
    delete_elements(slides_service, new_id, plan)

    print("Заменяю текст по элементам...")
    replace_elements(slides_service, new_id, plan)

    return new_id


def main():
    if len(sys.argv) < 2:
        print("Использование: python3 create_presentation.py plan.json")
        sys.exit(1)

    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        plan = json.load(f)

    print(f"Загружен план: {plan['title']}")
    print(f"Слайдов: {len(plan['slides'])}")
    for i, slide in enumerate(plan['slides'], 1):
        print(f"  {i}. {slide['description']}")

    print("\nСобираю презентацию...")
    new_id = build_presentation(plan)

    print(f"\nГотово!")
    print(f"Открыть: https://docs.google.com/presentation/d/{new_id}/edit")


if __name__ == "__main__":
    main()
