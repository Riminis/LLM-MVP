def save_to_markdown(data: dict, output_path: str, time, topics, tags=None, status='Draft', users='User'):
    with open(output_path, "w", encoding="utf-8") as f:
        # Записываем YAML-фронт-маттер
        f.write("---\n")
        f.write(f"created: {time.date()}\n")
        f.write(f"updated: {time.date()}\n")
        f.write(f"topics: {topics}\n")
        f.write(f"tags: {tags}\n")
        f.write(f"status: {status}\n")
        f.write(f"author: {users}\n")
        f.write("---\n\n")
        
        # Определяем заголовок в зависимости от домена
        domain = data.get('domain', 'Документ')
        f.write(f"# Ключевые понятия: {domain}\n\n")
        
        # Проверяем структуру данных: либо это {'structured': {...}}, либо сразу структурированные данные
        if 'structured' in data:
            # Формат: {'structured': {...}}
            structured_data = data['structured']
        else:
            # Формат: сразу структурированные данные
            structured_data = data
        
        # Обрабатываем все возможные типы данных
        sections = {
            "definitions": "Определения",
            "theorems": "Теоремы", 
            "formulas": "Формулы",
            "examples": "Примеры",
            "concepts": "Концепции",
            "laws": "Законы",
            "principles": "Принципы",
            "rules": "Правила",
            "postulates": "Постулаты",
            "corollaries": "Следствия",
            "lemmas": "Леммы",
            "proofs": "Доказательства",
            "properties": "Свойства",
            "applications": "Применения",
            "methods": "Методы",
            "notations": "Обозначения"
        }
        
        for key, title in sections.items():
            if key in structured_data and structured_data[key]:
                f.write(f"## {title}\n\n")
                for item in structured_data[key]:
                    if key == "formulas":
                        f.write(f"- ${item}$\n")
                    else:
                        f.write(f"- {item}\n")
                f.write("\n")
        
        # Если есть другие поля в structured_data, которые не вошли в sections
        for key, value in structured_data.items():
            if key not in sections and value and isinstance(value, list):
                section_title = key.replace('_', ' ').title()
                f.write(f"## {section_title}\n\n")
                for item in value:
                    f.write(f"- {item}\n")
                f.write("\n")
    
    return 'OK'
