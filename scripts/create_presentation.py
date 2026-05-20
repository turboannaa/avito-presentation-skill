"""
Создаёт презентацию Avito по plan.json, используя шаблон из Google Slides.
Использование: python3 create_presentation.py plan.json
"""

import sys
import json
from collections import Counter, defaultdict
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
            print(f"Попросите владельца открыть доступ: https://docs.google.com/presentation/d/{TEMPLATE_ID}")
        elif '403' in str(e):
            print("\nОшибка: нет прав на копирование шаблона.")
            print("Убедитесь, что вы прошли авторизацию: python3 scripts/auth.py")
        else:
            print(f"\nОшибка при копировании шаблона: {e}")
        raise


def get_presentation(slides_service, presentation_id: str) -> dict:
    return slides_service.presentations().get(
        presentationId=presentation_id
    ).execute()


def duplicate_slide(slides_service, presentation_id: str,
                    slide_id: str, suffix: str) -> tuple[str, dict]:
    """
    Дублирует слайд и возвращает (новый_slide_id, маппинг старых element_id -> новых).
    """
    pres = get_presentation(slides_service, presentation_id)
    orig_slide = next((s for s in pres['slides'] if s['objectId'] == slide_id), None)
    if not orig_slide:
        raise ValueError(f"Слайд {slide_id} не найден")

    # Собираем все objectId на слайде (сам слайд + элементы)
    elem_ids = [el['objectId'] for el in orig_slide.get('pageElements', [])]
    id_map = {slide_id: f"{slide_id}_{suffix}"}
    for eid in elem_ids:
        id_map[eid] = f"{eid}_{suffix}"

    slides_service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={'requests': [{'duplicateObject': {'objectId': slide_id, 'objectIds': id_map}}]}
    ).execute()

    elem_map = {eid: f"{eid}_{suffix}" for eid in elem_ids}
    return f"{slide_id}_{suffix}", elem_map


def prepare_slides(slides_service, presentation_id: str, plan_slides: list) -> list:
    """
    Для каждого слайда в плане готовит (slide_id, element_id_map).
    Если один template_id используется несколько раз — дублирует слайд.
    Возвращает список (plan_slide, real_slide_id, element_id_map).
    """
    need_count = Counter(s['template_id'] for s in plan_slides)

    # Для каждого template_id строим список (slide_id, elem_map) нужного размера
    available = {}
    for template_id, count in need_count.items():
        instances = [(template_id, {})]
        for i in range(1, count):
            new_sid, elem_map = duplicate_slide(
                slides_service, presentation_id, template_id, f"dup{i}"
            )
            instances.append((new_sid, elem_map))
        available[template_id] = instances

    counters = defaultdict(int)
    result = []
    for slide in plan_slides:
        tid = slide['template_id']
        idx = counters[tid]
        slide_id, elem_map = available[tid][idx]
        counters[tid] += 1
        result.append((slide, slide_id, elem_map))

    return result


def delete_unused_slides(slides_service, presentation_id: str, keep_ids: set):
    pres = get_presentation(slides_service, presentation_id)
    all_ids = [s['objectId'] for s in pres['slides']]
    to_delete = [sid for sid in all_ids if sid not in keep_ids]
    if not to_delete:
        return
    requests = [{"deleteObject": {"objectId": oid}} for oid in to_delete]
    slides_service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={"requests": requests}
    ).execute()


def reorder_slides(slides_service, presentation_id: str, ordered_ids: list[str]):
    """Переставляет слайды в нужный порядок."""
    for target_index, slide_id in enumerate(ordered_ids):
        slides_service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={'requests': [{'updateSlidesPosition': {
                'slideObjectIds': [slide_id],
                'insertionIndex': target_index
            }}]}
        ).execute()


def apply_transforms(slides_service, presentation_id: str,
                     slide_assignments: list):
    requests = []
    for plan_slide, slide_id, elem_map in slide_assignments:
        for orig_id, t in plan_slide.get("element_transforms", {}).items():
            real_id = elem_map.get(orig_id, orig_id)
            requests.append({
                "updatePageElementTransform": {
                    "objectId": real_id,
                    "applyMode": "ABSOLUTE",
                    "transform": {
                        "scaleX":     t.get("scaleX", 1),
                        "scaleY":     t.get("scaleY", 1),
                        "shearX":     t.get("shearX", 0),
                        "shearY":     t.get("shearY", 0),
                        "translateX": t["translateX"],
                        "translateY": t["translateY"],
                        "unit": "EMU"
                    }
                }
            })
    if requests:
        slides_service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={"requests": requests}
        ).execute()


def delete_elements(slides_service, presentation_id: str,
                    slide_assignments: list):
    to_delete = []
    for plan_slide, slide_id, elem_map in slide_assignments:
        for orig_id in plan_slide.get("delete_elements", []):
            to_delete.append(elem_map.get(orig_id, orig_id))
    if not to_delete:
        return
    requests = [{"deleteObject": {"objectId": oid}} for oid in to_delete]
    slides_service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={"requests": requests}
    ).execute()


def replace_elements(slides_service, presentation_id: str,
                     slide_assignments: list):
    requests = []
    for plan_slide, slide_id, elem_map in slide_assignments:
        for orig_id, new_text in plan_slide.get("element_replacements", {}).items():
            real_id = elem_map.get(orig_id, orig_id)
            requests.append({
                "deleteText": {"objectId": real_id, "textRange": {"type": "ALL"}}
            })
            if new_text:
                requests.append({
                    "insertText": {
                        "objectId": real_id,
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

    plan_slides = plan["slides"]
    unique_templates = len(set(s["template_id"] for s in plan_slides))
    print(f"Подготавливаю {len(plan_slides)} слайдов ({unique_templates} уникальных шаблонов)...")
    slide_assignments = prepare_slides(slides_service, new_id, plan_slides)

    keep_ids = {sid for _, sid, _ in slide_assignments}
    print(f"Удаляю лишние слайды...")
    delete_unused_slides(slides_service, new_id, keep_ids)

    print(f"Переставляю слайды в нужный порядок...")
    ordered_ids = [sid for _, sid, _ in slide_assignments]
    reorder_slides(slides_service, new_id, ordered_ids)

    print("Двигаю и ресайзю элементы...")
    apply_transforms(slides_service, new_id, slide_assignments)

    print("Удаляю ненужные элементы...")
    delete_elements(slides_service, new_id, slide_assignments)

    print("Заменяю текст...")
    replace_elements(slides_service, new_id, slide_assignments)

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
