from typing import Dict


def prepare_device_data(key: str, data: Dict[str, str]) -> Dict[str, str]:
    device_id = key.split(':')[1]
    prepared_data = {"id": device_id}
    prepared_data.update(data)
    return prepared_data


def device_updates_channel(device_id: str) -> str:
    return f"device:updates:{device_id}"


def prepare_for_redis(data: dict) -> dict:
    prepared_data = {}
    for k, v in data.items():
        if isinstance(v, bool):

            prepared_data[k] = str(v).lower()
        else:
            prepared_data[k] = str(v)
    return prepared_data