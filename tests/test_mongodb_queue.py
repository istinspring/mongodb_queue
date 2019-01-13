#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `mongodb_queue` package."""

import pytest

from click.testing import CliRunner

import pymongo
from mongodb_queue import cli


TEST_DATABASE_NAME = 'test_mqueue'


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


def test_mongodb_queue():
    from mongodb_queue.mongodb_queue import BaseMongodbQueue

    class MongodbQueue(BaseMongodbQueue):
       _queue_name = 'queue_queue'
       _payload_schema = {
           'key': {'type': 'string', 'required': True},
           'required_value': {'type': 'string', 'required': True},
           'default_value': {'type': 'string', 'default': 'nope'},
       }

    client = pymongo.MongoClient()

    q = MongodbQueue(client, TEST_DATABASE_NAME)

    payload = {
        'key': 'alpha',
        'required_value': 'yes',
    }
    task = q.put(payload, priority=5)
    assert isinstance(task, pymongo.results.InsertOneResult)


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'mongodb_queue.cli.main' in result.output
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output
