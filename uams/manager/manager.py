import time
import serial
import queue
import logging
from threading import Thread

from .uhf import UhfRfModule, UhfCommand


class ModulesManager(Thread):
    scan = False

    def __init__(self):
        Thread.__init__(self)

        # self.uhfModules keeps the list of UHF module managed by this manager
        # Initialize it by loading saved info from database
        self.uhf_modules = UhfRfModule.load()

        try:
            self.serial_device = serial.Serial('/dev/ttyUSB0', 19200, timeout=1)
        except:
            pass

        self.start()

    def run(self):
        while True:
            start_time = time.time_ns()
            for address, module in self.uhf_modules.items():
                if not module.is_alive():
                    module.start()

                # Process each module
                module.process()

            end_time = time.time_ns()
            logging.error("Loop for %f", (end_time - start_time) / 10**9)

    def scan(self):
        self.scan = True

    def get_all_modules(self):
        for address, module in self.uhf_modules.items():
            module.put_queue(UhfCommand(module))
        return self.uhf_modules


modules_manager = ModulesManager()
