# mongodb\_queue

[![image](https://img.shields.io/pypi/v/mongodb_queue.svg)](https://pypi.python.org/pypi/mongodb_queue)

[![image](https://img.shields.io/travis/istinspring/mongodb_queue.svg)](https://travis-ci.org/istinspring/mongodb_queue)

[![Documentation
Status](https://readthedocs.org/projects/mongodb-queue/badge/?version=latest)](https://mongodb-queue.readthedocs.io/en/latest/?badge=latest)

[![Updates](https://pyup.io/repos/github/istinspring/mongodb_queue/shield.svg)](https://pyup.io/repos/github/istinspring/mongodb_queue/)

Simple Queue based on MongoDb

  - Free software: MIT license
  - Documentation: <https://mongodb-queue.readthedocs.io>.

## Examples

```python
from mongodb_queue.mongodb_queue import PayloadValidationError

class MongodbQueue(BaseMongodbQueue):
    _queue_name = 'some_queue'
    _payload_schema = {
        'key': {'type': 'string', 'required': True},
        'required_value': {'type': 'string', 'required': True},
        'default_value': {'type': 'string', 'default': 'nope'},
    }

client = pymongo.MongoClient()

q = MongodbQueue(client, 'mongodb_queue')
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
```

## Features

  - [ ] bulk writes?
  - [ ] FIFO (by '_id'_)

## Credits

This package was created with
[Cookiecutter](https://github.com/audreyr/cookiecutter) and the
[audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage)
project template.
