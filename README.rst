=============
mongodb_queue
=============


.. image:: https://img.shields.io/pypi/v/mongodb_queue.svg
        :target: https://pypi.python.org/pypi/mongodb_queue

.. image:: https://img.shields.io/travis/istinspring/mongodb_queue.svg
        :target: https://travis-ci.org/istinspring/mongodb_queue

.. image:: https://readthedocs.org/projects/mongodb-queue/badge/?version=latest
        :target: https://mongodb-queue.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


.. image:: https://pyup.io/repos/github/istinspring/mongodb_queue/shield.svg
     :target: https://pyup.io/repos/github/istinspring/mongodb_queue/
     :alt: Updates



Simple Queue based on MongoDb


* Free software: MIT license
* Documentation: https://mongodb-queue.readthedocs.io.


Tutorial
--------

.. code-block:: python
   from mongodb_queue.mongodb_queue import PayloadValidationError

   class MongodbQueue(BaseMongodbQueue):
       _queue_name = QUEUE_COLLECTION
       _payload_schema = {
           'key': {'type': 'string', 'required': True},
           'required_value': {'type': 'string', 'required': True},
           'default_value': {'type': 'string', 'default': 'nope'},
       }


   client = pymongo.MongoClient()

   q = MongodbQueue(client, TEST_DATABASE_NAME)
   q.sort_by = [('created_at', 1)]

   # add element to the queue
   q.put({'key': '12', 'required_value': 'here'})

   for key in range(6):
       payload = {
           'key': str(key),
           'required_value': 'yes' if key % 2 == 0 else 'nope',
           'default_value': 'yes!'
       }
       task = q.put(payload, priority=key)

   assert q.size() == 7

   # get 3 documents not yet processed
   tasks = q.get(3)


Features
--------

* TODO

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
