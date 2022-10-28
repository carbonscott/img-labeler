#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pickle
import os
import numpy as np
import random
from datetime import datetime

from img_labeler.utils  import set_seed

class DataManager:
    def __init__(self):
        super().__init__()

        # Internal variables...
        self.img_state_dict = {}

        self.timestamp = self.get_timestamp()

        self.state_random = [random.getstate(), np.random.get_state()]

        return None


    def get_timestamp(self):
        now = datetime.now()
        timestamp = now.strftime("%Y_%m%d_%H%M_%S")

        return timestamp


    def save_random_state(self):
        self.state_random = (random.getstate(), np.random.get_state())

        return None


    def set_random_state(self):
        state_random, state_numpy = self.state_random
        random.setstate(state_random)
        np.random.set_state(state_numpy)

        return None




class FastData(DataManager):

    def __init__(self, config_data):
        super().__init__()

        # Imported variables...
        self.path_fastdata = getattr(config_data, 'path_fastdata' , None)
        self.username  = getattr(config_data, 'username' , None)
        self.seed      = getattr(config_data, 'seed'     , None)

        # Internal variables...
        self.data_list = []

        set_seed(self.seed)

        self.load_dataset()

        return None


    def load_dataset(self):
        with open(self.path_fastdata, 'rb') as fh:
            data_list = pickle.load(fh)

        self.data_list = data_list

        return None


    def get_img(self, idx):
        img, mask = self.data_list[idx]

        # Save random state...
        # Might not be useful for this labeler
        if not idx in self.img_state_dict:
            self.save_random_state()
            self.img_state_dict[idx] = self.state_random
        else:
            self.state_random = self.img_state_dict[idx]
            self.set_random_state()

        return img, mask
