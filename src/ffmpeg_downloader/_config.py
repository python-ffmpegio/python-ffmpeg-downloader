from os import path
import os
from ._path import get_dir
from pickle import load, dump
import json
from datetime import datetime, timedelta


def _config_file():
    return path.join(get_dir(), "config.data")


class Config:

    __instance = None
    __inited = False

    def __new__(cls) -> "Config":
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self) -> None:
        if type(self).__inited:
            return
        type(self).__inited = True

        self._data = None
        self.snapshot = {}

        os.makedirs(get_dir(), exist_ok=True)
        self.revert()

    def revert(self):
        try:
            with open(_config_file(), "rb") as f:
                self._data = load(f)
        except:
            self._data = {}

    def dump(self):
        with open(_config_file(), "wb") as f:
            dump(self._data, f)

    @property
    def releases(self):
        try:
            return {**self._data["releases"]}
        except:
            return {}

    @releases.setter
    def releases(self, value):
        self._data["releases"] = {**value}
        self._data["last_updated"] = datetime.now()

    def is_stale(self, stale_in=1):
        try:
            return datetime.now() - timedelta(stale_in) > self._data["last_updated"]
        except:
            return True

    @property
    def install_setup(self):
        try:
            return {**self._data["install_setup"]}
        except:
            return {}

    @install_setup.setter
    def install_setup(self, value):
        self._data["install_setup"] = value and {**value}
