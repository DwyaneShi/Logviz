#!/usr/bin/env python
'''
:mod:`core.viz` is a module containing classes for visualizing logs.
'''

from matplotlib.backends.backend_pdf import PdfPages
from mpl_toolkits.mplot3d import axes3d
from matplotlib import cm
from scipy.interpolate import griddata
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import math

import numpy as np

class Visualization(object):
    PDF_OUTPUT = 0
    PNG_OUTPUT = 1
    PLT_XTICK_LABEL_ROTATION = 'horizontal'

    def __init__(self, data, module=None):
        """Create a log visualization.

        Args:
            data (:list:): Processed log from Parser
            log_type (:str:): Log type
        """

        if not isinstance(data, list):
            raise Exception('Incompatible data type: {}'.format(
                type(data).__name__))
        if module is None:
            raise Exception("Should choose a module to visualize the log file.")

        self.module = module
        self.data = data

        self.x_data = []
        """(:obj:`list` of :obj:`int`): x axis data"""

        self.y_data = []
        """(:obj:`list` of :obj:`int`): y axis data, if the figure is 3-D"""

        self.xticks = []
        """(:obj:`list` of :obj:`int`): x axis ticks"""

        self.yticks = []
        """(:obj:`list` of :obj:`int`): y axis ticks, if the figure is 3-D"""

        self.xtick_labels = []
        """(:obj:`list` of :obj:`str`) x axis tick labels"""

        self.ytick_labels = []
        """(:obj:`list` of :obj:`str`) y axis tick labels, if the figure is 3-D"""

        self.results = {}
        self.fig_height = 0
        self.num_plots = 0

        self._calculate_plot_height()
        self._preprocess_data()

    def _calculate_plot_height(self):
        num_plots = self.module.num_plots()

        self.num_plots = num_plots
        self.fig_height = num_plots * 4

    def _preprocess_data(self):
        self.module.xy_data(self.data)
        self.module.preprocess_data(self.data)

    def save(self, output_path, output_type=PDF_OUTPUT):
        fig = plt.figure()
        self.module.generate_ticks()
        self.module.paint(fig)

        # fig.tight_layout()
        if output_type == Visualization.PDF_OUTPUT:
            pp = PdfPages(output_path)
            pp.savefig()
            pp.close()
        elif output_type == Visualization.PNG_OUTPUT:
            fig.savefig(output_path)
            plt.close(fig)
