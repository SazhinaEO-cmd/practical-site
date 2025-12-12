
import json
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

def load_data():
    path = "data/catalog.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
DATA = load_data()

@app.route("/")
def index():
    news = DATA.get("news", [])
    sales = DATA.get("sales", [])
    return render_template("index.html", news=news, sales=sales, vision_mode=False)

@app.route("/vision")
def vision():
    return render_template("index.html", vision_mode=True)

def get_data():
    with open("data/catalog.json", "r", encoding="utf-8") as f:
        return json.load(f)

@app.route("/catalog")
def catalog_list():
    data = get_data()
    categories = DATA["categories"]
    return render_template("catalog/list.html", categories=categories)

@app.route("/catalog/<int:category_id>")
def catalog_category(category_id):
    products = [
        p for p in DATA["products"] if p["category_id"] == category_id]
    category = next((c for c in DATA["categories"] if c["id"] == category_id), None)
    return render_template("catalog/category.html", category=category, products=products)

@app.route("/product/<int:product_id>")
def product_page(product_id):
    product = next((p for p in DATA["products"] if p["id"] == product_id), None)
    return render_template("catalog/product.html", product=product)

@app.route("/delivery")
def delivery():
    return render_template("delivery.html")

@app.route("/sales")
def sales():
    sales_list = DATA.get("sales", [])
    return render_template("sales.html", sales=sales_list)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contacts")
def contacts():
    return render_template("contacts.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", vision_mode=False), 404

@app.route("/sitemap")
def sitemap():
    return render_template("sitemap.html", vision_mode=False)

@app.route("/contact/send", methods=["POST"])
def contact_send():
    name = request.form.get("name")
    email = request.form.get("email")
    message = request.form.get("message")

    # сохраняем в текстовый файл
    with open("data/messages.txt", "a", encoding="utf-8") as f:
        f.write(f"{name} | {email} | {message}\n")

    return redirect("/contacts")

if __name__ == "__main__":
    app.run(debug=True)

