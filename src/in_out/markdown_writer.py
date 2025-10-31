def save_to_markdown(data: dict, output_path: str, time, topics, tags=None, status='Draft', users='User'):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write

        f.write(
        "---\n"
        f"created: {time.date()}\n"
        f"updated: {time.date()}\n"
        f"topics: {topics}\n"
        f"tags: {tags}\n"
        f"status: {status}\n"
        f"author: {users}\n"
        "---\n\n"
        )

        f.write("# Ключевые математические понятия\n\n")
        
        if data["definitions"]:
            f.write("## Определения\n\n")
            for d in data["definitions"]:
                f.write(f"- {d}\n")
            f.write("\n")
        
        if data["theorems"]:
            f.write("## Теоремы\n\n")
            for t in data["theorems"]:
                f.write(f"- {t}\n")
            f.write("\n")
        
        if data["formulas"]:
            f.write("## Формулы\n\n")
            for fm in data["formulas"]:
                f.write(f"- `{fm}`\n")
            f.write("\n")
        
        if data["examples"]:
            f.write("## Примеры\n\n")
            for ex in data["examples"]:
                f.write(f"- {ex}\n")
            f.write("\n")
    
    return 'OK'
