from mongoengine import Document, StringField, BooleanField, DateTimeField, IntField, choices
from wtforms import EmailField

class Task(Document):
    id = IntField(primary_key=True, required=True)
    user_email = EmailField()
    name = StringField(required=True)
    category = StringField(required=True, choices=['work', 'personal'])
    description = StringField()
    completion = BooleanField(default=False)
    finish_date = DateTimeField()
    meeting_date = DateTimeField()
