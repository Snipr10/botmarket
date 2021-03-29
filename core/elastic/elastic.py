
from datetime import datetime
from elasticsearch import Elasticsearch, NotFoundError

# https://elasticsearch-py.readthedocs.io/en/v7.11.0/
# default connect to localhost:9200
from botmarket.settings import ELASTIC_HOST

es = Elasticsearch(hosts=ELASTIC_HOST)
index = "bot-iphone-test"


def get_body(tags, text):
    return {
        'tags': tags,
        'text': text,
        'timestamp': datetime.now(),
    }


def delete_from_elastic(id):
    try:
        es.delete(index=index, id=id)
    except NotFoundError:
        pass


def add_to_elastic_bot_model(bot):
    tags = bot.tags
    try:
        if bot.last_name_en is not None:
            tags += " " + bot.last_name_en
        if bot.last_name_ru is not None:
            tags += bot.last_name_ru
        if bot.first_name_en is not None:
            tags += bot.first_name_en
        if bot.first_name_ru is not None:
            tags += bot.first_name_ru
    except Exception as e:
        print(e)
        pass
    add_to_elastic(bot.id, tags,
                   "{ru} {en}".format(ru=bot.description_ru,
                                      en=bot.description_en))


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
    count = 0
    try:
        res = es.search(index=index, body=create_search(keys), from_=from_, size=size)
        for r in res['hits']['hits']:
            ids.append(int(r['_id']))
        count = res['hits']['total']['value']
    except Exception:
        pass
    return ids, count


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
