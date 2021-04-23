from collections import deque
import logging
from datetime import datetime, time
import RPi.GPIO as GPIO
import pytz
from flask import make_response, Flask, request
from flask_apscheduler import APScheduler
from flask_cors import cross_origin
from gpiozero import CPUTemperature

app = Flask(__name__)

high_threshold = 60
low_threshold = 40
boost_pass = 0
silent_mode = False

# Pin Definitons:
fanPin = 17

# Pin Setup:
GPIO.setmode(GPIO.BCM)  # Broadcom pin-numbering scheme
GPIO.setup(fanPin, GPIO.OUT)  # LED pin set as output

# Initial state for LEDs:
GPIO.output(fanPin, GPIO.HIGH)
cpu = CPUTemperature()

temp_queue = deque(maxlen=1440)

app.logger.setLevel(logging.INFO)
formatter = logging.Formatter(f'%(asctime)s - %(levelname)s - %(message)s')
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(formatter)
app.logger.addHandler(consoleHandler)
app.logger.info("App started.")

scheduler = APScheduler()

timezone = pytz.timezone("EET")


@app.route('/', methods=['POST'])
@cross_origin()
def set_thresholds():
    global high_threshold, low_threshold
    data = request.get_json()
    something_set = False

    if "high_threshold" in data.keys() and data["high_threshold"]:
        something_set = True
        high_threshold = data["high_threshold"]

    if "low_threshold" in data.keys() and data["low_threshold"]:
        something_set = True
        low_threshold = data["low_threshold"]

    if something_set:
        return make_response({"message": "Temperature set"}, 200)
    else:
        return make_response({"message": "Nothing set"}, 418)


@app.route('/', methods=['GET'])
@cross_origin()
def get_thresholds():
    global high_threshold, low_threshold

    thresholds = {"high_threshold": high_threshold, "low_threshold": low_threshold}

    return make_response(thresholds, 200)


@app.route("/temperature", methods=['GET'])
@cross_origin()
def get_temperature():
    global cpu
    return make_response({"temperature": cpu.temperature}, 200)


@app.route("/temperature/queue", methods=['GET'])
@cross_origin()
def get_temperature_queue():
    global temp_queue
    return make_response({"temperature_queue": list(temp_queue)}, 200)


@app.route("/boost", methods=['GET'])
@cross_origin()
def boost():
    global boost_pass
    GPIO.output(fanPin, GPIO.HIGH)
    boost_pass = 5
    return make_response(200)


@app.route("/silentmode", methods=['GET'])
def get_silent_mode():
    return make_response({"silent_mode": silent_mode}, 200)


@scheduler.task('interval', id='control_fan', seconds=60)
def control_fan():
    global high_threshold, low_threshold, cpu, temp_queue, boost_pass

    current_time = str(datetime.now().astimezone(timezone)).split()[1].split('.')[0]
    temp_queue.append([cpu.temperature, current_time])
    app.logger.info("Temperature: " + str([cpu.temperature, current_time]))

    check_if_silent_mode()
    drive_fan(cpu, high_threshold, low_threshold)


def drive_fan(cpu, high_threshold, low_threshold):
    global boost_pass
    if float(cpu.temperature) > high_threshold:
        if boost_pass > 0:
            boost_pass -= 1
            return
        GPIO.output(fanPin, GPIO.HIGH + (10 if silent_mode else 0))
    elif float(cpu.temperature) < low_threshold:
        GPIO.output(fanPin, GPIO.LOW)


def check_if_silent_mode():
    global silent_mode
    silent_mode = time(23, 0) <= time() or time() <= time(8, 0)


if __name__ == '__main__':
    try:
        scheduler.init_app(app)
        scheduler.start()
        app.run(host="0.0.0.0", port=5000)
    except KeyboardInterrupt:  # If CTRL+C is pressed, exit cleanly:
        GPIO.cleanup()  # cleanup all GPIO
