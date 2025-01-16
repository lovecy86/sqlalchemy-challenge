# PART 2 --- DESIGNING CLIMATE APP

# Import the dependencies.
from flask import Flask, jsonify
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
import datetime as dt
#################################################
# Database Setup
#################################################

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base =  automap_base()

# reflect the tables
Base.prepare(autoload_with = engine)

# Save references to each table
Measurement =  Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB

session =  Session(engine)


#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

# 1. Route for Homepage, listing all the available routes.

@app.route("/")
def homepage():

    return(

    f"Welcome to the HomePage. Which API would you like to choose?.<br/>"
    f"/api/v1.0/precipitation<br/>"
    f"/api/v1.0/stations<br/>"
    f"/api/v1.0/tobs<br/>"
    f"/api/v1.0/<start><br>"
    f"/api/v1.0/<start>/<end><br>"

    )

# Retreving most recent date and one year back date
most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
most_recent_date = dt.datetime.strptime(most_recent_date, "%Y-%m-%d").date()
query_date = most_recent_date - dt.timedelta(days = 365)


# /api/v1.0/precipitation Route 

# Convert the query results from your precipitation analysis (i.e. retrieve only the last 12 months of data) to a dictionary 
# using date as the key and prcp as the value.Return the JSON representation of your dictionary.

@app.route("/api/v1.0/precipitation")
def precipitation_analysis():

    precipitation_data = session.query(Measurement.date, Measurement.prcp).\
    filter(Measurement.date >= query_date).\
    filter(Measurement.date <= most_recent_date).all()
    precip_analysis = []
    for date, prcp in precipitation_data:
        precip_dict = {date : prcp}
        precip_analysis.append(precip_dict)

    return jsonify(precip_analysis)


# 3. /api/v1.0/stations Route

#Return a JSON list of stations from the dataset.

@app.route("/api/v1.0/stations")
def station_list():

    stations = session.query(Station.station).all()
    station_list = [station[0] for station in stations]

    return jsonify(station_list)


# 4. /api/v1.0/tobs Route

# Query the dates and temperature observations of the most-active station for the previous year of data.
# Return a JSON list of temperature observations for the previous year.

@app.route("/api/v1.0/tobs")
def temperature():

    most_active_station = session.query(Measurement.station, func.count(Measurement.station)).\
        group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).first()[0]
    temp_list = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.date >= query_date).\
        filter(Measurement.date <= most_recent_date).\
        filter(Measurement.station == most_active_station).all()
    temperatures =  [temp[1] for temp in temp_list ]

    return jsonify(temperatures)


# 5. /api/v1.0/<start> and /api/v1.0/<start>/<end>

#Return a JSON list of the minimum temperature, the average temperature, and the maximum temperature for a specified start or start-end range.
#For a specified start, calculate TMIN, TAVG, and TMAX for all the dates greater than or equal to the start date.
#For a specified start date and end date, calculate TMIN, TAVG, and TMAX for the dates from the start date to the end date, inclusive.

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")

def temperature_status(start, end=None):
    # Determine the format of start and end dates
    try:
        start_date = dt.datetime.strptime(start, "%Y-%m-%d").date()
        if end:
            end_date = dt.datetime.strptime(end, "%Y-%m-%d").date()
        else:
            end_date = None
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    # Query for temperature statistics
    if end_date:
        # For start and end date range
        results = session.query( func.min(Measurement.tobs),func.avg(Measurement.tobs),func.max(Measurement.tobs) ).\
            filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()
    else:
        # For dates >= start date
        results = session.query(func.min(Measurement.tobs),func.avg(Measurement.tobs),func.max(Measurement.tobs)).\
            filter( Measurement.date >= start_date).all()

        session.close()

    # Extract the results
    temp_stats = {
        "start_date": start,
        "end_date": end if end else "latest",
        "TMIN": results[0][0],  #0th row and 0th column of results gives minimum temp
        #0th row and 1st column of results average  temp
        "TAVG": round(results[0][1], 2) if results[0][1] else None,  # Round average to 2 decimals
        "TMAX": results[0][2] #0th row and 2nd column of results gives maximum temp
    }

    return jsonify(temp_stats)


if __name__ =="__main__":
    app.run(debug = True)