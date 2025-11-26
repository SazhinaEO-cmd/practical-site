from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html", vision_mode=False)

@app.route("/vision")
def vision():
    return render_template("index.html", vision_mode=True)

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", vision_mode=False), 404

@app.route("/sitemap")
def sitemap():
    return render_template("sitemap.html", vision_mode=False)

if __name__ == "__main__":
    app.run(debug=True)

