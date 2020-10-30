from flask import Flask, render_template, request, redirect
from flask_wtf import FlaskForm
from wtforms import (
        StringField,
        SubmitField,
        TextAreaField,
        )
from wtforms.fields import Field
from wtforms.widgets import  TextInput
from wtforms import validators
from elasticsearch import Elasticsearch 
from dotenv import load_dotenv
import os

load_dotenv('.env')
app = Flask(__name__)
# app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

username, password = (
        os.environ.get('ELASTIC_USERNAME','elastic'),
        os.environ.get('ELASTICSEARCH_PASSWORD'),
        )

client = Elasticsearch(
        cloud_id=os.environ['CLOUD_ID'],
        # hosts = ['localhost'], for local instance
        http_auth=(username, password),
        )


@app.route('/')
def index():
    body = {
            "size": 10,
            "query": {
                "match": {
                    "status": "approved"
                    }
                }
            }

    results = client.search(index='open-cities-io-data', body=body)['hits']['hits']
    return render_template(
            "index.html",
            results=results,
    )


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
                {"term": {"status": "published"}},
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


class TagListField(Field):
    widget = TextInput()

    def _value(self):
        if self.data:
            return u', '.join(self.data)
        else:
            return u''

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = [x.strip() for x in valuelist[0].split(',')]

        else:
            self.data = []

class BetterTagListField(TagListField):
    def __init__(self, label='', validators=None, remove_duplicates=True, **kwargs):
        super(BetterTagListField, self).__init__(label, validators, **kwargs)
        self.remove_duplicates = remove_duplicates

    def process_formdata(self, valuelist):
        super(BetterTagListField, self).process_formdata(valuelist)
        if self.remove_duplicates:
            self.data = list(self._remove_duplicates(self.data))

    @classmethod
    def _remove_duplicates(cls, seq):
        """Remove duplicates in a case insensitive, but case preserving manner"""
        d = {}
        for item in seq:
            if item.lower() not in d:
                d[item.lower()] = True
                yield item


class DataEntry(FlaskForm):
    dataset_name = StringField('Dataset Name', validators=[validators.DataRequired()])
    dataset_url = StringField('Dataset URL', validators=[validators.DataRequired()])
    portal_url = StringField('Portal URL')
    portal_name = StringField('Portal Name')
    city = StringField('City')
    region = StringField('State/Region')
    country = StringField('Country') 
    tags = BetterTagListField('Tags')
    description = TextAreaField('Description')
    license = StringField('Liscense')
    submit = SubmitField('Submit')


@app.route('/add', methods=['GET', 'POST'])
def add():
    form = DataEntry(request.form)

    if request.method=="POST" and form.validate():
        body = {
                "portal_name": form.portal_name.data,
                "portal_url": form.portal_url.data,
                "dataset_name": form.dataset_name.data,
                "dataset_url": form.dataset_url.data,
                "city": form.city.data,
                "region": form.region.data,
                "country": form.country.data,
                "tags": form.tags.data,
                "description": form.description.data,
                "status": "pending"
                }

        flash.success('Your request has been logged for review')
        results = client.add('', body)
        return render_template('/', form=form)

    else:
        return render_template('add.html', form=form)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
