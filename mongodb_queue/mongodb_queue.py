# -*- coding: utf-8 -*-
"""Main module."""
import pymongo
from datetime import datetime
from cerberus import Validator
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


class PayloadValidationError(Exception):
    """Raised when payload validation failis"""


class MongodbConnector:
    """Connector to mongodb DATABASE"""

    @staticmethod
    def get_db(dbname=None,
               check_availability=False,
               mongodb_uri='mongodb://localhost:27017/{}',
               **kwargs):
        """Get database connection

        :param dbname: database name
        :param check_availability: check db availability
        :param mongodb_uri: uri template as python format string
        :returns: database connection client or `ConnectionFailure` exception
        """
        # celery complaining about connection happened before the fork
        # pass `connect=False` to MongoClient to connect on first operation
        db_name = dbname or ''
        client = MongoClient(mongodb_uri.format(db_name),
                             connect=False, **kwargs)

        # check client availability, see:
        # https://api.mongodb.com/python/current/api/pymongo/mongo_client.html
        if check_availability:
            try:
                # The ismaster command is cheap and does not require auth.
                client.admin.command('ismaster')
            except ConnectionFailure as ex:
                raise ex

        return client


class BaseMongodbQueue:
    '''Queue implementation'''

    _queue_name = 'queue_dummy'

    _payload_schema = {
        'value': {'type': 'string', 'required': True},
    }

    _queue_schema = {
        'created_at': {
            'type': 'datetime',
            'required': True,
        },
        'finished_at': {
            'type': 'datetime',
            'nullable': True,
            'default': None,
            'required': False,
        },
        'priority': {'type': 'integer', 'default': 0},
        'payload': {'type': 'dict', 'required': True},
    }

    _indexes = [
        [('priority', -1)],
        [('created_at', 1)],
        [('finished_at', -1)],
    ]

    _sort_by = [
        ('priority', -1),
        ('created_at', 1),
    ]

    @property
    def col(self):
        return self._conn[self._queue_name]

    @property
    def sort_by(self):
        return self._sort_by

    @sort_by.setter
    def sort_by(self, value):
        self._sort_by = value

    def __init__(self, client, dbname):
        self._db = client
        self._conn = self._db[dbname]

        self._payload_validator = Validator(self._payload_schema)
        self._document_validator = Validator(self._queue_schema)

    def put(self, payload, priority=0, selector={}):
        """Put task into profiles queue
         1
        :param payload: payload to save into the qeue
        :param priority: the bigger the better
        :param selector: key-value pair or more complex query to
        check if item already in queue
        :returns: `InsertOneResult`
        """
        # old code. TODO: delete
        # v = self.payload_validator.validate(payload)
        # if v is False:
        #     return {'vaidation_errors': self.payload_validator.errors}

        payload_normalized = self._payload_validator.normalized(payload)
        v = self._payload_validator.validate(payload)
        if v is False:
            raise PayloadValidationError(
                "Vaidation_errors: {}".format(
                    self._payload_validator.errors))

        document = {
            'payload': payload_normalized,
            'priority': priority,
            'created_at': datetime.utcnow(),
            'finished_at': None,
        }

        task = None
        if selector:
            task = self.col.find_one(selector)

        if task is None:
            task = self.col.insert_one(document)

        return task

    def get(self, length, selector={}):
        """Return sequence of tasks to process.

        :param length: the length of the desired sequence
        :param selector: additional condition to select tasks from queue
        :returns: list of document
        """
        documents = self.col.find(selector).sort(
            self.sort_by).limit(length)

        # for large collections  col.count() after .limit()
        # takes few minutes to complete
        return list(documents)

    def size(self):
        return self.col.count()

    def create_indexes(self):
        idx = []
        for index in self.indexes:
            i = self.col.create_index(index)
            idx.append(i)
        return idx

    def _validate_payload(self, payload):
        return self._payload_validator.validate(payload)

    def _validate_document(self, doc):
        return self._document_validator.validate(doc)
