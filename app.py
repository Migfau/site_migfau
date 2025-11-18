from flask import Flask, render_template, request, redirect, url_for, session
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Caminho do projeto
BASE_DIR = '/home/migfau/Documents/VSCode/Site'

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
PRODUCTS_FILE = os.path.join(BASE_DIR, 'products.json')
COMMENTS_FILE = os.path.join(BASE_DIR, 'comments.json')
USERS_FILE = os.path.join(BASE_DIR, 'users.json')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Garantir pastas
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Garantir arquivos básicos
for file in [PRODUCTS_FILE, COMMENTS_FILE, USERS_FILE]:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            if "users" in file:
                json.dump([], f)
            else:
                json.dump([], f)


# ---------- FUNÇÕES ----------

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)


def load_users():
    users = load_json(USERS_FILE)

    # Garantir estrutura completa
    for u in users:
        if "username" not in u:
            u["username"] = u.get("name", "")
        if "is_admin" not in u:
            u["is_admin"] = False

    # Sempre manter MIGFAU como admin supremo
    for u in users:
        if u["username"] == "migfau":
            u["is_admin"] = True

    return users


def save_users(users):
    save_json(USERS_FILE, users)


# ---------- ROTAS ----------

@app.route('/')
def index():
    products = load_json(PRODUCTS_FILE)
    comments = load_json(COMMENTS_FILE)
    users = load_users()

    logged = "username" in session
    is_admin = session.get("is_admin", False)

    return render_template('index.html',
                           products=products,
                           comments=comments,
                           logged_in=logged,
                           is_admin=is_admin)


# -------- Criar Conta --------
@app.route('/register', methods=['POST'])
def register():
    name = request.form["name"]
    username = request.form["username"]
    password = request.form["password"]

    users = load_users()

    # Nick já existe?
    if any(u["username"] == username for u in users):
        return "Usuário já existe."

    new_user = {
        "name": name,
        "username": username,
        "password": password,
        "is_admin": False
    }

    # Forçar migfau como admin
    if username == "migfau":
        new_user["is_admin"] = True

    users.append(new_user)
    save_users(users)

    return redirect('/')


# -------- Login --------
@app.route('/login', methods=['POST'])
def login():
    username = request.form["username"]
    password = request.form["password"]

    users = load_users()

    for u in users:
        if u["username"] == username and u["password"] == password:
            session["username"] = u["username"]
            session["is_admin"] = u["is_admin"]
            return redirect('/')

    return "Login inválido."


# -------- Logout --------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# -------- Produtos --------
@app.route('/add_product', methods=['POST'])
def add_product():
    if not session.get("is_admin"):
        return redirect('/')

    name = request.form['name']
    desc = request.form['desc']
    file = request.files['image']

    if file:
        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)

        products = load_json(PRODUCTS_FILE)
        products.append({
            'name': name,
            'desc': desc,
            'image': f'/static/uploads/{filename}'
        })
        save_json(PRODUCTS_FILE, products)

    return redirect('/')


@app.route('/remove_product/<int:index>')
def remove_product(index):
    if not session.get("is_admin"):
        return redirect('/')

    products = load_json(PRODUCTS_FILE)

    if 0 <= index < len(products):
        img_path = os.path.join(BASE_DIR, products[index]['image'].replace('/static/', 'static/'))
        if os.path.exists(img_path):
            os.remove(img_path)

        products.pop(index)
        save_json(PRODUCTS_FILE, products)

    return redirect('/')


# -------- Comentários --------
@app.route('/comment', methods=['POST'])
def comment():
    if not "username" in session:
        return redirect('/')

    text = request.form['text']
    user = session["username"]

    comments = load_json(COMMENTS_FILE)
    comments.append({
        "name": user,
        "text": text
    })
    save_json(COMMENTS_FILE, comments)

    return redirect('/')


@app.route('/remove_comment/<int:index>')
def remove_comment(index):
    if not session.get("is_admin"):
        return redirect('/')

    comments = load_json(COMMENTS_FILE)
    if 0 <= index < len(comments):
        comments.pop(index)
        save_json(COMMENTS_FILE, comments)

    return redirect('/')


# -------- Painel admin: usuários --------
@app.route('/users')
def users_panel():
    if not session.get("is_admin"):
        return redirect('/')

    users = load_users()
    return render_template('users.html', users=users)


@app.route('/toggle_admin/<username>')
def toggle_admin(username):
    if not session.get("is_admin"):
        return redirect('/')

    users = load_users()

    # impedir remover adm do migfau
    if username == "migfau":
        return redirect('/users')

    for u in users:
        if u["username"] == username:
            u["is_admin"] = not u["is_admin"]

    save_users(users)
    return redirect('/users')


# -------- RUN --------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
