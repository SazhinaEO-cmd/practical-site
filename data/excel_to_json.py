import pandas as pd
import json

def read_sheet(path):
    try:
        df = pd.read_excel(path)
        df = df.fillna("")  # заменяем NaN на пустые строки

        # Преобразуем все столбцы с датами в строки
        for col in df.columns:
            if "date" in col.lower():  # автоматически ищем столбцы даты
                df[col] = df[col].apply(lambda x: x.strftime("%Y-%m-%d") if hasattr(x, "strftime") else x)

        return df.to_dict(orient="records")

    except FileNotFoundError:
        print(f"Файл не найден: {path}")
        return []

def convert():
    categories = read_sheet("data/categories.xlsx")
    products = read_sheet("data/products.xlsx")
    news = read_sheet("data/news.xlsx")
    sales = read_sheet("data/sales.xlsx")

    output = {
        "categories": categories,
        "products": products,
        "news": news,
        "sales": sales
    }

    # Сохраняем JSON
    with open("data/catalog.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

    print("Файл обновлен!")

if __name__ == "__main__":
    convert()
