# app.py
from flask import Flask, render_template, request, redirect, url_for, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from bson.objectid import ObjectId

app = Flask(__name__)
app.config['MONGO_URI'] = "mongodb://localhost:27017/ecommerce"
app.secret_key = 'b"AE\x93\xeb\x84\x1ai\x9d\x96J+\x8aA2\x1dW`\x83\x84D0\xa5Y"'

mongo = PyMongo(app)
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    return User(str(user['_id']), user['username']) if user else None

@app.route('/')
def index():
    products = mongo.db.products.find()
    return render_template('index.html', products=products)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        
        if mongo.db.users.find_one({"username": username}):
            return "User already exists"
        
        mongo.db.users.insert_one({"username": username, "password": hashed_password})
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = mongo.db.users.find_one({"username": username})
        if user and check_password_hash(user['password'], password):
            login_user(User(str(user['_id']), user['username']))
            return redirect(url_for('index'))
        
        return "Invalid credentials"
    
    return render_template('login.html')

@app.route('/product/<product_id>')
def product_detail(product_id):
    product = mongo.db.products.find_one({"_id": ObjectId(product_id)})
    return render_template('product_detail.html', product=product)

@app.route('/add_to_cart/<product_id>')
@login_required
def add_to_cart(product_id):
    cart_item = mongo.db.cart.find_one({"user_id": current_user.id, "product_id": product_id})
    if cart_item:
        mongo.db.cart.update_one({"_id": cart_item['_id']}, {"$inc": {"quantity": 1}})
    else:
        mongo.db.cart.insert_one({"user_id": current_user.id, "product_id": product_id, "quantity": 1})
    return redirect(url_for('view_cart'))

@app.route('/cart')
@login_required
def view_cart():
    cart_items = list(mongo.db.cart.find({"user_id": current_user.id}))
    products = []
    for item in cart_items:
        product = mongo.db.products.find_one({"_id": ObjectId(item['product_id'])})
        if product:
            product['quantity'] = item['quantity']
            products.append(product)
    return render_template('cart.html', products=products)

@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    cart_items = list(mongo.db.cart.find({"user_id": current_user.id}))
    if cart_items:
        mongo.db.orders.insert_one({"user_id": current_user.id, "items": cart_items, "status": "Pending"})
        mongo.db.cart.delete_many({"user_id": current_user.id})  # Clear cart after checkout
    return "Order placed successfully"

if __name__ == '__main__':
    app.run(debug=True)
