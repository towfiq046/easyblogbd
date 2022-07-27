from elastic_transport import ConnectionError
from flask import current_app


def add_to_index(index, model):
    if not current_app.elasticsearch:
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    try:
        current_app.elasticsearch.index(index=index, id=model.id, body=payload)
    except ConnectionError:
        return


def remove_from_index(index, model):
    if not current_app.elasticsearch:
        return
    try:
        current_app.elasticsearch.delete(index=index, id=model.id)
    except ConnectionError:
        return


def query_index(index, text_to_search, page, per_page):
    if not current_app.elasticsearch:
        return [], 0
    search = current_app.elasticsearch.search(
        index=index,
        body={
            'query': {
                'multi_match': {
                    'query': text_to_search,
                    'fields': ['*']
                }
            },
            'from': (page - 1) * per_page, 'size': per_page
        })
    list_of_ids = [int(hit['_id']) for hit in search['hits']['hits']]
    total_number_of_posts = search['hits']['total']['value']
    return list_of_ids, total_number_of_posts
