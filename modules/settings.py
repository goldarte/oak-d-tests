import os
import sys
import yaml
#from ruamel.yaml import YAML
#yaml=YAML()
#yaml.default_flow_style = None
import copy
import logging
from collections.abc import Mapping, MutableMapping

logger = logging.getLogger(__name__)

class Settings(MutableMapping):
    def __init__(self, settings_path, default_flow_style=None):
        self.store = dict()
        self.default_flow_style = default_flow_style
        self.settings_path = settings_path
        self.load()

    def load(self):
        os.makedirs(os.path.realpath(os.path.dirname(self.settings_path)), exist_ok=True)
        try:
            with open(self.settings_path, 'r') as settings_file:
                self.store = yaml.safe_load(settings_file)
        except FileNotFoundError:
            logger.error(f"Can't read {os.path.realpath(self.settings_path)}, trying to create new...")
            with open(self.settings_path, 'w'):
                logger.info(f"Created {os.path.realpath(self.settings_path)}")
        except TypeError:
            pass
        if self.store is None:
            self.store = dict()

    def update_value(self, key_sequence, value):
        if type(key_sequence) is str:
            self.store[key_sequence] = value
        else:
            try:
                element = self.store
                keys_for_iterate = key_sequence[:-1]
                last_key = key_sequence[-1]
                for k in keys_for_iterate:
                    element = element[k]
                element[last_key] = value
            except TypeError:
                logger.error(f"Can't update {key_sequence} in config!")
                return
        self.save()

    def update_defaults(self, default_dict):
        updated_dict = copy.deepcopy(default_dict)
        old_store = copy.deepcopy(self.store)
        self.store = updated_dict
        self.update_recursive(old_store)
        self.save()

    def update_recursive(self, other_dict):
        def update(d, u):
            for k, v in u.items():
                if isinstance(v, Mapping):
                    d[k] = update(d.get(k, {}), v)
                else:
                    d[k] = v
            return d
        update(self.store, other_dict)

    def save(self):
        with open(self.settings_path, 'w+') as settings_file:
            yaml.safe_dump(self.store, settings_file, default_flow_style=self.default_flow_style, sort_keys=False)

    def __getitem__(self, key):
        return self.store[self._keytransform(key)]

    def __setitem__(self, key, value):
        self.store[self._keytransform(key)] = value

    def __delitem__(self, key):
        del self.store[self._keytransform(key)]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __repr__(self):
        return self.store.__repr__()

    def _keytransform(self, key):
        return key

if __name__ == '__main__':
    settings = Settings("test/settings.yaml")
    settings["test"] = "OMG"
    update_dict = {"test2":"abc", "test3":"def"}
    settings.update(update_dict)
    print(settings)
    settings["test_dict"] = {"a":1, "b":2}
    print(settings)
    settings.update_value(("test_dict", "b"), 3)
    print(settings)
    settings.save()
    test_dict = {"test2":4, "m":5}
    #test_dict.update(settings)
    #print(test_dict)
    settings.update_defaults(test_dict)
    print(settings)