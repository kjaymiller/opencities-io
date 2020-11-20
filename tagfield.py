from connection import client

from elasticsearch_dsl import connections, Document, Text, Date
from flask_wtf import FlaskForm
from wtforms import (
        StringField,
        SubmitField,
        TextAreaField,
        )
from wtforms.fields import Field
from wtforms.widgets import  TextInput
from wtforms import validators

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
    license = StringField('License')
    submit = SubmitField('Submit')


class NewDataSet(Document):
    dataset_name = Text()
    dataset_url = Text()
    portal_url = Text()
    portal_name = Text()
    city = Text()
    region = Text()
    country = Text() 
    tags = Text()
    description = Text()
    license = Text()
    status = Text()

    class Index():
        name = 'open-cities-io-data'
        using = client

