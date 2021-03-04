class Real_device_data(object):
    def __init__(self, data, ts, dtype, device_config_id, device_id):
        self.data = data
        self.ts = ts
        self.type = dtype
        self.device_config_id = device_config_id
        self.device_id = device_id