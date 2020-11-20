from functools import wraps
import json
from connection import client
from flask import (
        Flask,
        render_template,
        request,
        redirect,
        flash,
        url_for,
        session,
        )

from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
from urllib.parse import urlencode
from werkzeug.exceptions import HTTPException
import os

load_dotenv('.env')

es_index = os.environ['ES_INDEX'] # Points to the index to add data to

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['FLASK_SECRET']

# OAuth Login and Setup
oauth = OAuth(app)
auth0 = oauth.register(
        'auth0',
        client_id=os.environ['AUTH0_CLIENT'],
        client_secret=os.environ['AUTH0_SECRET'],
        api_base_url=os.environ['AUTH0_API_BASE_URL'],
        authorize_url=os.environ['AUTH0_AUTHORIZATION_URL'],
        access_token_url= os.environ['AUTH0_TOKEN_URL'],
        client_kwargs={'scope': 'openid profile email'},
        )


@app.route('/callback')
def callback_handling():
    # Handles response from token endpoint
    auth0.authorize_access_token()
    resp = auth0.get('userinfo')
    userinfo = resp.json()

    # Store the user information in flask session.
    session['jwt_payload'] = userinfo
    session['profile'] = {
        'user_id': userinfo['sub'],
        'name': userinfo['name'],
        'picture': userinfo['picture']
    }
    return redirect('/')


@app.route('/login')
def login():
    return auth0.authorize_redirect(redirect_uri=os.environ['AUTH0_REDIRECT_URL'])


def requires_auth(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    if 'profile' not in session:
      # Redirect to Login page here
      return redirect('/')
    return f(*args, **kwargs)

  return decorated


@app.route('/logout')
def logout():
    # Clear session stored data
    session.clear()
    # Redirect user to logout endpoint
    params = {'returnTo': url_for('index', _external=True), 'client_id': 'aFJ8iXzY0GhOGza1aa8MLgeSDmQi0akA'}
    return redirect(auth0.api_base_url + '/v2/logout?' + urlencode(params))


# Main Web Site Routing
@app.route('/')
def index():
    """Homepage"""
    size = request.args.get('size', 10)
    body = {
            "size": size,
            "query": {
                "match_all": {
                    }
                }
            }

    results = client.search(index=es_index, body=body)['hits']['hits']
    userinfo=session.get('profile', None)
    return render_template(
            "index.html",
            results=results,
            userinfo=userinfo,
    )

@app.route('/search')
def search():
    """Return Search Results Based on Products"""
    query = request.args.get('query', '')
    body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["title", "region^2", "publisher.name"],
            }
        },
    }

    results = client.search(index='open-cities-io-data', body=body)['hits']['hits']

    return render_template(
            "search.html",
            query=query,
            results=results,
    )


@app.route('/portal/<portal_name>')
def get_portal(portal_name):
    """Opens all the documents belonging to a specific portal. This currently loads data from elasticsearch."""
    body = {
            "query": {
                "match": {"portal_name": portal_name}
                }
            }
    results = client.search(index=es_index, body=body)['hits']['hits']
    return render_template(
            "search.html",
            query=portal_name,
            results=results,
    )


@app.route('/pages/<_doc>')
def get_doc(_doc:str):
    """Opens a record for a single api"""
    doc = client.get('open-cities-io-data', _doc)
    return render_template('doc.html', doc=doc) 

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
