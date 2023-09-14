import json
import os

from dateutil.parser import parse

import logging
from datetime import datetime, timedelta
from typing import Dict, List

from kafka import KafkaProducer

from app import db
from app.udaconnect.models import Location
from app.udaconnect.schemas import LocationSchema
from geoalchemy2.functions import ST_AsText, ST_Point
from sqlalchemy.sql import text
from shapely import wkb, wkt

import location_pb2
import location_pb2_grpc

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("udaconnect-location-api")

class LocationService:
    @staticmethod
    def retrieve(location_id) -> Location:
        location, coord_text = (
            db.session.query(Location, Location.coordinate.ST_AsText())
            .filter(Location.id == location_id)
            .one()
        )

        # Rely on database to return text form of point to reduce overhead of conversion in app code
        location.wkt_shape = coord_text
        return location

    @staticmethod
    def create(location: Dict) -> Location:
        validation_results: Dict = LocationSchema().validate(location)
        if validation_results:
            logger.warning(f"Unexpected data format in payload: {validation_results}")
            raise Exception(f"Invalid payload: {validation_results}")

        logging.debug("location: %r", location)
        g = wkt.loads(f"POINT({location['longitude']} {location['latitude']})")
        # Turn location data into a binary sequence for Kafka
        kafka_data = location_pb2.LocationMessage(
               person_id=int(location["person_id"]),
               creation_time=parse(location["creation_time"], fuzzy=True).isoformat(),
               latitude=float(location["latitude"]),
               longitude=float(location["longitude"]),
               coordinate=wkb.dumps(g, hex=True, srid=4326)
           ).SerializeToString()
        
        logging.debug("data: %r", kafka_data)
        producer = KafkaProducer(bootstrap_servers=os.environ["FLASK_KAFKA_SERVER"])
        topic    = os.environ["FLASK_KAFKA_TOPIC"]
        producer.send(topic, kafka_data)

        # new_location = Location()
        # new_location.person_id = location["person_id"]
        # new_location.creation_time = location["creation_time"]
        # new_location.coordinate = ST_Point(location["latitude"], location["longitude"])
        
        # db.session.add(new_location)
        # db.session.commit()

        return '{"result": "ok"}'
