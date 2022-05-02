import json
import logging
import threading
import time
import queue
from threading import Thread, Lock

from .models import UhfRfModuleModel
from rest_framework import serializers


class UhfCommand:
    def __init__(self, uhf):
        self.uhf = uhf

    def process(self):
        logging.error("Hello %s", self.uhf.address)


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
            self.uhf_rf_module_model = uhf_rf_module_model
            self.address = self.uhf_rf_module_model.address
            self.state = self.uhf_rf_module_model.state
        else:
            self.address = address
            self.state = state

            self.uhf_rf_module_model = UhfRfModuleModel()
            self.uhf_rf_module_model.address = address
            self.uhf_rf_module_model.state = state
            self.uhf_rf_module_model.save()

        self.queue = queue.Queue()

        self.run_event = threading.Event()
        self.run_event.clear()

        self.done_event = threading.Event()
        self.done_event.clear()

        self.timeout = 10 ** 8  # 100ms

        self.queue.maxsize = 10

    def run(self):
        used_time = 0
        while True:
            self.run_event.wait()

            start_time = time.time_ns()
            try:
                timeout = (self.timeout - used_time) / 10 ** 9
                uhf_command = self.queue.get(timeout=timeout)
                uhf_command.process()
                self.queue.task_done()
            except:
                pass
            end_time = time.time_ns()

            # Release mutex for the next run if not timeout
            used_time += end_time - start_time
            if used_time < self.timeout:
                self.run_event.set()
            else:
                # Reset used time
                used_time = 0
                # Wait in the next loop
                self.run_event.clear()
                # Notify done to the main process
                self.done_event.set()

    def process(self):
        # Clear flag to wait until done
        self.done_event.clear()
        # Start dequeue
        self.run_event.set()
        # Wait until at least one queue is processed
        self.done_event.wait()

    def put_queue(self, cmd: UhfCommand):
        self.queue.put(cmd)
