import time
import logging
from threading import Thread

from .uhf import UhfRfModule


class ModulesManager(Thread):

    def __init__(self):
        Thread.__init__(self)

        # self.uhfModules keeps the list of UHF module managed by this manager
        # Initialize it by loading saved info from database
        self.uhfModules = UhfRfModule.load()

    def run(self):
        while True:
            for module in self.uhfModules:
                logging.error("Hello %s", module.address)
                time.sleep(1)

    def get_all_modules(self):
        return self.uhfModules


modules_manager = ModulesManager()
