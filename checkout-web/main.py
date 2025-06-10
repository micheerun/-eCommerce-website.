from flask import Flask, render_template, redirect, url_for, request, abort, flash, session
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os
import smtplib

my_email = os.environ.get('MY_EMAIL')
password_email = os.environ.get("EMAIl_PASSWORD")

app = Flask(__name__)
app.config['SECRET_KEY'] = "API-KEY"
login_manager = LoginManager()
login_manager.init_app(app)

class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class User(UserMixin, db.Model):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))


with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)
def admin_only(function):
    @wraps(function)
    def wrapper():
        if current_user.id != 1:
            abort(404)
        return function
    return wrapper

@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()
        if not user:
            flash('That email does not exist, please try again.')
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password Incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('show_products'))
    return render_template("login.html", current_user= current_user)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        print(name,email,password)
        if not password:
            flash("Password field is empty")
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash("User already exist. Please login")
            return redirect(url_for('login'))
        new_pass =generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
        new_user = User(
            name = name,
            email= email,
            password = new_pass,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect('show_products')
    return render_template("register.html", current_user= current_user)


products = [
    {'id': 1, "name": "Baby yoda's cup", "price":6.99,"image":"Baby yoda's cup.jpg"},
    {'id': 2, "name": "blue lightsaber", "price":10.99,"image":"blue lightsaber.jpg"},
    {'id': 3, "name": "cup from Darth Vader's office", "price":4.99, "image":"cup from Darth Vader's office.jpg"},
    {'id': 4, "name": "cup from episode one", "price":5.99,"image":"cup from episode one.jpg"},
    {'id': 5, "name": "Darth Santa", "price":9.99,"image":"Darth Santa.jpg"},
    {'id': 6, "name": "For Mando", "price":10.99,"image":"For Mando.jpg"},
    {'id': 7, "name": "Mando Fever", "price":9.99,"image":"Mando Fever.jpg"},
    {'id': 8, "name": "Master Yondu's lightsaber", "price":15.99,"image":"Master Yondu's lightsaber.jpg"},
    {'id': 9, "name": "siths", "price":9.99,"image":"siths.jpg"},
]

@app.route("/products")
def show_products():
    return render_template("index.html", products= products)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = int(request.form.get('product_id'))
    product = next((p for p in products if p['id'] == product_id), None)

    if product:
        cart = session.get('cart',[])
        cart.append(product)
        session['cart'] = cart
        session.modified = True
    return redirect(url_for("show_products"))

@app.route('/checkout')
def view_cart():
    cart= session.get("cart",[])
    total = sum(item['price'] for item in cart)
    return render_template("checkout.html", cart=cart, total=total)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))
@app.route('/done', methods=['POST'])
def pay():
    if request.method == 'POST':
        with  smtplib.SMTP("smtp.gmail.com") as connection:
            connection.starttls()
            connection.login(user=my_email, password=password_email)
            connection.sendmail(
                from_addr=my_email,
                to_addrs="micahsmith700@yahoo.com",
                msg=f"Subject: Product on the way\n\nThank you for sopping with us"
            )
        return render_template('done.html')

@app.route('/remove', methods=['POST'])
def remove_from_cart():
    try:
        product_id = int(request.form.get('product_id'))
    except (TypeError, ValueError):
        flash('Invalid product ID')
        return redirect(url_for('view_cart'))

    cart= session.get('cart',[])
    to_remove = next((i for i, item in enumerate(cart) if item['id'] == product_id),None)
    if to_remove is not None:
        del cart[to_remove]

    session['cart'] = cart
    session.modified = True

    return  redirect(url_for('view_cart'))

if __name__ == "__main__":
    app.run(debug=True)