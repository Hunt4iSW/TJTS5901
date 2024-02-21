from flask import Flask, redirect, render_template, request, session, url_for, flash
from functools import wraps
from forms import RegistryForm, LoginForm
import stockmarket as db
from tools import hash_password
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.secret_key = '!secret'
csrf = CSRFProtect(app) # Add CSRF-protection (Cross-site request forgery) to the Flask-app.

db.reset() # TODO: Remove once done with testing the database.
db.test_populate() # TODO: Remove once done with testing the database.

if __name__ == '__main__':
    """Boots in a Flask-app environment.
    Defines the host, port and debug-mode for the app.
    """
    app.run(host='127.0.0.1', port=8080, debug=True)


def auth_required(f):
    """Decorator function for authenticating the users.
    Directs to login page in case not verified into session.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'trader' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    """Redirects the user to the front page.
    """
    return redirect(url_for('dashboard'))


@app.route('/registry', methods=['GET'])
def registry():
    """Creates a trader registry page.
    """
    form = RegistryForm()
    return render_template('registry.html', form=form)


@app.route('/register', methods=['POST'])
def register():
    """Handles the registering of the trader.
    """
    form = RegistryForm(request.form)
    if request.form.get("cancel", ""):
        return redirect(url_for('login'))
    if not form.validate():
        return render_template('registry.html', form=form)
    first_name = form.first_name.data.strip().lower().capitalize()
    last_name = form.last_name.data.strip().lower().capitalize()
    tradername = form.tradername.data.strip() # TODO: Decide whether the tradername should be caseinsensitive or not.
    hashword = hash_password(form.password.data)
    add_trader(first_name, last_name, tradername, hashword)
    flash(f'New trader "{tradername}" registered!', 'info')
    return redirect(url_for('login'))


@app.route('/login', methods=['GET'])
def login():
    """Creates a trader login page.
    """
    form = LoginForm()
    return render_template('login.html', form=form)
    

@app.route('/auth', methods=['POST'])
def auth():
    """Handles the authentication of the login.
    """
    form = LoginForm(request.form)
    if not form.validate():
        return render_template('login.html', form=form)
    tradername = form.tradername.data.strip()
    trader = get_trader(tradername)
    session['trader'] = trader
    return redirect(url_for('dashboard'))


@app.route('/logout', methods=['GET'])
def logout():
    """Clears the session, logging the user out.
    """
    session.clear()
    return redirect('/')


@app.route('/dashboard', methods=['GET'])
@auth_required
def dashboard():
    """Shows the trader dashboard.
    """
    return render_template('dashboard.html', trader=session['trader'])


@app.route('/offer_listing', methods=['GET'])
@auth_required
def offer_listing():
    """Lists all available offers.
    """
    stocks = get_stocks()
    for stock in stocks:
        offers = get_stock_offers(stock['stockid'])
        stock['offers'] = offers
    return render_template('offer_listing.html', stocks=stocks)


@app.route('/bid_listing', methods=['GET'])
@auth_required
def bid_listing():
    """Lists all available bids.
    """
    stocks = get_stocks()
    for stock in stocks:
        bids = get_stock_bids(stock['stockid'])
        stock['bids'] = bids
    return render_template('bid_listing.html', stocks=stocks)


@app.route('/orders', methods=['GET'])
@auth_required
def orders():
    orders_query = 'SELECT * FROM orders'
    orders = db.query(orders_query)
    for order in orders: # Prints order results to console
        print(order['id'])
        print(order['trader_id'])
        print(order['stock_id'])
        print(order['date'])
        print(order['quantity'])
        print(order['is_buy'])
        print(order['price'])
    return "Orders printed!"


def get_trader(tradername):
    trader = db.query("SELECT traderid, first_name, last_name, tradername FROM traders WHERE tradername = ?", (tradername,), True)
    return trader


def add_trader(first_name, last_name, tradername, hashword):
    db.modify("INSERT INTO traders (first_name, last_name, tradername, hashword) VALUES (?, ?, ?, ?)", (first_name, last_name, tradername, hashword))


def get_stocks():
    stocks_query = "SELECT * FROM stocks"
    stocks = db.query(stocks_query)
    return stocks


def get_stock_offers(stockid):
    # Fetch orders where `selling` is 1 for the current stock
    offers = db.query("SELECT * FROM orders WHERE stockid = ? AND selling = 1", (stockid,))
    return offers


def get_stock_bids(stockid):
    # Fetch orders where `selling` is 1 for the current stock
    bids = db.query("SELECT * FROM orders WHERE stockid = ? AND selling = 0", (stockid,))
    return bids