# LLM-MVP: Knowledge Base Pipeline

Автоматизированная система для обработки документов и создания структурированной базы знаний в Obsidian с использованием Sber GigaChat API.

## Описание

LLM-MVP — это pipeline, который:

1. **Загружает документы** в различных форматах (PDF, DOCX, TXT, JSON, RST, LaTeX, Markdown)
2. **Обрабатывает через GigaChat** для извлечения ключевой информации и создания резюме
3. **Автоматически генерирует имена файлов** на основе основной темы документа
4. **Создаёт Markdown файлы** с YAML frontmatter для Obsidian
5. **Управляет связями** между документами (tags, topics, backlinks)
6. **Сохраняет индекс** для быстрого поиска и анализа

## Быстрый старт

### Требования

- Python 3.8+
- Ключи доступа к Sber GigaChat API
- SSL сертификаты Sber

### Установка

```bash
# Клонируем репозиторий
git clone https://github.com/Riminis/LLM-MVP.git
cd LLM-MVP

# Создаём виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # На Windows: .venv\Scripts\activate

# Устанавливаем зависимости
pip install -r requirements.txt
```

### Конфигурация

#### 1. Переменные окружения

Создайте файл `.env` в корне проекта:

```env
GIGACHAT_CLIENT_ID=ваш_client_id
GIGACHAT_CLIENT_SECRET=ваш_client_secret
```

#### 2. SSL сертификаты

Поместите сертификаты Sber в папку `certs/`:

```
certs/
├── sber_oauth_cert.pem      # Для получения токена
└── sber_api_cert.pem        # Для API запросов
```

Система автоматически найдёт сертификаты в:
- `certs/` (текущая директория)
- `src/../certs/` (относительный путь)
- `~/.sber_certs/` (домашняя директория)

#### 3. Входные файлы

Подготовьте документ для обработки:

```
examples/
└── math_sample.txt          # Ваш документ
```

Обновите промпт если нужно:

```
prompts/
└── universal_prompt.txt     # Инструкция для GigaChat
```

### Запуск

```bash
# Простой запуск
python test.py

# С отладкой
python -u test.py
```

## Результат

После запуска будут созданы:

```
vault/                        # Выходная директория
├── analysis-mathematical-fundamentals.md
├── geometry-euclidean-basics.md
└── ...

.obsidian/
└── index.json              # Индекс файлов и связей
```

## Архитектура

### Основные компоненты

```
src/
├── extract_agent.py         # GigaChat API клиент
├── document_loader.py       # Загрузчик документов
├── index_manager.py         # Управление индексом
├── link_generator.py        # Генерация ссылок между файлами
└── pipeline.py              # Главный pipeline
```

### Поток данных

```
Входной документ
    ↓
DocumentLoader (загрузка)
    ↓
GigaChatClient (обработка через LLM)
    ↓
KnowledgeBasePipeline (парсинг и структурирование)
    ├── Парсинг frontmatter (title, main_topic, tags)
    ├── Извлечение topics из содержания
    └── Генерация имени файла из main_topic
    ↓
LinkGenerator (создание связей)
    ↓
IndexManager (сохранение метаданных)
    ↓
Markdown файл + индекс JSON
```

## YAML Frontmatter

Каждый файл содержит YAML frontmatter для Obsidian:

```markdown
---
title: "Математический анализ: основные понятия"
main_topic: "analysis"
tags: [math, calculus, analysis, definitions, theorems]
date: "2025-12-12"
summary: "Ключевые определения и теоремы математического анализа"
---

# Основное содержание...
```

**Поля frontmatter:**
- `title` — название документа
- `main_topic` — основная категория (используется для имени файла)
- `tags` — теги для категоризации
- `date` — дата создания
- `summary` — краткое описание

## Система связей

### Автоматическая генерация связей

Система анализирует:
- **Общие теги** — файлы с похожими тегами связываются
- **Похожие темы** — рассчитывается Jaccard similarity
- **Упоминания в тексте** — выделенные слова автоматически становятся ссылками

### Структура индекса

```json
{
  "files": {
    "analysis-mathematical-fundamentals.md": {
      "title": "Математический анализ",
      "tags": ["math", "analysis"],
      "topics": ["definitions", "theorems"],
      "related": ["calculus-limits.md"]
    }
  },
  "backlinks": {
    "analysis-mathematical-fundamentals.md": ["file1.md", "file2.md"]
  }
}
```

## Особенности

 **Многоформатная поддержка**
- PDF, DOCX, TXT, JSON, RST, LaTeX, Markdown

 **Интеллектуальная обработка**
- Автоматическое извлечение метаданных
- Сжатие контента с сохранением ключевой информации
- Умное создание имён файлов

 **Надёжная обработка ошибок**
- Fallback парсеры для неправильного YAML
- Graceful degradation без PyYAML
- Подробное логирование

 **Obsidian-совместимость**
- Wiki-ссылки ([[file]])
- Якоря для навигации ([[#Section]])
- Чистый YAML frontmatter
- Поддержка тегов и backlinks

 **Масштабируемость**
- Обработка больших документов
- Эффективная индексация
- Быстрый поиск связей

## Кастомизация

### Изменение промпта

Отредактируйте `prompts/universal_prompt.txt`:

```bash
nano prompts/universal_prompt.txt
```

**Ключевые переменные в промпте:**
- `{SOURCE_CONTENT}` — содержание документа
- `{SOURCE_FILE_PATH}` — путь к файлу
- `{LANGUAGE}` — язык документа

### Изменение параметров

В `test.py`:

```python
pipeline = KnowledgeBasePipeline(
    output_dir="vault",              # Директория для вывода
    index_path=".obsidian/index.json" # Путь к индексу
)
```

В `src/pipeline.py`:

```python
# Порог релевантности для автоссылок
auto_link_min_confidence=0.6

# Количество связанных файлов
max_results=5
```

## Логирование

Система использует стандартный Python логгер:

```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

**Уровни логирования:**
- `INFO` — информация о ходе выполнения
- `WARNING` — предупреждения (отсутствие файлов, fallback парсеры)
- `ERROR` — критические ошибки

## Решение проблем

### "Missing GIGACHAT credentials"

**Решение:** Проверьте `.env` файл:

```bash
cat .env
# Должно содержать:
# GIGACHAT_CLIENT_ID=...
# GIGACHAT_CLIENT_SECRET=...
```

### "Certificate not found"

**Решение:** Убедитесь что сертификаты в `certs/`:

```bash
ls -la certs/
# sber_oauth_cert.pem
# sber_api_cert.pem
```

### "YAML parsing failed"

**Решение:** Система автоматически использует fallback парсер. Проверьте логи для деталей.

### "Files without links"

**Решение:** Нормально для первого импорта. Добавьте больше документов, система найдёт связи.

## Статистика

После запуска вывод включает:

```
Knowledge base statistics:
  total_files: 3
  total_links: 4
  unique_topics: 13
  unique_tags: 3
```

## Безопасность

- Переменные окружения не коммитятся (см. `.gitignore`)
- SSL сертификаты не должны быть в Git
- Используются secure HTTP адаптеры
- Нет сохранения токенов на диск

## Примеры использования

### Обработка одного документа

```python
from src.pipeline import KnowledgeBasePipeline

pipeline = KnowledgeBasePipeline()
result = pipeline.process_document(
    input_file="examples/document.pdf",
    prompt_file="prompts/universal_prompt.txt"
)
print(f"Создан файл: {result}")
```

### Получение статистики

```python
stats = pipeline.get_graph_stats()
print(f"Всего файлов: {stats['total_files']}")
print(f"Уникальных тегов: {stats['unique_tags']}")
```

### Поиск несвязанных файлов

```python
orphaned = pipeline.find_orphaned_files()
if orphaned:
    print(f"Файлы без связей: {orphaned}")
```

## Структура проекта

```
LLM-MVP/
├── src/
│   ├── __init__.py
│   ├── extract_agent.py       # GigaChat интеграция
│   ├── document_loader.py     # Загрузка документов
│   ├── index_manager.py       # Управление индексом
│   ├── link_generator.py      # Генерация ссылок
│   └── pipeline.py            # Главный pipeline
├── prompts/
│   └── universal_prompt.txt   # Инструкция для LLM
├── examples/
│   └── math_sample.txt        # Пример входного файла
├── certs/
│   ├── sber_oauth_cert.pem
│   └── sber_api_cert.pem
├── vault/                     # Выходные Markdown файлы
├── .obsidian/
│   └── index.json             # Индекс для Obsidian
├── test.py                    # Главный скрипт
├── requirements.txt           # Зависимости Python
├── .env.example               # Шаблон переменных окружения
├── .gitignore                 # Git ignore
└── README.md                  # Этот файл
```

## Зависимости

```
requests>=2.28.0
python-dotenv>=0.20.0
PyYAML>=6.0
python-docx>=0.8.11
PyPDF2>=3.0.0
urllib3>=1.26.0
```

## Лицензия

MIT License - см. LICENSE файл


## Дорожная карта

- [ ] Поддержка множественной обработки документов
- [ ] Web интерфейс для управления
- [ ] Интеграция с Obsidian плагинами
- [ ] Кэширование результатов обработки
- [ ] Поддержка других LLM API
- [ ] Визуализация графа знаний
