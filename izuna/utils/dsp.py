from izunadsp.core.manager import Manager
from izunadsp.parts.apply_eq import ApplyEQ


class DSPHandler:
    def __init__(self):
        self.settings = {
            "volume": 1.0,
            "eq": [],
        }
        self.dsp = Manager()
        self.dsp.register_part(ApplyEQ())

    def change_setting(self, key, value):
        self.settings[key] = value
