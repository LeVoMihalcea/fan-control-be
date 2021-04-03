from flask import make_response, Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
import RPi.GPIO as GPIO
import time
from gpiozero import CPUTemperature
from collections import deque

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


@app.route('/', methods=['POST'])
def set_thresholds():
    global high_threshold, low_threshold
    data = request.get_json()
    something_set = False

    if "high_threshold" in data.keys() && data["high_threshold"]:
        something_set = True
        high_threshold = data["high_threshold"]

    if "low_threshold" in data.keys() && data["low_threshold"]:
        something_set = True
        low_threshold = data["low_threshold"]

    if something_set:
        return make_response({"message": "Temperature set"}, 200)
    else:
        return make_response({"message": "Nothing set"}, 418)


@app.route('/', methods=['GET'])
def get_thresholds():
    global high_threshold, low_threshold

    thresholds = {"high_threshold": high_threshold, "low_threshold": low_threshold}

    return make_response(thresholds, 200)


@app.route("/temperature", methods=['GET'])
def get_temperature():
    global cpu
    return make_response({"temperature": cpu.temperature}, 200)


@app.route("/temperature/queue", methods=['GET'])
def get_temperature_queue():
    global temp_queue
    return make_response({"temperature_queue": list(temp_queue)}, 200)


def control_fan():
    global high_threshold, low_threshold, cpu, temp_queue

    print(cpu.temperature)
    temp_queue.append(cpu.temperature)

    if float(cpu.temperature) > high_threshold:
        GPIO.output(fanPin, GPIO.HIGH)
    elif float(cpu.temperature) < low_threshold:
        GPIO.output(fanPin, GPIO.LOW)


if __name__ == '__main__':
    try:
        sched = BackgroundScheduler(daemon=True)
        sched.add_job(control_fan, 'interval', minutes=1)
        sched.start()
        app.run(host="0.0.0.0", port=10040)
    except KeyboardInterrupt:  # If CTRL+C is pressed, exit cleanly:
        GPIO.cleanup()  # cleanup all GPIO
