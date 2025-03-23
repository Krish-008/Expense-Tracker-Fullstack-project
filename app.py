from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Expense Model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Create the database tables
with app.app_context():
    db.create_all()

# Login Manager
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home Page - Show Expenses
@app.route('/')
@login_required
def home():
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', expenses=expenses)

# Add Expense Page
@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        name = request.form['name']
        amount = float(request.form['amount'])
        category = request.form['category']

        # Save to database
        new_expense = Expense(name=name, amount=amount, category=category, user_id=current_user.id)
        db.session.add(new_expense)
        db.session.commit()

        return redirect(url_for('home'))

    return render_template('add_expense.html')

# Delete Expense
@app.route('/delete_expense/<int:id>', methods=['POST'])
@login_required
def delete_expense(id):
    expense = Expense.query.get(id)
    if expense:
        db.session.delete(expense)
        db.session.commit()
    return redirect(url_for('home'))

# Edit Expense
@app.route('/edit_expense/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_expense(id):
    expense = Expense.query.get(id)
    
    if request.method == 'POST':
        expense.name = request.form['name']
        expense.amount = request.form['amount']
        expense.category = request.form['category']
        db.session.commit()
        return redirect(url_for('home'))
    
    return render_template('edit_expense.html', expense=expense)

# Summary Page
@app.route('/summary')
@login_required
def summary():
    total_expenses = db.session.query(db.func.sum(Expense.amount)).filter_by(user_id=current_user.id).scalar() or 0
    categories = db.session.query(Expense.category, db.func.sum(Expense.amount)).filter_by(user_id=current_user.id).group_by(Expense.category).all()
    
    return render_template('summary.html', total_expenses=total_expenses, categories=categories)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('home'))
    
    return render_template('register.html')


# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    # If the user is already logged in, redirect them to the home page
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):  # Verify the hashed password
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

# Logout Route

@app.route('/logout')
def logout():
    # If you're using Flask-Login for authentication, log the user out
    logout_user()
    
    # Alternatively, if you're using the session, you can pop the user_id like this
    from flask import session
    session.pop('user_id', None)  # Remove user_id from session

    flash('You have been logged out.', 'info')  # Optional: Add a flash message
    return redirect(url_for('login'))
if __name__ == '__main__':
    app.run(debug=True)
