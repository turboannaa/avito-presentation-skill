# Avito Presentation Skill

Скилл создаёт презентацию в Google Slides по шаблону Avito — достаточно написать тему в чат.

---

## Что нужно для работы

- Mac или Windows с Python 3.9+
- Claude Code (платная подписка)
- Google-аккаунт с доступом к Google Drive

---

## Шаг 1 — Установить Claude Code

**Если используешь скилл внутри Авито** — установи через внутреннюю утилиту `avito-ai` (уточни актуальную команду у команды платформы).

**Если устанавливаешь самостоятельно:**

```bash
npm install -g @anthropic-ai/claude-code
```

Проверить установку:

```bash
claude --version
```

---

## Шаг 2 — Скачать скилл с GitHub

Репозиторий открытый, клонировать может любой:

```bash
git clone https://github.com/turboannaa/avito-presentation-skill.git
cd avito-presentation-skill
```

---

## Шаг 3 — Установить Python-зависимости

```bash
pip3 install google-api-python-client google-auth google-auth-oauthlib
```

---

## Шаг 4 — Настроить Google API (один раз)

### 4.1 Создать проект в Google Cloud

1. Зайди на [console.cloud.google.com](https://console.cloud.google.com)
2. Нажми **Select a project** → **New Project** → назови как угодно → **Create**

### 4.2 Включить нужные API

В левом меню: **APIs & Services** → **Library**

Найди и включи (кнопка **Enable**):
- **Google Slides API**
- **Google Drive API**
- **Google Docs API**

### 4.3 Создать OAuth credentials

1. **APIs & Services** → **Credentials** → **Create Credentials** → **OAuth client ID**
2. Если просит настроить Consent Screen:
   - **External** → заполни только название приложения → сохрани
3. Application type: **Desktop app** → **Create**
4. Скачай JSON → переименуй в `credentials.json` → положи в папку скилла

### 4.4 Авторизоваться

```bash
python3 scripts/auth.py
```

Откроется браузер → войди в Google-аккаунт → разреши доступ.

В папке появится `token.json` — это твой личный ключ доступа, **никому не отправляй**.

---

## Шаг 5 — Запустить Claude Code в папке скилла

```bash
cd avito-presentation-skill
claude
```

---

## Шаг 6 — Создать презентацию

Просто напиши в чат тему, например:

> Мне нужна презентация на 8 слайдов на тему «Как мы запускали новый продукт за 2 недели»

Клод сам:
1. Подберёт нужные шаблонные слайды
2. Напишет контент
3. Сформирует `plan.json`
4. Запустит скрипт и создаст презентацию в твоём Google Drive

В ответ получишь ссылку на готовую презентацию.

---

## Частые вопросы

**Презентация не создаётся, ошибка 403**
→ Проверь что все три API включены в Google Cloud Console (шаг 4.2)

**`token.json` не создаётся**
→ Убедись что `credentials.json` лежит в папке скилла и запусти `python3 auth.py` заново

**Текст не влезает / съезжает**
→ Напиши Клоду что именно не так — он подправит позиции и пересоберёт

---

## Файлы в репозитории

| Файл | Описание |
|------|----------|
| `scripts/create_presentation.py` | Основной скрипт сборки |
| `scripts/auth.py` | Одноразовая OAuth авторизация |
| `references/showcase_plan.json` | Пример со всеми типами слайдов |
| `references/plan.json` | Последний сгенерированный план |
| `scripts/inspect_slides.py` | Утилита — показывает структуру шаблона |

---

---

## Важно

Не передавай в скилл персональные данные пользователей, чувствительную корпоративную информацию или внутренние данные, которые не предназначены для передачи внешним сервисам. Скилл отправляет контент слайдов через Google Slides API — всё что ты вводишь, попадает в Google.

---

Вопросы → @anndreevva
