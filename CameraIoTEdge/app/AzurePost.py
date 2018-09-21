from flask import Flask
from takepicture import camera
import os
from azure.storage.blob import BlockBlobService, PublicAccess
import json

from iothub_client import IoTHubClient, IoTHubTransportProvider, IoTHubClientError
from iothub_client import IoTHubMessage, IoTHubMessageDispositionResult
from iothub_client import IoTHubClientRetryPolicy, IoTHubClientResult, IoTHubError

app = Flask(__name__)

TIMEOUT = 241000
MINIMUM_POLLING_TIME = 9
# messageTimeout - the maximum time in milliseconds until a message times out.
# The timeout period starts at IoTHubClient.send_event_async.
# By default, messages do not expire.
MESSAGE_TIMEOUT = 10000
# chose HTTP, AMQP, AMQP_WS or MQTT as transport protocol
PROTOCOL = IoTHubTransportProvider.MQTT
# used to pass as user context on Twin reporting
TWIN_CONTEXT = 0

# String containing Hostname, Device Id & Device Key in the format:
# "HostName=<host_name>;DeviceId=<device_id>;SharedAccessKey=<device_key>"
try:
    CONNECTION_STRING = os.environ["CONNECTION_STRING"]
except KeyError: 
    pass

try:
    account_name= os.environ["BLOB_ACCOUNT_NAME"]
except KeyError:
    pass

try:
    account_key= os.environ["BLOB_ACCOUNT_KEY"]
except KeyError:
    pass


def postblob():
    blob_service = BlockBlobService(account_name, account_key)
    container_name = 'webcam'
    # in case you need to create the container
    # blob_service.create_container(container_name)
    # blob_service.set_container_acl(container_name, public_access=PublicAccess.Container)
    cam.TakePicture()
    blob_service.create_blob_from_path(
        container_name,        
        'picture',
        os.getcwd() + "/static/image.jpg"
    )

def receive_message_callback(message, counter):
    message_buffer = message.get_bytearray()
    size = len(message_buffer)
    msg = message_buffer[:size].decode('utf-8')
    if(msg == "picture"):
        postblob()
    return IoTHubMessageDispositionResult.ACCEPTED

def device_twin_callback(update_state, payload, user_context):
    try:
        js = json.loads(payload)
        timezone = js["desired"]["timezone"]
        cam.timezone = int(timezone)
        reported_state = "{\"timezone\":" + str(cam.timezone) + "}"
        client.send_reported_state(reported_state, len(reported_state), send_reported_state_callback, TWIN_CONTEXT)
    except:
        pass

def send_reported_state_callback(status_code, user_context):
    pass

def iothub_client_init():
    # prepare iothub client
    client = IoTHubClient(CONNECTION_STRING, PROTOCOL)
    if client.protocol == IoTHubTransportProvider.HTTP:
        client.set_option("timeout", TIMEOUT)
        client.set_option("MinimumPollingTime", MINIMUM_POLLING_TIME)
    # set the time until a message times out
    client.set_option("messageTimeout", MESSAGE_TIMEOUT)
    # to enable MQTT logging set to 1
    if client.protocol == IoTHubTransportProvider.MQTT:
        client.set_device_twin_callback(
            device_twin_callback, TWIN_CONTEXT)
        client.set_option("logtrace", 0)
    client.set_message_callback(
        receive_message_callback, 0)

    retryPolicy = IoTHubClientRetryPolicy.RETRY_INTERVAL
    retryInterval = 100
    client.set_retry_policy(retryPolicy, retryInterval)
    return client

@app.route('/')
def hello():
    return "Hello from python flask webapp!, try /image.jpg /postimage /timezone"

@app.route('/image.jpg')
def image():
    cam.TakePicture()
    return app.send_static_file('image.jpg')

@app.route('/timezone')
def timezone():
    return "The timezone is: " + str(cam.timezone) + "h"

@app.route('/postimage')
def postimage():
    postblob()
    return 'image posted https://portalvhdskb2vtjmyg3mg.blob.core.windows.net/webcam/picture'

if __name__ == '__main__':
    # initialize the camera
    cam = camera()
    # initialize IoTHub
    client = iothub_client_init()
    # run flask, host = 0.0.0.0 needed to get access to it outside of the host
    app.run(host='0.0.0.0',port=1337)