#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `mongodb_queue` package."""

import pytest

from click.testing import CliRunner

import pymongo
from mongodb_queue import cli
from mongodb_queue.mongodb_queue import BaseMongodbQueue


TEST_DATABASE_NAME = 'test_mqueue'
QUEUE_COLLECTION = 'queue_queue'


class MongodbQueue(BaseMongodbQueue):
    _queue_name = QUEUE_COLLECTION
    _payload_schema = {
        'key': {'type': 'string', 'required': True},
        'required_value': {'type': 'string', 'required': True},
        'default_value': {'type': 'string', 'default': 'nope'},
    }


@pytest.fixture(scope='function')
def test_db():
    """Test that we're using testing database,
    load module level fixture, ensure
    collection will be droped after execution of the test case"""
    db = pymongo.MongoClient()
    conn = db[TEST_DATABASE_NAME]

    assert conn.name == TEST_DATABASE_NAME
    yield db, conn
    conn[QUEUE_COLLECTION].drop()


@pytest.fixture
def response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get('https://github.com/audreyr/cookiecutter-pypackage')


def test_content(response):
    """Sample pytest test function with the pytest fixture as an argument."""
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string


def test_mongodb_queue_init_base_class():
    from mongodb_queue.mongodb_queue import BaseMongodbQueue

    client = pymongo.MongoClient()
    q = BaseMongodbQueue(client, TEST_DATABASE_NAME)
    assert q.size() == 0


def test_mongodb_queue_put(test_db):
    from mongodb_queue.mongodb_queue import PayloadValidationError

    client, _ = test_db
    q = MongodbQueue(client, TEST_DATABASE_NAME)

    payload = {
        'key': 'alpha',
        'required_value': 'yes',
    }
    task = q.put(payload, priority=5)
    assert isinstance(task, pymongo.results.InsertOneResult)
    assert q.size() == 1

    # save in cycle
    for key in range(6):
        payload = {
            'key': str(key),
            'required_value': 'yes' if key % 2 == 0 else 'nope',
            'default_value': 'yes!'
        }
        task = q.put(payload, priority=5)

    assert q.size() == 7

    # check validation error
    with pytest.raises(PayloadValidationError):
        payload = {
            'key': 'test'
        }
        q.put(payload, priority=0)


def test_mongodb_queue_put_with_selectors(test_db):
    client, _ = test_db
    q = MongodbQueue(client, TEST_DATABASE_NAME)

    # save in cycle
    for key in range(7):
        payload = {
            'key': str(key),
            'required_value': 'yes' if key % 2 == 0 else 'nope',
            'default_value': 'yes!'
        }
        task = q.put(payload, priority=key)

    assert task is not None
    assert q.size() == 7

    data_from_get = q.get(4, selector={'payload.required_value': 'yes'})
    assert len(data_from_get) == 4
    assert len(data_from_get) == q.col.count({'payload.required_value': 'yes'})


def test_mongodb_queue_delete(test_db):
    client, _ = test_db
    q = MongodbQueue(client, TEST_DATABASE_NAME)

    # save in cycle
    for key in range(7):
        payload = {
            'key': str(key),
            'required_value': 'yes' if key % 2 == 0 else 'nope',
            'default_value': 'yes!'
        }
        q.put(payload, priority=key)

    assert q.size() == 7

    tasks = q.get(1)
    result = q.delete({'_id': tasks[0]['_id']})

    assert isinstance(result, pymongo.results.DeleteResult)
    assert q.size() == 6


def test_mongodb_queue_zero_length(test_db):
    client, _ = test_db

    q = MongodbQueue(client, TEST_DATABASE_NAME)
    assert q.size() == 0


def test_mongodb_queue_get_sort_by(test_db):
    # client = pymongo.MongoClient()
    client, conn = test_db

    q = MongodbQueue(client, TEST_DATABASE_NAME)
    q.sort_by = [('created_at', 1)]

    # save in cycle
    for key in range(6):
        payload = {
            'key': str(key),
            'required_value': 'yes' if key % 2 == 0 else 'nope',
            'default_value': 'yes!'
        }
        task = q.put(payload, priority=key)

    assert task is not None
    assert q.size() == 6

    # get 3 documents not yet processed
    tasks_queue_get = q.get(3)
    assert len(tasks_queue_get) == 3

    created_at_list = [x['created_at'] for x in tasks_queue_get]
    created_at_list_sorted = sorted(created_at_list)

    for v, s in zip(created_at_list, created_at_list_sorted):
        assert v == s

    created_at_list_sorted_rev = sorted(created_at_list, reverse=True)

    for s in created_at_list_sorted_rev:
        assert s in created_at_list

    # tasks_queue_get = q.get(2)
    # # check selectors working
    # pass


def test_mongodb_queue_get_mark_done(test_db):
    # client = pymongo.MongoClient()
    client, conn = test_db

    q = MongodbQueue(client, TEST_DATABASE_NAME)
    q.sort_by = [('finished_at', 1)]

    assert q.size() == 0

    # save in cycle
    for key in range(6):
        payload = {
            'key': str(key),
            'required_value': 'yes' if key % 2 == 0 else 'nope',
            'default_value': 'yes!'
        }
        task = q.put(payload, priority=key)

    assert task is not None
    assert q.size() == 6

    # get 3 documents not yet processed
    tasks_queue_get = q.get(3)
    assert len(tasks_queue_get) == 3

    for t in tasks_queue_get:
        assert t['finished_at'] is None

    for t in tasks_queue_get:
        result = q.mark_done({'_id': t['_id']})
        assert isinstance(result, pymongo.results.UpdateResult)

    # get 3 last
    tasks_left = q.get(3)
    assert len(tasks_left) == 3

    for t in tasks_left:
        assert t['finished_at'] is None

    for t in tasks_left:
        result = q.mark_done({'_id': t['_id']})

    # check there are none items left unprocessed
    assert q.col.count({'finished_at': None}) == 0


def test_mongo_queue_put_bulk(test_db):
    client, conn = test_db

    q = MongodbQueue(client, TEST_DATABASE_NAME)

    documents = []
    doc_template = {
        'key': '',
        'required_value': 'yes',
    }
    for num in range(1, 5):
        payload = doc_template.copy()
        payload['key'] = 'doc {}'.format(num)

        documents.append(payload)

    r = q.put_bulk(documents, 'key', priority=10)
    br = r.bulk_api_result

    assert br['nUpserted'] == 4
    assert q.size() == 4


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'mongodb_queue.cli.main' in result.output
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output
