from flask import Flask
from threading import Event
import signal
import os

from flask_kafka import FlaskKafka
import psycopg2

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USERNAME"),
    password=os.getenv("DB_PASSWORD")
)

app = Flask(__name__)

INTERRUPT_EVENT = Event()

bus = FlaskKafka(INTERRUPT_EVENT,
                 bootstrap_servers=os.getenv('FLASK_KAFKA_SERVER'),
                 group_id="consumer-grp-id"
                 )

from location_pb2 import LocationMessage

def listen_kill_server():
    signal.signal(signal.SIGTERM, bus.interrupted_process)
    signal.signal(signal.SIGINT, bus.interrupted_process)
    signal.signal(signal.SIGQUIT, bus.interrupted_process)
    signal.signal(signal.SIGHUP, bus.interrupted_process)


@bus.handle(os.getenv("FLASK_KAFKA_TOPIC"))
def test_topic_handler(msg):
    message = LocationMessage()
    message.ParseFromString(msg.value)

    sql = """INSERT INTO public.location (person_id, coordinate, creation_time)
                VALUES(%s, %s, %s) RETURNING id;"""
        
    location_id = None
    try:
        # create a new cursor
        cur = conn.cursor()
        # execute the INSERT statement
        cur.execute(sql, (message.person_id, message.coordinate, message.creation_time, ))
        # get the generated id back
        location_id = cur.fetchone()[0]
        # commit the changes to the database
        conn.commit()
        # close communication with the database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()    

    print("consumed {} from locations".format(message))
    print("created location {} ".format(location_id))


if __name__ == '__main__':
    bus.run()
    listen_kill_server()
    app.run(debug=True, port=5004)