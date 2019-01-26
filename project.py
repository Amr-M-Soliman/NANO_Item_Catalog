#!/usr/bin/env python3
import random
import httplib2
import json
import string
import requests
from flask import Flask, render_template, \
    request, redirect, jsonify, url_for, flash, \
    session as login_session, make_response, g
from redis import Redis
from flask_httpauth import HTTPBasicAuth
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, CatItem, User
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

# Flask instance
app = Flask(__name__)

auth = HTTPBasicAuth()
redis = Redis()

#Get CLIENT_ID of google sign-in
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

# Connect to database
engine = create_engine('sqlite:///itemcatalog.db',
                       connect_args={'check_same_thread': False},
                       echo=True)
Base.metadata.bind = engine

# Create session
DBSession = sessionmaker(bind=engine)
session = DBSession()


# show login page
@app.route('/login')
def showLogin():
    print("login")
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)

# login by google account of user
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    # Submit request, parse response
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    login_session['provider'] = 'google'

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: ' \
              '150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output

# logout google account of user
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        print('Access Token is None')
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

# login by facebook account of user
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = request.data

    # turn data to string
    access_token = str(access_token)

    # to use access token without (')
    access_token = access_token[access_token.find('\'') + 1:-1]

    print("access token received %s " % access_token)

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_' \
          'type=fb_exchange_token&client_id={0}&client_secret={1}&fb_exchange_token={2}' \
        .format(app_id, app_secret, access_token)
    h = httplib2.Http()
    result = str(h.request(url, 'GET')[1])

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
        Due to the formatting for the result from the server 
        token exchange we have to split the token first on commas 
        and select the first index which gives us the key : value
        for the server access token then we split it on colons 
        to pull out the actual token value and replace the remaining 
        quotes with nothing so that it can be used directly 
        in the graph api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')
    url = 'https://graph.facebook.com/v2.8/me?' \
          'access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture' \
          '?access_token=%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: ' \
              '300px;border-radius: 150px;-webkit-border-radius:' \
              ' 150px;-moz-border-radius: 150px;"> '
    #send flash message
    flash("Now logged in as %s" % login_session['username'])
    return output

#logout user's facebook account
@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?' \
          'access_token=%s' % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"

# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    """ Deletes all user session values and redirect to the main page."""
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()

        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
            # Reset the user's Facebook session.
            del login_session['username']
            del login_session['email']
            del login_session['picture']

        # Reset the user's session.
        del login_session['user_id']
        del login_session['provider']

        flash("You have successfully been logged out.")
        return redirect(url_for('showCategories'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCategories'))



# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
        'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).first()
    return user

def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

@auth.verify_password
def verify_password(username_or_token, password):
    # Try to see if it's a token first
    user_id = User.verify_auth_token(username_or_token)
    if user_id:
        user = session.query(User).filter_by(id=user_id).one()
    else:
        user = session.query(User).filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


# Show all categories
@app.route('/')
@app.route('/categories')
def showCategories():
    categories = session.query(Category).all()
    # Get category items added
    items = session.query(CatItem).all()
    return render_template('publicCategories.html',
                           categories=categories, items=items)

# Show all items of the selected category
@app.route('/categories/<int:category_id>/items')
def showCategory(category_id):

    # Get all categories
    categories = session.query(Category).all()

    # Get category
    category = session.query(Category).filter_by(id=category_id).first()

    # Get name of category
    categoryName = category.name

    # Get all items of a specific category
    categoryItems = session.query(CatItem)\
        .filter_by(category_id=category_id).all()

    # Get count of category items
    categoryItemsCount = session.query(CatItem)\
        .filter_by(category_id=category_id).count()

    return render_template('category.html',
                           categories=categories,
                           categoryItems=categoryItems,
                           categoryName=categoryName,
                           categoryItemsCount=categoryItemsCount)

# Create a new category
@app.route('/category/new', methods=['GET', 'POST'])
def newCategory():

    # Check if the user is logged in
    if 'username' not in login_session:
        return redirect('/login')

    # POST method
    if request.method == 'POST':
        newCategory = Category(name=request.form['name'],
                               user_id=login_session['user_id'])

        # Add the created category to the database
        session.add(newCategory)
        session.commit()

        # Send a flah message
        flash("New Category created!")

        # Redirect to 'showCategories' page
        return redirect(url_for('showCategories'))

    else:

        # Return the page to create a new category
        return render_template('newCategories.html')

# Update a category
@app.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
def editCategory(category_id):

    # Check if the user is logged in
    if 'username' not in login_session:
        return redirect('/login')

    # Get the specific category to be updated by user
    categoryToEdit = session.query(
        Category).filter_by(id=category_id).one()

    # If logged in user != item owner redirect them
    if categoryToEdit.user_id != login_session['user_id']:
        return "<script>function myFunction()" \
               " {alert('You are not authorized to edit this category." \
               " Please create your own category in order to edit.');}" \
               "</script><body onload='myFunction()''>"

    # POST method
    if request.method == 'POST':
        if request.form['name']:
            categoryToEdit.name = request.form['name']

            # Sen a flash message
            flash("Category Edited!")

            # Redirect the user to 'showCategories' page
            return redirect(url_for('showCategories'))
    else:

        #The page to update the category
        return render_template(
            'editCategory.html', category=categoryToEdit)

# Delete a category
@app.route('/category/<int:category_id>/delete', methods=['GET', 'POST'])
def deleteCategory(category_id):

    # Check if the user is logged in
    if 'username' not in login_session:
        return redirect('/login')

    # Get the specific category to be deleted by user
    categoryToDelete = session.query(
        Category).filter_by(id=category_id).one()

    # Git all category items to be deleted
    itemsToDelete = session.query(CatItem).\
                    filter_by(category_id=category_id).all()

    # If logged in user != item owner redirect them
    if categoryToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction()" \
               " {alert('You are not authorized to delete this category.');}" \
               "</script><body onload='myFunction()''>"

    # POST methods
    if request.method == 'POST':

        # Delete all items in category
        for i in itemsToDelete:
            session.delete(i)

        # Delete category
        session.delete(categoryToDelete)
        session.commit()

        # Send flash message
        flash("A category has deleted!")

        # Redirect the user to 'showCategories' page
        return redirect(
            url_for('showCategories'))
    else:
        #The page to delete the category
        return render_template(
            'deleteCategory.html',category=categoryToDelete)

# Show an item
@app.route('/categories/<int:category_id>/items/<int:item_id>')
def showItem(category_id, item_id):

    # Get the specific item by item_id
    item = session.query(CatItem).filter_by(id=item_id).first()

    # Get the creator id of the item
    creator = getUserInfo(item.user_id)
    return render_template('categoryItem.html',
                           item=item, creator=creator)

# Create a new item
@app.route('/category/newitem', methods=['GET', 'POST'])
def newItem():

    # Check if the user is logged in
    if 'username' not in login_session:
        return redirect('/login')

    # POST method
    if request.method == 'POST':
        newItem = CatItem(name=request.form['name'],
                          description=request.form['description'],
                          category_id=request.form['category'],
                          user_id=login_session['user_id'])

        # Add the new item to database
        session.add(newItem)
        session.commit()

        # Send a slush message
        flash("New Game created!")

        # Redirect to the main page
        return redirect(url_for('showCategories'))
    else:

        # Get all categories
        categories = session.query(Category).all()

        # Return the page to create new item
        return render_template('newmenuitem.html', categories=categories)

# Update an item
@app.route('/category/<int:category_id>/item/<int:item_id>/edit:',
           methods=['GET', 'POST'])
def editItem(category_id, item_id):

    # Check if the user is logged in
    if 'username' not in login_session:
        return redirect('/login')

    # Get the item to be updated by item_id
    itemTOEdit = session.query(CatItem).filter_by(id=item_id).one()
    category = session.query(Category).filter_by(id=category_id).one()
    categories = session.query(Category).all()

    # If logged in user != item owner redirect them
    if login_session['user_id'] != itemTOEdit.user_id:
        return "<script>function myFunction()" \
               "{alert('You are not authorized to add items to this category." \
               " Please create your own category in order to add items.');}" \
               "</script><body onload='myFunction()''>"

    # POST methods
    if request.method == 'POST':
        if request.form['name']:
            itemTOEdit.name = request.form['name']
        if request.form['description']:
            itemTOEdit.description = request.form['description']
        if request.form['category']:
            itemTOEdit.category_id = request.form['category']

        # Update the item
        session.add(itemTOEdit)
        session.commit()

        # Send a flash message
        flash("Game edited!")

        # Redirect the user to 'showItem'
        return redirect(url_for('showItem',
                                category_id=category_id,
                                tem_id=item_id))
    else:

        # The page to update the item
        return render_template(
            'editmenuitem.html',category_id=category_id,
                                item_id=item_id,
                                item=itemTOEdit,
                                categories=categories)

# Delete an item
@app.route('/category/<int:category_id>/item/<int:item_id>/delete',
           methods=['GET', 'POST'])
def deleteItem(category_id, item_id):

    # Check if the user is logged in
    if 'username' not in login_session:
        return redirect('/login')

    # Get the item to be deleted by item_id
    itemToDelete = session.query(CatItem).filter_by(id=item_id).one()
    category = session.query(Category).filter_by(id=category_id).one()

    # If logged in user != item owner redirect them
    if login_session['user_id'] != itemToDelete.user_id:
        return "<script>function myFunction()" \
               "{alert('You are not authorized to delete items to this category." \
               " Please create your own category in order to delete items.');}" \
               "</script><body onload='myFunction()''>"

    # POST method
    if request.method == 'POST':

        # Delete the item from database
        session.delete(itemToDelete)
        session.commit()

        # Send a flash message
        flash('Item deleted')

        # Redirect the user to 'showCategory' page
        return redirect(url_for('showCategory', category_id=category_id))
    else:

        # The page to delete the item
        return render_template('deleteMenuItem.html', item=itemToDelete)



# JSON
# JSON API ENDPOINT HERE TO GET ALL CATEGORIES
# JSON for all categories
@app.route('/categories/JSON')
def categoryJSON():
    category = session.query(Category).all()
    return jsonify(Category=[i.serialize for i in category])

# JSON API ENDPOINT HERE TO GET ALL ITEMS OF ONE CATEGORY
@app.route('/categories/<int:category_id>/items/JSON')
def categoryMenuJSON(category_id):
    category = session.query(Category).filter_by(id=category_id).all()
    items = session.query(CatItem).filter_by(
        category_id=category_id).all()
    return jsonify(CatItem=[i.serialize for i in items])

# JSON API ENDPOINT HERE TO GET ONE CATEGORY SPECIFIC  ITEM
@app.route('/categories/<int:category_id>/items/<int:item_id>/JSON')
def menuItemJSON(category_id, item_id):
    oneItem = session.query(CatItem).filter_by(id=item_id).one()
    return jsonify(CatItem=oneItem.serialize)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=7000)
