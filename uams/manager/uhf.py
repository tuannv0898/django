import json

from .models import UhfRfModuleModel
from rest_framework import serializers


class UhfRfModuleSerializer(serializers.Serializer):

    address = serializers.CharField(max_length=16)
    state = serializers.BooleanField()

    def create(self, validated_data):
        UhfRfModule.objects.create(**validated_data)

    def update(self, instance, validated_data):
        pass


class UhfRfModule:

    @staticmethod
    def load():
        module_list = []
        modules = UhfRfModuleModel.objects.all()
        for module in modules:
            module_list.append(UhfRfModule(module))
        return module_list

    def __init__(self, uhf_rf_module_model: UhfRfModuleModel = None, address: str = "0", state: bool = False):
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
