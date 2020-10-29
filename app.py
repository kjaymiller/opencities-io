from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired
from elasticsearch import Elasticsearch 
from elasticsearch_dsl import Document, Text
import os

app = Flask(__name__)
username, password = (
        os.environ.get('ELASTIC_USERNAME','elastic'),
        os.environ.get('ELASTIC_PASSWORD'),
        )
host = f"{username}:{password}@localhost"
client = Elasticsearch(hosts=[host])

class DataEntry(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    url = StringField('url', validators=[DataRequired()])
    data_type = StringField('data_type', validators=[DataRequired()])
    geo_type = StringField('geo_type', validators=[DataRequired()])
    area_name = StringField('region', validators=[DataRequired()])
    country = StringField('country', validators=[DataRequired()])  
    

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search')
def search():
    query = request.args.get('query', '')
    body = {
        "query": {
            "bool": {
                "must": [
                    {"multi_match": {
                        "query": query,
                        "fields": ["city^2", "region^2", "portal_name", "datasets_name^3"]}},
                ],
            "filter": [
                {"term": {"status": "approved"}},
                ] 
            }
        }
    }

    results = client.search(index='open-cities-io-data', body=body)['hits']['hits']

    return render_template(
            "search.html",
            query=query,
            results=results,
    )


@app.route('/pages/<_doc>')
def page(_doc:str):
   doc = client.get('open-cities-io-data', _doc)
   return render_template('doc.html', doc=doc) 


@app.route('/add', methods=["POST"])
def add():
    body = request.form.get()
    client.add(body)

if __name__ == '__main__':
    app.run()
