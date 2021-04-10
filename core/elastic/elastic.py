import re
from datetime import datetime
from elasticsearch import Elasticsearch, NotFoundError

# https://elasticsearch-py.readthedocs.io/en/v7.11.0/
# default connect to localhost:9200
from botmarket.settings import ELASTIC_HOST

es = Elasticsearch(hosts=ELASTIC_HOST)
index = "bot-iphone-test"


def get_body(tags, description_ru, description_en):
    language = []
    if description_ru is not None and description_ru != "":
        language.append("ru")
    if description_en is not None and description_en != "":
        language.append("en")
    if not language:
        lan = "en"
        for t in tags:
            if re.match("^[а-я-А-ЯёЁ]", t):
                lan = "ru"
                break
        language.append(lan)

    return {
        "tags": tags,
        "text": "{ru} {en}".format(ru=description_ru,
                                   en=description_en),
        "timestamp": datetime.now(),
        "language": language

    }


def delete_from_elastic(id):
    try:
        es.delete(index=index, id=id)
    except NotFoundError:
        pass


def add_to_elastic_bot_model(bot):
    add_to_elastic(bot.id, bot.tags,
                   bot.description_ru,
                   bot.description_en)


def add_to_elastic_bot_data(bot):
    add_to_elastic(bot['id'], bot['tags'],
                   bot['description_ru'],
                   bot['description_en'])


def add_to_elastic(id, tags, description_ru, description_en):
    try:
        res = es.index(index=index, id=id, body=get_body(tags, description_ru, description_en))
    except Exception as e:
        print(e)


def search_elastic(keys, from_, size, language=["en", "ru"]):
    ids = []
    count = 0
    try:
        res = es.search(index=index, body=create_search(keys, language), from_=from_, size=size)
        for r in res['hits']['hits']:
            ids.append(int(r['_id']))
        count = res['hits']['total']['value']
    except Exception:
        pass
    return ids, count


def create_search(keys, language):
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
            "should": should,
            "must": [{'match': {'language': {'query': str(language)}}}
                     ]
        }
    }
    }


#
# #
# # # es.index(index="lan", id=1, body={
# # #         'tags': ["vk"],
# # #         'text': ["vk"],
# # #         'timestamp': datetime.now(),
# # #     'language':["ru", "en"]
# # #     })
# #
# # {
# #     'query': {
# #         'bool': {'should':
# #                      [{'match': {'tags': {'query': 'v', 'fuzziness': 'AUTO'}}}, {'match': {'text': {'query': 'v', 'fuzziness': 'AUTO'}}}, {'match': {'tags': {'query': 'k', 'fuzziness': 'AUTO'}}}, {'match': {'text': {'query': 'k', 'fuzziness': 'AUTO'}}}]
# #                  },
# #         "must": [
# #             {
# #                 "terms": {
# #                     "language": [
# #                         "tag-1",
# #                         "tag-2",
# #                         "tag-3"
# #                     ],
# #                     "execution": "and"
# #                 }
# #             }
# #         ],
# #     }
# # }
#
# a = es.search(index="ln", body={'query': {'bool': {'should': [{'match': {'tags': {'query': 'vk', 'fuzziness': 'AUTO'}}},
#                                                               {'match': {'text': {'query': 'vk', 'fuzziness': 'AUTO'}}},
#                                                               {'match': {'text': {'query': 'vk', 'fuzziness': 'AUTO'}}}
#                                                               ],
#                                                    'must': [{
#                                                        'match': {'language': {'query': 'en', 'fuzziness': 'AUTO'}}}
#                                                    ]}}}, from_=0, size=10)
#
# es.search(index=index, body={'query': {'bool': {'should': [{'match': {'tags': {'query': 'бот', 'fuzziness': 'AUTO'}}},
#                                                            {'match': {'text': {'query': 'бот', 'fuzziness': 'AUTO'}}}
#                                                            ],
#                                                 'must': [{
#                                                     'match': {'language': {'query': 'en', 'fuzziness': 'AUTO'}}}
#                                                 ], }}}, from_=0, size=10)
