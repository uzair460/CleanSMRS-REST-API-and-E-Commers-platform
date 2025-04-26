from datetime import datetime
from uuid import uuid4
from app import db  # Import db from the app module

class Observation(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    time_zone_offset = db.Column(db.String(10), nullable=False)
    coordinates = db.Column(db.String(50), nullable=False)
    temperature_water = db.Column(db.Float, nullable=True)
    temperature_air = db.Column(db.Float, nullable=True)
    humidity = db.Column(db.Float, nullable=True)
    wind_speed = db.Column(db.Float, nullable=True)
    wind_direction = db.Column(db.Float, nullable=True)
    precipitation = db.Column(db.Float, nullable=True)
    haze = db.Column(db.Float, nullable=True)
    becquerel = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Observation {self.id}>"