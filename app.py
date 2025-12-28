
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
    
def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_users(users):
    with open("data/users.json", "w", encoding="utf-8") as f:
        json.dump({"users": users}, f, ensure_ascii=False, indent=2)
# ---------- Главная ----------
@app.route("/")
def index():
    data = get_data()
    # --- 3 случайные категории ---
    categories = data.get("categories", [])
    if len(categories) >= 3:
        categories_random = random.sample(categories, 3)
    else:
        categories_random = categories
    # --- сортировка новостей от новых к старым ---
    news = data.get("news", [])
    news_sorted = sorted(
        news,
        key=lambda n: datetime.strptime(n["date"], "%Y-%m-%d"),
        reverse=True
    )
    return render_template("index.html", news=news_sorted, sales=data.get("sales", []), categories=categories_random, vision_mode=False)

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

@app.route("/news/<int:news_id>")
def news_detail(news_id):
    data = get_data()
    news_list = data.get("news", [])

    news_item = next((n for n in news_list if n["id"] == news_id), None)

    if not news_item:
        abort(404)

    return render_template("news_detail.html", news=news_item)

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
    text = request.form.get("message")

    messages = load_json("data/messages.json")

    messages.append({
        "id": int(datetime.now().timestamp()),
        "type": "contact",
        "topic": "Сообщение с формы контактов",
        "status": "open",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "from": {
            "role": "guest",
            "username": session.get("user", {}).get("username") if session.get("user") else email,
            "email": email,
            "name": name
        },
        "messages": [
            {
                "author": "customer",
                "text": text,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
        ]
    })

    save_json("data/messages.json", messages)
    return redirect("/contacts")

# ---------- Авторизация ----------    
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()
        action = request.form.get("action")

        users_data = load_json("data/users.json")
        users = users_data.get("users", [])
        
        user = next(
            (u for u in users if u["username"] == username), None)

        if action == "login":
            if user and user["password"] == password:
                session["user"] = {"username": user["username"],"role": user["role"]}
                return redirect("/")
            else:
                flash("Пользователь не зарегистрирован или неверный логин/пароль.Нажмите «Регистрация»")
                return render_template("login.html")
        if action == "register":
            if user:
                session["user"] = {"username": user["username"], "role": user["role"]}
                return redirect("/")
            else:
                new_user = {"id":max(u["id"] for u in users) + 1 if users else 1,
                            "username": username,
                            "password": password,
                            "role": "customer"}
                users.append(new_user)
                save_users(users)

                session["user"] = {"username": new_user["username"], "role": new_user["role"]}
                return redirect("/")

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

# ---------- Страница сообщений покупателя ----------
@app.route("/messages")
def messages():
    if not session.get("user"):
        return redirect("/login")

    messages = load_json("data/messages.json")

    user_msgs = [
        d for d in messages
        if d["from"]["username"] == session["user"]["username"]
    ]

    return render_template("messages.html", messages=user_msgs)


# ---------- Отправка сообщения от покупателя ----------
@app.route("/messages/create", methods=["POST"])
def create_dialog():
    if not session.get("user"):
        return redirect("/login")

    dialogs = load_json("data/messages.json")

    dialog = {
        "id": int(datetime.now().timestamp()),
        "topic": request.form["topic"],
        "status": "open",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "from": {
            "username": session["user"]["username"]
        },
        "messages": [
            {
                "username": session["user"]["username"],
                "text": request.form["message"],
                "date": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
        ]
    }

    dialogs.append(dialog)
    save_json("data/messages.json", dialogs)

    return redirect("/messages")
# ---------- Отправка сообщения в существующий диалог - покупатель ----------
@app.route("/messages/send/<int:dialog_id>", methods=["POST"])
def send_message(dialog_id):
    dialogs = load_json("data/messages.json")

    for d in dialogs:
        if d["id"] == dialog_id and d["status"] == "open":
            d["messages"].append({
                "username": session["user"]["username"],
                "text": request.form["message"],
                "date": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            break

    save_json("data/messages.json", dialogs)
    return redirect("/messages")

# ---------- Сообщения администратора ----------
@app.route("/admin/messages")
def admin_messages():
    if not session.get("user") or session["user"]["role"] != "admin":
        return redirect("/login")

    messages = load_json("data/messages.json")
    new_messages, new_orders = get_admin_counters()
    return render_template("admin_messages.html",messages=messages,new_messages=new_messages,new_orders=new_orders)

# ---------- Отправка сообщения в существующий диалог - админ ----------
@app.route("/admin/messages/answer/<int:id>", methods=["POST"])
def admin_answer(id):
    dialogs = load_json("data/messages.json")

    for d in dialogs:
        if d["id"] == id and d["status"] == "open":
            d["messages"].append({
                "username": "admin",
                "text": request.form["answer"],
                "date": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            break

    save_json("data/messages.json", dialogs)
    return redirect("/admin/messages")
# ---------- Закрытие диалога - админ ----------
@app.route("/admin/messages/close/<int:id>", methods=["POST"])
def admin_close_dialog(id):
    dialogs = load_json("data/messages.json")

    for d in dialogs:
        if d["id"] == id:
            d["status"] = "closed"
            break

    save_json("data/messages.json", dialogs)
    return redirect("/admin/messages")
# ---------- Новый заказ/сообщение ----------
def get_admin_counters():
    messages = load_json("data/messages.json")
    orders = load_json("data/orders.json")

    new_messages = 0
    for d in messages:
        if d.get("status") == "open":
            last = d["messages"][-1]
            if last.get("username") != "admin":
                new_messages += 1
    new_orders = len([o for o in orders if o.get("status") == "оформлен"])

    return new_messages, new_orders

@app.context_processor
def inject_admin_counters():
    user = session.get("user")
    if user and user.get("role") == "admin":
        new_messages, new_orders = get_admin_counters()
        return dict(
            new_messages=new_messages,
            new_orders=new_orders
        )
    return dict(new_messages=0, new_orders=0)
# ---------- Удаление заказов ----------
@app.route("/admin/order/delete/<int:id>", methods=["POST"])
def delete_order(id):
    if session.get("user", {}).get("role") != "admin":
        abort(403)

    orders = load_json("data/orders.json")
    orders = [o for o in orders if o["id"] != id]
    save_json("data/orders.json", orders)

    return redirect("/admin")

if __name__ == "__main__":
    app.run(debug=True)

