import os
import peewee
from datetime import datetime
from playhouse.shortcuts import ThreadSafeDatabaseMetadata

BASE_PATH = os.path.dirname(__file__)

db = peewee.SqliteDatabase(os.path.join(BASE_PATH, 'data.db'), pragmas={
    'journal_mode': 'wal',
    'cache_size': -1024 * 10})


class QuestionModel(peewee.Model):
    question_id = peewee.IntegerField()
    num = peewee.IntegerField(default=0)
    status = peewee.SmallIntegerField(default=0)

    class Meta:
        database = db
        model_metadata_class = ThreadSafeDatabaseMetadata
        db_table = 'question'


class ArticleModel(peewee.Model):
    question_id = peewee.IntegerField()
    question = peewee.CharField()
    note_id = peewee.CharField()
    title = peewee.CharField()
    user_id = peewee.CharField()
    nickname = peewee.CharField()

    description = peewee.TextField()
    liked_count = peewee.CharField()
    collected_count = peewee.CharField()
    comment_count = peewee.CharField()

    url = peewee.CharField(max_length=1000, null=True)
    video = peewee.CharField(null=True)
    images = peewee.CharField(null=True)
    created = peewee.DateTimeField(default=datetime.now, formats=['%Y-%m-%d %H:%M:%S'])

    class Meta:
        database = db
        model_metadata_class = ThreadSafeDatabaseMetadata
        db_table = 'article'


QuestionModel.create_table()
ArticleModel.create_table()
