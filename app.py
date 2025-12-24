
import json
from flask import Flask, render_template, request, redirect, session, flash, abort
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = "practice-secret-key"


# ---------- Работа с данными ----------
def get_data():
    with open("data/catalog.json", "r", encoding="utf-8") as f:
        return json.load(f)
def load_users():
    with open("data/users.json", encoding="utf-8") as f:
        return json.load(f)["users"]

# ---------- Главная ----------
@app.route("/")
def index():
    data = get_data()
    categories = data.get("categories", [])
    if len(categories) >= 3:
        categories_random = random.sample(categories, 3)
    else:
        categories_random = categories
    return render_template("index.html", news=data.get("news", []), sales=data.get("sales", []), categories=categories_random, vision_mode=False)

@app.route("/vision")
def vision():
    data = get_data()
    return render_template("index.html", news=data.get("news", []), sales=data.get("sales", []), categories=data.get("categories", []), vision_mode=True)

# ---------- Каталог ----------
@app.route("/catalog")
def catalog_list():
    data = get_data()
    return render_template("catalog/list.html", categories=data["categories"])

@app.route("/catalog/<int:category_id>")
def catalog_category(category_id):
    data = get_data()
    category = next((c for c in data["categories"] if c["id"] == category_id), None)
    if not category:
        abort(404)
    products = [p for p in data["products"]
                if p["category_id"] == category_id]
    return render_template("catalog/category.html", category=category, products=products)

@app.route("/product/<int:product_id>")
def product_page(product_id):
    data = get_data()
    product = next((p for p in data["products"] if p["id"] == product_id), None)
    if not product:
        abort(404)
    return render_template("catalog/product.html", product=product)

@app.route("/delivery")
def delivery():
    return render_template("delivery.html")

@app.route("/sales")
def sales():
    data = get_data()
    return render_template("sales.html", sales=data["sales"])

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

# ---------- Корзина ----------

def get_cart():
    return session.get("cart", {})

def save_cart(cart):
    session["cart"] = cart
    session.modified = True

@app.route("/cart/add/<int:product_id>")
def cart_add(product_id):
    user = session.get("user")
    if not user or user["role"] != "customer":
        return redirect("/login")
    cart = get_cart()
    pid = str(product_id)
    cart[pid] = cart.get(pid, 0) + 1
    save_cart(cart)
    return redirect(request.referrer or "/cart")

@app.route("/cart/inc/<int:product_id>")
def cart_inc(product_id):
    cart = get_cart()
    pid = str(product_id)
    cart[pid] = cart.get(pid, 0) + 1
    save_cart(cart)
    return redirect("/cart")

@app.route("/cart/dec/<int:product_id>")
def cart_dec(product_id):
    cart = get_cart()
    pid = str(product_id)

    if pid in cart:
        cart[pid] -= 1
        if cart[pid] <= 0:
            cart.pop(pid)

    save_cart(cart)
    return redirect("/cart")

@app.route("/cart")
def cart():
    user = session.get("user")
    if not user or user["role"] != "customer":
        return redirect("/login")
    data = get_data()
    cart = get_cart()
    products = data["products"]

    cart_items = []
    total = 0

    for pid, qty in cart.items():
        product = next((p for p in products if p["id"] == int(pid)), None)
        if product:
            item_total = product["price"] * qty
            total += item_total
            cart_items.append({
                "product": product,
                "qty": qty,
                "total": item_total
            })

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total=total
    )

@app.route("/cart/remove/<int:product_id>")
def cart_remove(product_id):
    cart = get_cart()
    cart.pop(str(product_id), None)
    save_cart(cart)
    return redirect("/cart")

@app.route("/cart/clear")
def cart_clear():
    session.pop("cart", None)
    return redirect("/cart")

# ---------- Обратная связь ----------
@app.route("/contact/send", methods=["POST"])
def contact_send():
    name = request.form.get("name")
    email = request.form.get("email")
    message = request.form.get("message")

    # сохраняем в текстовый файл
    with open("data/messages.txt", "a", encoding="utf-8") as f:
        f.write(f"{name} | {email} | {message}\n")

    return redirect("/contacts")

# ---------- Авторизация ----------    
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        users = load_users()
        user = next(
            (u for u in users if u["username"] == username and u["password"] == password),
            None
        )

        if user:
            session["user"] = {
                "username": user["username"],
                "role": user["role"]
            }
            return redirect("/")
        else:
            flash("Неверный логин или пароль")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------- Админка ----------
@app.route("/admin")
def admin():
    user = session.get("user")
    if not user or user["role"] != "admin":
        return redirect("/login")
    try:
        with open("data/orders.json", "r", encoding="utf-8") as f:
            orders = json.load(f)
    except FileNotFoundError:
        orders = []
    return render_template("admin.html", orders = orders)

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# ---------- Формирование заказа ----------
@app.route("/order/create")
def create_order():
    if "user" not in session or "cart" not in session:
        return redirect("/login")

    # загрузка заказов
    try:
        with open("data/orders.json", "r", encoding="utf-8") as f:
            orders = json.load(f)
    except FileNotFoundError:
        orders = []

    data = get_data()
    products = data["products"]

    cart = session["cart"]
    order_items = []
    total = 0

    for pid, qty in cart.items():
        product = next((p for p in products if p["id"] == int(pid)), None)
        if not product:
            continue
        sum_item = product["price"] * qty
        total += sum_item

        order_items.append({
            "product_id": product["id"],
            "name": product["name"],
            "price": product["price"],
            "qty": qty,
            "sum": sum_item
        })

    order = {
        "id": len(orders) + 1,
        "user": session["user"]["username"],
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": "оформлен",
        "total": total,
        "items": order_items
    }

    orders.append(order)

    with open("data/orders.json", "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

    session.pop("cart", None)

    return redirect("/order/success")

@app.route("/order/success")
def order_success():
    return render_template("order_success.html")
# смена статуса заказа админ
@app.route("/admin/order/status", methods=["POST"])
def change_order_status():
    order_id = int(request.form.get("order_id"))
    new_status = request.form.get("status")

    with open("data/orders.json", "r", encoding="utf-8") as f:
        orders = json.load(f)

    for order in orders:
        if order["id"] == order_id:
            order["status"] = new_status
            break

    with open("data/orders.json", "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

    return redirect("/admin")
# отслеживание заказа
@app.route("/orders")
def my_orders():
    user = session.get("user")
    if not user or user["role"] != "customer":
        return redirect("/login")

    try:
        with open("data/orders.json", encoding="utf-8") as f:
            orders = json.load(f)
    except FileNotFoundError:
        orders = []

    user_orders = [
        o for o in orders if o["user"] == user["username"]
    ]

    return render_template("orders.html", orders=user_orders)
# поисковик
@app.route("/search")
def search():
    query = request.args.get("q", "").strip().lower()

    data = get_data()
    products = data["products"]

    results = []
    if query:
        results = [
            p for p in products
            if query in p["name"].lower()
        ]

    return render_template(
        "catalog/search.html",
        query=query,
        results=results
    )


if __name__ == "__main__":
    app.run(debug=True)

