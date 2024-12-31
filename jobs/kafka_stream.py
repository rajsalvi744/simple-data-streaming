import datetime
import requests
import json

URL = "http://randomuser.me/api"


def get_data():
    res = requests.get(URL)
    res = res.json()
    res = res['results'][0]
    return res


def format_data(res):
    data = {}

    data['user_id'] = res['login']['uuid']
    data['first_name'] = res['name']['first'],
    data['last_name'] = res['name']['last'],
    data['gender'] = res['gender'],
    data['data_of_birth'] = res['dob']['date'],
    data['address'] = f"{res['location']['street']['number']}-{res['location']['street']['name']}," \
                      f"{res['location']['city']},{res['location']['state']},{res['location']['country']}"
    data['postcode'] = res['location']['postcode'],
    data['nationality'] = res['nat'],
    data['email'] = res['email'],
    data['phone'] = res['phone'],
    data['username'] = res['login']['username'],
    data['photo'] = res['picture']['medium']
    return data


def delivery_report(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')


def stream_data():
    import time
    from confluent_kafka import SerializingProducer
    import logging

    producer = SerializingProducer({'bootstrap.servers': 'localhost:9092'})

    curr_time = time.time()

    while True:
        if time.time() > curr_time + 120:
            break
        try:
            res = get_data()
            res = format_data(res)
            producer.produce('users_created',
                             key=res['user_id'],
                             value=json.dumps(res).encode('utf-8'),
                             on_delivery=delivery_report
                             )
            producer.flush()
        except Exception as e:
            logging.error(f"An Error Occurred :{e} ")
            continue


if __name__ == "__main__":
    stream_data()

