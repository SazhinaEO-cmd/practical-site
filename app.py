from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html", vision_mode=False)

@app.route("/vision")
def vision():
    return render_template("index.html", vision_mode=True)

@app.route("/catalog")
def catalog_list():
    categories = [
        {"id":1, "name": "Посуда"},
        {"id":2, "name": "Текстиль"},
        {"id":3, "name": "Декор"},
        {"id":4, "name": "Хозяйственные товары"},
    ]
    return render_template("catalog/list.html", categories=categories)

@app.route("/catalog/<int:category_id>")
def catalog_category(category_id):
    # Временные данные для теста
    products = [
        {"id": 1, "name": "Набор тарелок", "price": 1200},
        {"id": 2, "name": "Стаканы стеклянные", "price": 850},
        {"id": 3, "name": "Салфетки хлопковые", "price": 400},
    ]
    return render_template("catalog/category.html", category_id=category_id, products=products)

@app.route("/product/<int:product_id>")
def product_page(product_id):
    product = {
        "name": "Набор тарелок",
        "description": "Классический набор из керамики",
        "price": 1200
    }
    return render_template("catalog/product.html", product=product)

@app.route("/delivery")
def delivery():
    return render_template("delivery.html")

@app.route("/sales")
def sales():
    return render_template("sales.html")

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

if __name__ == "__main__":
    app.run(debug=True)