# -*- coding: utf-8 -*-
"""Main module."""
import pymongo
from datetime import datetime
from cerberus import Validator
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


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
        '_id': {'type': 'string'},
        'done': {'type': 'boolean', 'default': False},
        'created_at': {'type': 'datetime', 'required': True},
        'finished_at': {'type': 'datetime', 'required': False},
        'priority': {'type': 'integer', 'default': 0},
        'payload': {'type': 'dict', 'required': True},
    }
    _indexes = [
        [('created_at', -1)],
        [('finished_at', -1)]
    ]

    @property
    def col(self):
        return self._conn[self._queue_name]

    def __init__(self, client, dbname):
        self._db = client
        self._conn = self._db[dbname]

        self._payload_validator = Validator(self._payload_schema)
        self._document_validator = Validator(self._queue_schema)

    def put(self, payload, priority=0,
            created_at=None, finished_at=None,
            yield_bulk=False):
        """Put task into profiles queue

        :param payload: payload to save into the qeue
        :param priority: the bigger the better
        :param created_at: explicitely set 'created_at' field
        :param finished_at: explicitely set 'finished_at' filed
        :param yield_bulk return
        :returns: mongodb op result or InsertOp
        """
        v = self.payload_validator.validate(payload)
        if v is False:
            return {'vaidation_errors': self.payload_validator.errors}

        payload_ = self.payload_validator.normalized(payload)
        document = {
            'created_at': datetime.utcnow(),
            'finished_at': datetime.fromtimestamp(0),
            'priority': priority,
            'payload': payload_,
        }

        if created_at is not None:
            document['created_at'] = created_at

        if finished_at is not None:
            document['finished_at'] = finished_at
        else:
            # if 'finished_at' is not defined we assign date of
            # datetime.datetime(1970, 1, 1, 7, 0)
            finished_at = datetime.fromtimestamp(0)
            document['finished_at'] = finished_at

        task = self.col.find_one(
            {'payload.key': payload['key']})

        # if task with this username aren't there
        if task is None:
            # add new task
            if yield_bulk:
                task = pymongo.InsertOne(document)
            else:
                task = self.conn[self.queue_name].insert_one(document)
                logger.debug('Task added: {}'.format(task.inserted_id))

        return task

    def get(self, length):
        """Return sequence of tasks to process.
        """
        documents = self.conn[self.queue_name].find(
            {
                'payload.key': False,
            }
        ).sort([('finished_at', 1), ('priority', -1)]).limit(lenghth)

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
