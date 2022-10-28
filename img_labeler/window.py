#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import pickle
import numpy as np

from pyqtgraph    import LabelItem, ImageItem, SignalProxy
from pyqtgraph.Qt import QtGui, QtWidgets, QtCore

class Window(QtGui.QMainWindow):
    def __init__(self, layout, data_manager):
        super().__init__()

        self.createAction()
        self.createMenuBar()
        self.connectAction()

        self.layout       = layout
        self.data_manager = data_manager

        self.timestamp = self.data_manager.timestamp
        self.username  = self.data_manager.username

        self.num_img = len(self.data_manager.data_list)

        self.idx_img = 0

        self.setupButtonFunction()
        self.setupButtonShortcut()
        self.setupMouseModeShortcut()

        self.label_item = ImageItem(None)
        self.layout.viewer_img.getView().addItem(self.label_item)
        self.mask_item = ImageItem(None)
        self.layout.viewer_img.getView().addItem(self.mask_item)

        self.mask_dict = {}
        self.two_click_pos_list = []

        self.proxy_click = None

        self.dispImg()

        return None


    def setupMouseModeShortcut(self):
        QtGui.QShortcut(QtCore.Qt.Key_L, self, self.switchToLabelMode)
        QtGui.QShortcut(QtCore.Qt.Key_M, self, self.switchToMaskMode)
        QtGui.QShortcut(QtCore.Qt.Key_Space, self, self.switchOffMouseMode)


    def switchOffMouseMode(self):
        self.proxy_click = None


    def switchToLabelMode(self):
        self.proxy_click = SignalProxy(self.layout.viewer_img.getView().scene().sigMouseClicked, slot = self.mouseClickedToLabel)


    def switchToMaskMode(self):
        self.proxy_click = SignalProxy(self.layout.viewer_img.getView().scene().sigMouseClicked, slot = self.mouseClickedToMask)


    def mouseClickedToMask(self, event):
        mouse_pos = self.layout.viewer_img.getView().vb.mapSceneToView(event[0].scenePos())

        x = int(mouse_pos.x())
        y = int(mouse_pos.y())

        self.two_click_pos_list.append((x, y))

        if len(self.two_click_pos_list) == 2:
            (x_0, y_0), (x_1, y_1) = self.two_click_pos_list

            mask = self.mask_dict[self.idx_img]
            size_x, size_y = mask.shape[-2:]

            x_0 = min(max(x_0, 0), size_x)
            x_1 = min(max(x_1, 0), size_x)
            y_0 = min(max(y_0, 0), size_y)
            y_1 = min(max(y_1, 0), size_y)

            x_b, x_e = sorted([x_0, x_1])
            y_b, y_e = sorted([y_0, y_1])

            ## mask[0, x_b:x_e+1, y_b:y_e+1] = 1 if np.all(mask[0, x_b:x_e+1, y_b:y_e+1] == 0) == True else 0
            mask_selected = mask[0, x_b:x_e+1, y_b:y_e+1]
            mask_selected = 1 if np.all(mask_selected == 0) == True else 0
            mask[0, x_b:x_e+1, y_b:y_e+1] = mask_selected

            self.dispImg(requires_refresh_img = False, requires_refresh_label = False, requires_refresh_mask = True)
            self.two_click_pos_list = []


    def mouseClickedToLabel(self, event):
        mouse_pos = self.layout.viewer_img.getView().vb.mapSceneToView(event[0].scenePos())

        x = int(mouse_pos.x())
        y = int(mouse_pos.y())

        img, mask = self.data_manager.get_img(self.idx_img)
        size_x, size_y = mask.shape[-2:]
        if x < size_x and y < size_y:
            mask[0, x, y] = 0 if mask[0, x, y] == 1 else 1

        self.dispImg(requires_refresh_img = False, requires_refresh_label = True, requires_refresh_mask = False)


    def config(self):
        self.setCentralWidget(self.layout.area)
        self.resize(700, 700)
        self.setWindowTitle(f"X-ray Diffraction Image Labeler")

        return None


    def setupButtonFunction(self):
        self.layout.btn_next_img.clicked.connect(self.nextImg)
        self.layout.btn_prev_img.clicked.connect(self.prevImg)

        return None


    def setupButtonShortcut(self):
        # w/ buttons
        self.layout.btn_next_img.setShortcut("N")
        self.layout.btn_prev_img.setShortcut("P")

        # w/o buttons
        QtGui.QShortcut(QtCore.Qt.Key_G, self, self.goEventDialog)

        return None


    ###############
    ### DIPSLAY ###
    ###############
    def dispImg(self, requires_refresh_img = True, requires_refresh_label = True, requires_refresh_mask = True):
        # Let idx_img bound within reasonable range....
        self.idx_img = min(max(0, self.idx_img), self.num_img - 1)

        img, label = self.data_manager.get_img(self.idx_img)

        if self.idx_img not in self.mask_dict:
            mask = np.ones(label.shape, dtype = 'uint8')
            self.mask_dict[self.idx_img] = mask
        mask = self.mask_dict[self.idx_img]

        img, label, mask = img[0], label[0], mask[0]

        vmin = np.mean(img)
        vmax = vmin + 6 * np.std(img)

        if requires_refresh_img:
            # Display images...
            self.layout.viewer_img.setImage(img, levels = [vmin, vmax])
            ## self.layout.viewer_img.setHistogramRange(0, 1)
            self.layout.viewer_img.getView().autoRange()

        if requires_refresh_label:
            # Overlay label...
            label_pixel = np.zeros(label.shape + (4, ), dtype = 'uint8')
            label_pixel[:, :, 0][label == 1] = 255
            label_pixel[:, :, 1][label == 1] = 0
            label_pixel[:, :, 2][label == 1] = 0
            label_pixel[:, :, 3][label == 1] = 100

            self.layout.viewer_img.removeItem(self.label_item)
            self.label_item = ImageItem(label_pixel, levels = [0, 128])
            self.layout.viewer_img.addItem(self.label_item)

        if requires_refresh_mask:
            # Overlay label...
            mask_pixel = np.zeros(mask.shape + (4, ), dtype = 'uint8')
            mask_pixel[:, :, 0][mask == 0] = 0
            mask_pixel[:, :, 1][mask == 0] = 0
            mask_pixel[:, :, 2][mask == 0] = 255
            mask_pixel[:, :, 3][mask == 0] = 100

            self.layout.viewer_img.removeItem(self.mask_item)
            self.mask_item = ImageItem(mask_pixel, levels = [0, 128])
            self.layout.viewer_img.addItem(self.mask_item)

        # Display title...
        self.layout.viewer_img.getView().setTitle(f"Sequence number: {self.idx_img}/{self.num_img - 1}")

        return None


    ##################
    ### NAVIGATION ###
    ##################
    def nextImg(self):
        # Support rollover...
        idx_next = self.idx_img + 1
        self.idx_img = idx_next if idx_next < self.num_img else 0

        self.dispImg()

        return None


    def prevImg(self):
        idx_img_current = self.idx_img

        # Support rollover...
        idx_prev = self.idx_img - 1
        self.idx_img = idx_prev if -1 < idx_prev else self.num_img - 1

        # Update image only when next/prev event is found???
        if idx_img_current != self.idx_img:
            self.dispImg()

        return None


    ################
    ### MENU BAR ###
    ################
    def saveStateDialog(self):
        path_pickle, is_ok = QtGui.QFileDialog.getSaveFileName(self, 'Save File', f'{self.timestamp}.pickle')

        if is_ok:
            obj_to_save = ( self.data_manager.data_list,
                            self.data_manager.state_random,
                            self.idx_img,
                            self.timestamp )

            with open(path_pickle, 'wb') as fh:
                pickle.dump(obj_to_save, fh, protocol = pickle.HIGHEST_PROTOCOL)

            print(f"State saved")

        return None


    def loadStateDialog(self):
        path_pickle = QtGui.QFileDialog.getOpenFileName(self, 'Open File')[0]

        if os.path.exists(path_pickle):
            with open(path_pickle, 'rb') as fh:
                obj_saved = pickle.load(fh)
                self.data_manager.data_list     = obj_saved[0]
                self.data_manager.state_random  = obj_saved[1]
                self.idx_img                    = obj_saved[2]
                self.timestamp                  = obj_saved[3]

            self.dispImg()

        return None


    def goEventDialog(self):
        idx, is_ok = QtGui.QInputDialog.getText(self, "Enter the event number to go", "Enter the event number to go")

        if is_ok:
            self.idx_img = int(idx)

            # Bound idx within a reasonable range
            self.idx_img = min(max(0, self.idx_img), self.num_img - 1)

            self.dispImg()

        return None


    def createMenuBar(self):
        menuBar = self.menuBar()

        # File menu
        fileMenu = QtWidgets.QMenu("&File", self)
        menuBar.addMenu(fileMenu)

        fileMenu.addAction(self.loadAction)
        fileMenu.addAction(self.saveAction)

        # Go menu
        goMenu = QtWidgets.QMenu("&Go", self)
        menuBar.addMenu(goMenu)

        goMenu.addAction(self.goAction)

        return None


    def createAction(self):
        self.loadAction = QtWidgets.QAction(self)
        self.loadAction.setText("&Load State")

        self.saveAction = QtWidgets.QAction(self)
        self.saveAction.setText("&Save State")

        self.goAction = QtWidgets.QAction(self)
        self.goAction.setText("&Event")

        return None


    def connectAction(self):
        self.loadAction.triggered.connect(self.loadStateDialog)
        self.saveAction.triggered.connect(self.saveStateDialog)

        self.goAction.triggered.connect(self.goEventDialog)

        return None
