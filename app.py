from collections import deque
import logging
import RPi.GPIO as GPIO
from flask import make_response, Flask, request
from flask_apscheduler import APScheduler
from flask_cors import cross_origin
from gpiozero import CPUTemperature

app = Flask(__name__)

high_threshold = 60
low_threshold = 40

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

scheduler = APScheduler()
@scheduler.task('interval', id='control_fan', seconds=5)
def control_fan():
    app.logger.info("Pre global definition")
    global high_threshold, low_threshold, cpu, temp_queue

    app.logger.info("Scheduler job running")
    temp_queue.append(cpu.temperature)
    app.logger.info(cpu.temperature)

    if float(cpu.temperature) > high_threshold:
        GPIO.output(fanPin, GPIO.HIGH)
    elif float(cpu.temperature) < low_threshold:
        GPIO.output(fanPin, GPIO.LOW)


if __name__ == '__main__':
    try:
        scheduler.init_app(app)
        scheduler.start()
        app.run(host="0.0.0.0", port=10040)
    except KeyboardInterrupt:  # If CTRL+C is pressed, exit cleanly:
        GPIO.cleanup()  # cleanup all GPIO
