
from datetime import datetime
from elasticsearch import Elasticsearch

# https://elasticsearch-py.readthedocs.io/en/v7.11.0/
# default connect to localhost:9200

es = Elasticsearch()
index = "bot-test"


def get_body(tags, text):
    return {
        'tags': tags,
        'text': text,
        'timestamp': datetime.now(),
    }


def delete_from_elastic(id):
    es.delete(index=index, id=id)


def add_to_elastic_bot_data(bot):
    add_to_elastic(bot['id'], bot['tags'],
                   "{ru} {en}".format(ru=bot['description_ru'],
                                      en=bot['description_en']))


def add_to_elastic(id, tags, text):
    try:
        res = es.index(index=index, id=id, body=get_body(tags, text))
    except Exception as e:
        print(e)


def search_elastic(keys, from_, size):
    ids = []
    try:
        res = es.search(index=index, body=create_search(keys), from_=from_, size=size)
        for r in res['hits']['hits']:
            ids.append(int(r['_id']))
    except Exception:
        pass
    return ids


def create_search(keys):
    should = []
    for key in keys:
        should.append({
            "match": {
                "tags": {
                    "query": key,
                    "fuzziness": "AUTO"
                }
            }
        })
        should.append({
            "match": {
                "text": {
                    "query": key,
                    "fuzziness": "AUTO"
                }
            }
        })
    return {"query": {
        "bool": {
            "should": should
        }
    }
    }
