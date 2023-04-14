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




class PeakNetData(DataManager):
    """
    PeakNet Data (PND) are produced by PeakNet by converting peak information
    in stream files into a tensor/ndarray.

    Tensor shape: (N, 2, H, W)
    - N: The number of data points that have been selected.
    - 2: It refers to a pair of an image and its corresponding label.
    - H, W: The height and width of both the image and its corresponding label.  

    Main tasks of this class:
    - Offers `get_img` function that returns a data point tensor with the shape
      (2, H, W).
    - Offers an interface that allows users to modify the label tensor with the
      shape (1, H, W).  The label tensor only supports integer type.
    """

    def __init__(self, config_data):
        super().__init__()

        # Imported variables...
        self.path_pnd      = getattr(config_data, 'path_pnd'     , None)
        self.username      = getattr(config_data, 'username'     , None)
        self.seed          = getattr(config_data, 'seed'         , None)
        self.layer_manager = getattr(config_data, 'layer_manager', None)

        if self.layer_manager is None:
            layer_metadata = {
                0 : {'name' : 'bgs', 'color' : '#FFFFFF'},
                1 : {'name' : 'pks', 'color' : '#FF0000'},
                2 : {'name' : 'flaw', 'color' : '#00FF00'},
            }
            layer_order  = [0, 1, 2]
            layer_active = 2
            self.layer_manager = LayerManager(layer_metadata = layer_metadata,
                                              layer_order    = layer_order,
                                              layer_active   = layer_active)

        # Internal variables...
        self.data_list = []

        set_seed(self.seed)

        self.load_dataset()

        return None


    def load_dataset(self):
        with open(self.path_pnd, 'rb') as fh:
            data_list = pickle.load(fh)

        self.data_list = data_list

        return None


    def get_img(self, idx):
        img, label = self.data_list[idx]

        # Save random state...
        # Might not be useful for this labeler
        if not idx in self.img_state_dict:
            self.save_random_state()
            self.img_state_dict[idx] = self.state_random
        else:
            self.state_random = self.img_state_dict[idx]
            self.set_random_state()

        return img, label




class LayerManager:
    def __init__(self, layer_metadata, layer_order, layer_active):
        self.layer_metadata = layer_metadata
        self.layer_order    = layer_order
        self.layer_active   = layer_active
