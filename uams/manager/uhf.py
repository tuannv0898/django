import json
import logging
import threading
import time
import queue
from enum import Enum
from threading import Thread
import random

from .models import UhfRfModuleModel
from rest_framework import serializers


class CommandType(Enum):
    KEEP_ALIVE = 1
    READ_RF_TAG = 2


class RespondType(Enum):
    HAVE_TAG = 1


class UhfCommand:
    def __init__(self, cmd: CommandType, uhf):
        self.cmd = cmd
        self.uhf = uhf

    def process(self):
        if self.cmd == CommandType.KEEP_ALIVE:
            # logging.error("KEEP_ALIVE %s", self.uhf.address)
            if random.random() > 0.9:
                self.uhf.put_cmd_queue(UhfCommand(CommandType.READ_RF_TAG, self.uhf))
        elif self.cmd == CommandType.READ_RF_TAG:
            logging.error("READ_RF_TAG %s", self.uhf.address)
            uhf_res = UhfRespond(RespondType.HAVE_TAG, self.uhf)
            uhf_res.password = int(random.random() * 1000)
            self.uhf.put_res_queue(uhf_res)
        else:
            pass


class UhfRespond:
    __password = None

    def __init__(self, res: RespondType, uhf):
        self.res = res
        self.uhf = uhf

    def __str__(self):
        return "Address: " + self.uhf.address + "\tRespond type: " + str(self.res.name)

    @property
    def password(self):
        return self.__password

    @password.setter
    def password(self, password):
        self.__password = password


class UhfRfModuleSerializer(serializers.Serializer):
    address = serializers.CharField(max_length=16)
    state = serializers.BooleanField()

    def create(self, validated_data):
        UhfRfModule.objects.create(**validated_data)

    def update(self, instance, validated_data):
        pass


class UhfRfModule(Thread):

    @staticmethod
    def load():
        module_dict = {}
        modules = UhfRfModuleModel.objects.all()
        for module in modules:
            module_dict[module.address] = UhfRfModule(module)
        return module_dict

    def __init__(self, uhf_rf_module_model: UhfRfModuleModel = None, address: str = "0", state: bool = False):
        Thread.__init__(self)
        if uhf_rf_module_model is not None:
            self.__uhf_rf_module_model = uhf_rf_module_model
            self.__address = self.__uhf_rf_module_model.address
            self.__state = self.__uhf_rf_module_model.state
        else:
            self.__address = address
            self.__state = state

            self.__uhf_rf_module_model = UhfRfModuleModel()
            self.__uhf_rf_module_model.address = address
            self.__uhf_rf_module_model.state = state
            self.__uhf_rf_module_model.save()

        self.__cmd_queue = queue.Queue()
        self.__res_queue = queue.Queue()

        self.__run_event = threading.Event()
        self.__run_event.clear()

        self.__done_event = threading.Event()
        self.__done_event.clear()

        self.__timeout = 10 ** 8  # 100ms

    @property
    def address(self):
        return self.__address

    @address.setter
    def x(self, address):
        self.__address = address

    def run(self):
        used_time = 0
        while True:
            self.__run_event.wait()

            start_time = time.time_ns()
            try:
                timeout = (self.__timeout - used_time) / 10 ** 9
                uhf_command = self.__cmd_queue.get(timeout=timeout)
                uhf_command.process()
                self.__cmd_queue.task_done()
            except Exception as e:
                pass
            end_time = time.time_ns()

            # Release mutex for the next run if not timeout
            used_time += end_time - start_time
            if used_time < self.__timeout:
                self.__run_event.set()
            else:
                # Reset used time
                used_time = 0
                # Wait in the next loop
                self.__run_event.clear()
                # Notify done to the main process
                self.__done_event.set()

    def process(self):
        # Send keep alive message to UHF module if there is nothing to do
        if self.__cmd_queue.empty():
            self.put_cmd_queue(UhfCommand(CommandType.KEEP_ALIVE, self))

        # Clear flag to wait until done
        self.__done_event.clear()
        # Start dequeue
        self.__run_event.set()
        # Wait until at least one queue is processed
        self.__done_event.wait()

    def put_cmd_queue(self, cmd: UhfCommand):
        self.__cmd_queue.put(cmd)

    def put_res_queue(self, cmd: UhfCommand):
        self.__res_queue.put(cmd)

    def get_res_queue(self):
        return self.__res_queue
