from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api, Resource, fields
from flask_migrate import Migrate  # Import Flask-Migrate
from uuid import uuid4
from datetime import datetime

# Initialize the Flask app, database, and API
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cleansmrs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Initialize Flask-Migrate
api = Api(app, doc="/docs", title="CleanSMRS API", description="API for managing observations in CleanSMRS")

# Define the Observation model (database table)
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

# API models for Swagger documentation
observation_model = api.model("Observation", {
    "id": fields.String(readonly=True, description="Unique identifier for the observation"),
    "date": fields.String(required=True, description="Date of observation (YYYY-MM-DD)"),
    "time": fields.String(required=True, description="Time of observation (HH:MM:SS)"),
    "time_zone_offset": fields.String(required=True, description="Timezone offset"),
    "coordinates": fields.String(required=True, description="Coordinates in latitude and longitude"),
    "temperature_water": fields.Float(description="Water temperature in Celsius"),
    "temperature_air": fields.Float(description="Air temperature in Celsius"),
    "humidity": fields.Float(description="Humidity percentage"),
    "wind_speed": fields.Float(description="Wind speed in km/h"),
    "wind_direction": fields.Float(description="Wind direction in degrees"),
    "precipitation": fields.Float(description="Precipitation in mm"),
    "haze": fields.Float(description="Haze level (arbitrary units)"),
    "becquerel": fields.Float(description="Becquerel level"),
    "notes": fields.String(description="Additional notes"),
    "created": fields.String(readonly=True, description="Timestamp of creation"),
    "updated": fields.String(readonly=True, description="Timestamp of last update"),
    "deleted": fields.String(description="Timestamp of deletion (if deleted)")
})

# Namespace for Observations
ns_observations = api.namespace("observations", description="Operations related to observations")

# Routes and Swagger documentation
@ns_observations.route("/")
class ObservationsList(Resource):
    @ns_observations.marshal_list_with(observation_model)
    def get(self):
        """Get all observations"""
        observations = Observation.query.all()
        return observations, 200

    @ns_observations.expect(observation_model)
    def post(self):
        """Create a new observation"""
        data = request.get_json()
        try:
            date = datetime.strptime(data["date"], "%Y-%m-%d").date()
            time = datetime.strptime(data["time"], "%H:%M:%S").time()
            observation = Observation(
                date=date,
                time=time,
                time_zone_offset=data["time_zone_offset"],
                coordinates=data["coordinates"],
                temperature_water=data.get("temperature_water"),
                temperature_air=data.get("temperature_air"),
                humidity=data.get("humidity"),
                wind_speed=data.get("wind_speed"),
                wind_direction=data.get("wind_direction"),
                precipitation=data.get("precipitation"),
                haze=data.get("haze"),
                becquerel=data.get("becquerel"),
                notes=data.get("notes"),
            )
            db.session.add(observation)
            db.session.commit()
            return {"message": "Observation created successfully", "id": observation.id}, 201
        except Exception as e:
            return {"error": str(e)}, 400

@ns_observations.route("/<string:id>")
class ObservationItem(Resource):
    @ns_observations.marshal_with(observation_model)
    def get(self, id):
        """Get an observation by ID"""
        observation = Observation.query.get(id)
        if not observation:
            api.abort(404, f"Observation {id} not found")
        return observation


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1")
