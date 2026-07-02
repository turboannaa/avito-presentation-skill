"""
Создаёт презентацию Avito по plan.json, используя шаблон из Google Slides.
Использование: python3 create_presentation.py plan.json
"""

import sys
import json
import math
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


def _get_image_size_px(url: str):
    """Скачивает изображение по URL и возвращает (width_px, height_px) или None."""
    try:
        import urllib.request
        import tempfile
        from PIL import Image as PILImage
        with tempfile.NamedTemporaryFile(suffix='.img', delete=False) as tmp:
            tmp_path = tmp.name
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            with open(tmp_path, 'wb') as f:
                f.write(resp.read())
        img = PILImage.open(tmp_path)
        return img.size  # (width, height)
    except Exception as e:
        print(f"  ⚠️  Не удалось получить размер картинки: {e}")
        return None


def handle_image_placeholders(slides_service, presentation_id: str,
                              slide_assignments: list):
    """
    Обрабатывает плейсхолдеры картинок на всех слайдах.

    ПРАВИЛО: картинки вставляются ТОЛЬКО в слайды, где шаблон предусматривает
    для них место (элемент с текстом «Вставьте картинку сюда»).

    Логика:
    - Если в слайде плана есть image_url → удаляем IMAGE-плейсхолдер и текст-метку,
      вставляем картинку с сохранением пропорций (fill by height/width).
    - Если image_url нет → удаляем текст-метку «Вставьте картинку сюда»,
      IMAGE-плейсхолдер шаблона остаётся (пользователь вставит вручную).
    - Если на слайде нет плейсхолдера → image_url игнорируется (предупреждение).

    Правило масштабирования (fill, без кропа):
    - Если картинка вертикальная относительно фрейма → высота = высота фрейма,
      ширина пересчитывается пропорционально.
    - Если горизонтальная → ширина = ширина фрейма, высота пересчитывается.
    - Картинка центрируется в фрейме.

    Формат в plan.json:
        { "template_id": "...", "image_url": "https://...", ... }
    """
    PLACEHOLDER_TEXT = 'Вставьте картинку сюда'

    pres = get_presentation(slides_service, presentation_id)
    slide_elements = {
        slide['objectId']: slide.get('pageElements', [])
        for slide in pres['slides']
    }

    delete_requests = []
    create_requests = []

    for plan_slide, slide_id, elem_map in slide_assignments:
        image_url = plan_slide.get('image_url')
        elements = slide_elements.get(slide_id, [])

        # Ищем текст-метку «Вставьте картинку сюда»
        label_elem = None
        for elem in elements:
            text_content = ''.join(
                te.get('textRun', {}).get('content', '')
                for te in elem.get('shape', {}).get('text', {}).get('textElements', [])
            )
            if PLACEHOLDER_TEXT in text_content:
                label_elem = elem
                break

        if label_elem is None:
            if image_url:
                print(f"  ⚠️  image_url указан, но слайд {slide_id} не имеет места под картинку — пропускаю")
            continue

        # Ищем IMAGE-элемент (реальный фрейм под картинку)
        # Берём самый крупный IMAGE на слайде по площади
        image_frame_elem = None
        best_area = 0
        for elem in elements:
            if 'image' not in elem:
                continue
            s = elem.get('size', {})
            t = elem.get('transform', {})
            eff_w = s.get('width', {}).get('magnitude', 0) * t.get('scaleX', 1)
            eff_h = s.get('height', {}).get('magnitude', 0) * t.get('scaleY', 1)
            area = eff_w * eff_h
            if area > best_area:
                best_area = area
                image_frame_elem = elem

        # Удаляем текст-метку в любом случае
        delete_requests.append({"deleteObject": {"objectId": label_elem['objectId']}})

        if image_url and image_frame_elem is not None:
            # Определяем размеры и позицию фрейма
            s = image_frame_elem.get('size', {})
            t = image_frame_elem.get('transform', {})
            frame_w = s.get('width', {}).get('magnitude', 0) * t.get('scaleX', 1)
            frame_h = s.get('height', {}).get('magnitude', 0) * t.get('scaleY', 1)
            frame_x = t.get('translateX', 0)
            frame_y = t.get('translateY', 0)

            # Удаляем IMAGE-плейсхолдер шаблона
            delete_requests.append({"deleteObject": {"objectId": image_frame_elem['objectId']}})

            # Получаем реальные размеры вставляемой картинки
            img_size = _get_image_size_px(image_url)
            if img_size:
                img_w_px, img_h_px = img_size
                # Определяем направление масштабирования (fill без кропа)
                img_ratio = img_w_px / img_h_px    # > 1 горизонтальная, < 1 вертикальная
                frame_ratio = frame_w / frame_h

                if img_ratio < frame_ratio:
                    # Картинка вертикальнее фрейма → fill по высоте
                    new_h = frame_h
                    new_w = frame_h * img_ratio
                else:
                    # Картинка горизонтальнее или квадратная → fill по ширине
                    new_w = frame_w
                    new_h = frame_w / img_ratio

                # Центрируем в фрейме
                cx = frame_x + (frame_w - new_w) / 2
                cy = frame_y + (frame_h - new_h) / 2
            else:
                # Не удалось получить размер — вставляем на весь фрейм
                new_w, new_h = frame_w, frame_h
                cx, cy = frame_x, frame_y

            create_requests.append({
                "createImage": {
                    "url": image_url,
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width":  {"magnitude": new_w, "unit": "EMU"},
                            "height": {"magnitude": new_h, "unit": "EMU"}
                        },
                        "transform": {
                            "scaleX": 1, "scaleY": 1,
                            "translateX": cx, "translateY": cy,
                            "unit": "EMU"
                        }
                    }
                }
            })
        elif image_url and image_frame_elem is None:
            print(f"  ⚠️  image_url указан, но у слайда {slide_id} нет IMAGE-фрейма — пропускаю вставку")
        # else: image_url не указан — текст-метка уже добавлена к удалению,
        # IMAGE-плейсхолдер шаблона остаётся для ручной вставки

    if delete_requests:
        slides_service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={"requests": delete_requests}
        ).execute()

    if create_requests:
        slides_service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={"requests": create_requests}
        ).execute()

    n_img = len(create_requests)
    if n_img:
        print(f"  Вставлено картинок: {n_img}")


def apply_transforms(slides_service, presentation_id: str,
                     slide_assignments: list):
    """
    Применяет трансформации из плана.
    Если в плане не указан scaleX/scaleY — берём текущее значение из шаблона,
    а не дефолт 1. Это важно: иначе scaleX шаблона (например 1.3848) будет
    сброшен в 1 и фреймы станут уже, чем задумано.
    """
    # Читаем текущие трансформы один раз
    pres = get_presentation(slides_service, presentation_id)
    element_lookup = {
        elem['objectId']: elem
        for slide in pres['slides']
        for elem in slide.get('pageElements', [])
    }

    requests = []
    for plan_slide, slide_id, elem_map in slide_assignments:
        for orig_id, t in plan_slide.get("element_transforms", {}).items():
            real_id = elem_map.get(orig_id, orig_id)
            # Дефолты — текущий transform шаблона, а не единица
            cur = element_lookup.get(real_id, {}).get('transform', {})
            requests.append({
                "updatePageElementTransform": {
                    "objectId": real_id,
                    "applyMode": "ABSOLUTE",
                    "transform": {
                        "scaleX":     t.get("scaleX",  cur.get("scaleX", 1)),
                        "scaleY":     t.get("scaleY",  cur.get("scaleY", 1)),
                        "shearX":     t.get("shearX",  cur.get("shearX", 0)),
                        "shearY":     t.get("shearY",  cur.get("shearY", 0)),
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


def apply_target_lines(slides_service, presentation_id: str,
                       slide_assignments: list):
    """
    Для элементов с element_target_lines в плане изменяет ширину фрейма (scaleX)
    так, чтобы текст помещался ровно в указанное число строк при текущем шрифте.

    Формат в plan.json:
        "element_target_lines": { "element_id": 2 }
    """
    pres = get_presentation(slides_service, presentation_id)
    element_lookup = {
        elem['objectId']: elem
        for slide in pres['slides']
        for elem in slide.get('pageElements', [])
    }

    requests = []
    for plan_slide, slide_id, elem_map in slide_assignments:
        for orig_id, target in plan_slide.get("element_target_lines", {}).items():
            new_text = plan_slide.get("element_replacements", {}).get(orig_id, "")
            if not new_text or target < 1:
                continue
            real_id = elem_map.get(orig_id, orig_id)
            elem = element_lookup.get(real_id)
            if not elem or 'shape' not in elem:
                continue

            size = elem.get('size', {})
            t = elem.get('transform', {})
            base_w = size.get('width', {}).get('magnitude', 0)
            if base_w <= 0:
                continue

            # Шрифт из первого textRun шаблона
            font_pt = 18.0
            for te in elem['shape'].get('text', {}).get('textElements', []):
                fs = te.get('textRun', {}).get('style', {}).get('fontSize', {})
                if fs.get('magnitude'):
                    font_pt = float(fs['magnitude'])
                    break

            # Нужная ширина: самый длинный абзац / target строк
            longest = max(len(p) for p in new_text.split('\n'))
            chars_per_line = math.ceil(longest / target)
            needed_w = chars_per_line * font_pt * 12700 * 0.55
            new_scale_x = needed_w / base_w

            requests.append({
                "updatePageElementTransform": {
                    "objectId": real_id,
                    "applyMode": "ABSOLUTE",
                    "transform": {
                        "scaleX":     new_scale_x,
                        "scaleY":     t.get('scaleY', 1),
                        "shearX":     t.get('shearX', 0),
                        "shearY":     t.get('shearY', 0),
                        "translateX": t.get('translateX', 0),
                        "translateY": t.get('translateY', 0),
                        "unit": "EMU"
                    }
                }
            })

    if requests:
        print(f"  Подгоняю ширину {len(requests)} фреймов под целевое число строк...")
        slides_service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={"requests": requests}
        ).execute()


def fit_text_to_frame(slides_service, presentation_id: str,
                      slide_assignments: list):
    """
    Позиции и размеры фреймов НЕ меняем — берём точно из шаблона.

    Логика выравнивания шрифта:
      1. Для каждого элемента считаем оптимальный pt (меньше/больше шагами 5pt).
      2. Группируем элементы одного слайда по исходному размеру шрифта из шаблона:
         одинаковый исходный pt = одна категория (заголовки, описания и т.д.).
      3. Всей группе присваиваем наименьший найденный pt в группе —
         так все заголовки слайда одного размера, все описания — одного.

    font_size_overrides из plan.json имеет приоритет и не перезаписывается.
    """
    pres = get_presentation(slides_service, presentation_id)

    element_lookup = {}
    for slide in pres['slides']:
        for elem in slide.get('pageElements', []):
            element_lookup[elem['objectId']] = elem

    def estimate_height(text, pt, width_emu):
        char_w = pt * 12700 * 0.55
        cpl = max(1, int(width_emu / char_w))
        lines = sum(
            max(1, math.ceil(max(1, len(p)) / cpl))
            for p in text.split('\n')
        )
        return lines * pt * 12700 * 1.45 + pt * 12700 * 1.0

    def optimal_pt(text, orig_pt, eff_w, eff_h):
        """
        Оптимальный размер шрифта для одного элемента.
        Рост: пробуем +1, +2, +3, +4, +5 — берём максимальный влезающий (не выше orig+5).
        Уменьшение: пробуем -1, -2, -3, -4, -5 — берём минимальный влезающий (не ниже 10pt).
        """
        if estimate_height(text, orig_pt, eff_w) <= eff_h:
            # Влезает — пробуем увеличить на 1..5pt, берём наибольший вариант
            best = orig_pt
            for delta in range(1, 6):
                if estimate_height(text, orig_pt + delta, eff_w) <= eff_h:
                    best = orig_pt + delta
                else:
                    break
            return best
        else:
            # Не влезает — уменьшаем на 1..5pt пока не влезет, минимум 10pt
            for delta in range(1, 6):
                c = orig_pt - delta
                if c < 10:
                    return 10
                if estimate_height(text, c, eff_w) <= eff_h:
                    return c
            return max(10, orig_pt - 5)

    # Шаг 1: считаем оптимальный pt для каждого элемента
    # groups[(slide_id, orig_pt_rounded)] = [(real_id, opt_pt), ...]
    groups = defaultdict(list)

    for plan_slide, slide_id, elem_map in slide_assignments:
        overrides = plan_slide.get("font_size_overrides", {})
        # Элементы с element_target_lines уже получили нужную ширину фрейма —
        # не трогаем их шрифт, иначе fit_text_to_frame сломает результат
        target_lines_ids = set(plan_slide.get("element_target_lines", {}).keys())
        for orig_id, new_text in plan_slide.get("element_replacements", {}).items():
            if not new_text or orig_id in overrides or orig_id in target_lines_ids:
                continue
            real_id = elem_map.get(orig_id, orig_id)
            elem = element_lookup.get(real_id)
            if not elem or 'shape' not in elem:
                continue

            size = elem.get('size', {})
            t = elem.get('transform', {})
            eff_w = size.get('width', {}).get('magnitude', 0) * t.get('scaleX', 1)
            eff_h = size.get('height', {}).get('magnitude', 0) * t.get('scaleY', 1)
            if eff_w <= 0 or eff_h <= 0:
                continue

            font_pt = 18.0
            for te in elem['shape'].get('text', {}).get('textElements', []):
                fs = te.get('textRun', {}).get('style', {}).get('fontSize', {})
                if fs.get('magnitude'):
                    font_pt = float(fs['magnitude'])
                    break

            opt = optimal_pt(new_text, font_pt, eff_w, eff_h)
            groups[(slide_id, round(font_pt))].append((real_id, opt))

    # Шаг 2: берём минимальный pt в каждой группе и ставим всем
    requests = []
    for (slide_id, orig_pt), members in groups.items():
        group_min = min(pt for _, pt in members)
        if group_min == orig_pt:
            continue  # без изменений
        for real_id, _ in members:
            requests.append({
                "updateTextStyle": {
                    "objectId": real_id,
                    "textRange": {"type": "ALL"},
                    "style": {
                        "fontSize": {"magnitude": group_min, "unit": "PT"}
                    },
                    "fields": "fontSize"
                }
            })

    if requests:
        print(f"  Выравниваю шрифт в {len(requests)} элементах...")
        slides_service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={"requests": requests}
        ).execute()


def apply_font_sizes(slides_service, presentation_id: str,
                     slide_assignments: list):
    """
    Применяет переопределения размера шрифта из font_size_overrides.
    Шаг изменения — 5pt (можно больше или меньше шаблонного значения, минимум 5pt).

    Формат в plan.json:
        "font_size_overrides": {
            "element_id": 24
        }
    """
    requests = []
    for plan_slide, slide_id, elem_map in slide_assignments:
        for orig_id, size_pt in plan_slide.get("font_size_overrides", {}).items():
            size_pt = max(10, size_pt)  # минимум 10pt
            real_id = elem_map.get(orig_id, orig_id)
            requests.append({
                "updateTextStyle": {
                    "objectId": real_id,
                    "textRange": {"type": "ALL"},
                    "style": {
                        "fontSize": {"magnitude": size_pt, "unit": "PT"}
                    },
                    "fields": "fontSize"
                }
            })
    if requests:
        slides_service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={"requests": requests}
        ).execute()


def build_presentation(plan: dict) -> str:
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # cache_discovery=False — получаем свежий discovery-документ,
    # чтобы новые поля API (например autoFit) были доступны
    slides_service = build('slides', 'v1', credentials=creds, cache_discovery=False)
    drive_service = build('drive', 'v3', credentials=creds, cache_discovery=False)

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

    print("Обрабатываю плейсхолдеры картинок...")
    handle_image_placeholders(slides_service, new_id, slide_assignments)

    # apply_target_lines ДОЛЖЕН идти ДО replace_elements:
    # тогда в шейпах ещё живёт оригинальный текст шаблона с правильным fontSize,
    # и мы читаем его корректно для расчёта scaleX.
    print("Подгоняю ширину фреймов под целевое число строк...")
    apply_target_lines(slides_service, new_id, slide_assignments)

    print("Заменяю текст...")
    replace_elements(slides_service, new_id, slide_assignments)

    print("Подгоняю шрифт под размер фреймов из шаблона...")
    fit_text_to_frame(slides_service, new_id, slide_assignments)

    print("Применяю переопределения размера шрифта...")
    apply_font_sizes(slides_service, new_id, slide_assignments)

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

    # Проверка количества слайдов — только если поле явно задано в плане.
    #
    # Правило: expected_slide_count ставить ТОЛЬКО когда исходный документ
    # сам нумерует разделы / слайды (например: «Слайд 1», «## 1.», «Section 3»).
    # Тогда количество слайдов в плане должно строго совпадать с этим числом.
    #
    # Если документ не содержит явной нумерации — поле не ставится,
    # и Клод выбирает количество слайдов самостоятельно по смыслу.
    if "expected_slide_count" in plan:
        expected = plan["expected_slide_count"]
        actual = len(plan["slides"])
        if actual != expected:
            print(f"\n❌ Ошибка: в плане указано expected_slide_count={expected}, "
                  f"но слайдов в slides[] — {actual}.")
            print("Исправь plan.json перед запуском.")
            sys.exit(1)
        print(f"✓ Количество слайдов совпадает с ожидаемым: {expected}")

    print("\nСобираю презентацию...")
    new_id = build_presentation(plan)

    print(f"\nГотово!")
    print(f"Открыть: https://docs.google.com/presentation/d/{new_id}/edit")


if __name__ == "__main__":
    main()
