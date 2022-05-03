import time
import serial
import queue
import logging
from threading import Thread
import paho.mqtt.client as mqtt

from .uhf import UhfRfModule, UhfRespond


class ResponseConsumer(Thread):
    def __init__(self, q: queue.Queue, client: mqtt.Client):
        Thread.__init__(self)
        self.__queue = q
        self.__client = client

    def run(self):
        while True:
            uhf_res = self.__queue.get()
            self.consume(uhf_res)
            self.__queue.task_done()

    def consume(self, uhf_res: UhfRespond):
        logging.error("ResponseConsumer %s", uhf_res)
        self.__client.publish("/gw_tx", str(uhf_res))


class ModulesManager(Thread):

    def __init__(self):
        Thread.__init__(self)

        # self.uhfModules keeps the list of UHF module managed by this manager
        # Initialize it by loading saved info from database
        self.uhf_modules = UhfRfModule.load()

        try:
            self.serial_device = serial.Serial('/dev/ttyUSB0', 19200, timeout=1)
        except:
            pass

        self.queue = queue.Queue()

        self.__client = mqtt.Client("ModulesManager")
        self.__client.on_message = self.on_message
        self.__client.on_subscribe = self.on_subscribe
        self.__client.on_connect = self.on_connect

        self.__client.connect("localhost", 1883)
        self.__client.loop_start()

        self.__respond_consumer = ResponseConsumer(self.queue, self.__client)
        self.__respond_consumer.start()

        self.start()

    def run(self):
        while True:
            start_time = time.time_ns()
            for address, module in self.uhf_modules.items():
                if not module.is_alive():
                    module.start()

                # Process each module
                module.process()

                # Get all queues from UHF modules to process in one place
                while not module.get_res_queue().empty():
                    uhf_respond = module.get_res_queue().get(block=False)
                    self.queue.put(uhf_respond)
                    module.get_res_queue().task_done()

            end_time = time.time_ns()
            # logging.error("Loop for %f", (end_time - start_time) / 10**9)

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logging.error("Drone Connection Established")
            self.__client.subscribe("/gw_rx")
        else:
            logging.error("bad connection Returned code=", rc)

    def on_subscribe(self, client, userdata, mid, granted_qos):
        logging.error("Subscription complete")

    def on_message(self, client, userdata, pdu):
        logging.error("%s %s", pdu.topic, pdu.payload.decode())

    def get_all_modules(self):
        return self.uhf_modules


modules_manager = ModulesManager()
