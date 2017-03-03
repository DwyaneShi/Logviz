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

import numpy as np


class Visualization(object):
    PDF_OUTPUT = 0
    PNG_OUTPUT = 1
    PLT_XTICK_LABEL_ROTATION = 'horizontal'

    def __init__(self, data, log_type):
        """Create a log visualization.

        Args:
            data (:list:): Processed log from Parser
            log_type (:str:): Log type
        """

        if not isinstance(data, list):
            raise Exception('Incompatible data type: {}'.format(
                type(data).__name__))

        self.data = data
        self.log_type = log_type.split('-')[0]
        self.log_subtype = log_type.split('-')[1]

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

        self.ecb_total_throughput = {}
        self.ecb_throughput = {}
        self.ecb_latency = {}
        self.fig_height = 0
        self.num_plots = 0

        self._calculate_plot_height()
        self._preprocess_data()

    def _calculate_plot_height(self):
        num_plots = 0

        if self.log_type == "ECB":
            num_plots = 1

        self.num_plots = num_plots
        self.fig_height = num_plots * 4

    def _preprocess_data(self):
        self.xdata = None
        self.ydata = None
        if self.log_type == "ECB":
            xdata = set()
            ydata = set()
            for data in self.data:
                xdata.add(data["chunk_size"])
                ydata.add(data["threads_num"])
        self.xdata = sorted(xdata)
        self.ydata = sorted(ydata)

        xcount = len(self.xdata)
        xtick_label_stepsize = xcount / 15
        if xtick_label_stepsize == 0:
            xtick_label_stepsize = 1
        self.xticks = np.arange(0, xcount, xtick_label_stepsize)
        self.xtick_labels = [self.__to_size(self.xdata[i]) for i in self.xticks]

        ycount = len(self.ydata)
        ytick_label_stepsize = ycount / 15
        if ytick_label_stepsize == 0:
            ytick_label_stepsize = 1
        self.yticks = np.arange(0, ycount, ytick_label_stepsize)
        self.ytick_labels = [self.ydata[i] for i in self.yticks]

        if self.log_type == "ECB":
            for data in self.data:
                self.coder = data["coder"].replace("Java", "").strip()
                if self.coder == "Mellanox":
                    self.coder = "Mellanox EC Offload"
                method = data["method"]
                chunk_size = data["chunk_size"]
                buffer_size = data["buffer_size"]
                threads_num = data["threads_num"]
                factor = buffer_size * threads_num
                iteration = data["total_data_size"] / factor
                if method not in self.ecb_throughput:
                    self.ecb_throughput[method] = {}
                    self.ecb_total_throughput[method] = {}
                    self.ecb_latency[method] = {}
                if iteration not in self.ecb_throughput[method]:
                    self.ecb_throughput[method][iteration] = {}
                    self.ecb_total_throughput[method][iteration] = {}
                    self.ecb_latency[method][iteration] = {}
                if chunk_size not in self.ecb_throughput[method][iteration]:
                    self.ecb_throughput[method][iteration][chunk_size] = {}
                    self.ecb_total_throughput[method][iteration][chunk_size] = {}
                    self.ecb_latency[method][iteration][chunk_size] = {}
                if threads_num in self.ecb_throughput[method][iteration][chunk_size] \
                and self.ecb_throughput[method][iteration][chunk_size][threads_num]:
                    self.ecb_throughput[method][iteration][chunk_size][threads_num].append(data["total_throughput"] / threads_num)
                    self.ecb_total_throughput[method][iteration][chunk_size][threads_num].append(data["total_throughput"])
                    self.ecb_latency[method][iteration][chunk_size][threads_num].append(data["time_avg"])
                else:
                    self.ecb_throughput[method][iteration][chunk_size][threads_num] = [data["total_throughput"] / threads_num]
                    self.ecb_total_throughput[method][iteration][chunk_size][threads_num] = [data["total_throughput"]]
                    self.ecb_latency[method][iteration][chunk_size][threads_num] = [data["time_avg"]]

            for method in self.ecb_throughput:
                for iteration in self.ecb_throughput[method]:
                    for chunk_size in self.ecb_throughput[method][iteration]:
                        for threads_num in self.ecb_throughput[method][iteration][chunk_size]:
                            self.ecb_throughput[method][iteration][chunk_size][threads_num] = \
                                np.mean(self.ecb_throughput[method][iteration][chunk_size][threads_num])
                            self.ecb_total_throughput[method][iteration][chunk_size][threads_num] = \
                                np.mean(self.ecb_total_throughput[method][iteration][chunk_size][threads_num])
                            self.ecb_latency[method][iteration][chunk_size][threads_num] = \
                                np.mean(self.ecb_latency[method][iteration][chunk_size][threads_num])

    def __throughput_array(self, source, xdata, ydata):
        temp_array = [source[x][y] for x, y in zip(np.ravel(xdata), np.ravel(ydata))]
        unit = "MB"
        if np.mean(temp_array) > 5 * 1024:
            temp_array = [x / 1024 for x in temp_array]
            unit = "GB"
        return (unit, np.array(temp_array))

    def save(self, output_path, output_type=PDF_OUTPUT):
        plt_idx = 1
        fig = plt.figure()

        if self.log_type == "ECB":
            x_labels = 14
            y_labels = 7
            method = "encode"
            blocks = 1024

        if self.log_type == "ECB" and self.log_subtype == "TotalThroughput":
            ax = fig.gca(projection='3d')
            total_throughput = self.ecb_total_throughput[method][blocks]
            xticks, yticks = np.meshgrid(self.xticks, self.yticks)
            xdata, ydata = np.meshgrid(self.xdata, self.ydata)
            unit, zticks = self.__throughput_array(total_throughput, xdata, ydata)
            zticks = zticks.reshape(xdata.shape)
            ax.plot_surface(xticks, yticks, zticks, alpha=0.6)
            xtick_labels = [self.xtick_labels[int(x)] for x in ax.get_xticks() if int(x) in range(len(self.xtick_labels))]
            ytick_labels = [self.ytick_labels[int(y)] for y in ax.get_yticks() if int(y) in range(len(self.ytick_labels))]
            for i in range(len(xtick_labels)):
                if (i % 2) == 1:
                    xtick_labels[i] = ""
            for i in range(len(ytick_labels)):
                if (i % 2) == 1:
                    ytick_labels[i] = ""
            ax.contour(xticks, yticks, zticks, zdir='x', offset=0, cmap=cm.coolwarm)
            ax.contour(xticks, yticks, zticks, zdir='y', offset=y_labels - 1, cmap=cm.coolwarm)
            # ax.contour(xticks, yticks, zticks, zdir='z', offset=0, cmap=cm.coolwarm)
            ax.set_xlabel('Chunk Size')
            ax.set_xlim(0, x_labels - 1)
            ax.set_ylabel('#Threads')
            ax.set_ylim(0, y_labels - 1)
            ax.set_zlabel('Total Throughput ({}/sec)'.format(unit))
            ax.set_zlim(0)
            ax.set_xticklabels(xtick_labels)
            ax.set_yticklabels(ytick_labels)

            plt.title('Total Throughput - {}'.format(self.coder))
            plt_idx += 1
        elif self.log_type == "ECB" and self.log_subtype == "Throughput":
            ax = fig.gca(projection='3d')
            throughput = self.ecb_throughput[method][blocks]
            xticks, yticks = np.meshgrid(self.xticks, self.yticks)
            xdata, ydata = np.meshgrid(self.xdata, self.ydata)
            unit, zticks = self.__throughput_array(throughput, xdata, ydata)
            zticks = zticks.reshape(xdata.shape)
            ax.plot_surface(xticks, yticks, zticks, alpha=0.6)
            xtick_labels = [self.xtick_labels[int(x)] for x in ax.get_xticks() if int(x) in range(len(self.xtick_labels))]
            ytick_labels = [self.ytick_labels[int(y)] for y in ax.get_yticks() if int(y) in range(len(self.ytick_labels))]
            for i in range(len(xtick_labels)):
                if (i % 2) == 1:
                    xtick_labels[i] = ""
            for i in range(len(ytick_labels)):
                if (i % 2) == 1:
                    ytick_labels[i] = ""
            ax.contour(xticks, yticks, zticks, zdir='x', offset=0, cmap=cm.coolwarm)
            ax.contour(xticks, yticks, zticks, zdir='y', offset=y_labels - 1, cmap=cm.coolwarm)
            # ax.contour(xticks, yticks, zticks, zdir='z', offset=0, cmap=cm.coolwarm)
            ax.set_xlabel('Chunk Size')
            ax.set_xlim(0, x_labels - 1)
            ax.set_ylabel('#Threads')
            ax.set_ylim(0, y_labels - 1)
            ax.set_zlabel('Throughput ({}/sec)'.format(unit))
            ax.set_zlim(0)
            ax.set_xticklabels(xtick_labels)
            ax.set_yticklabels(ytick_labels)

            plt.title('Throughput - {}'.format(self.coder))
            plt_idx += 1
        elif self.log_type == "ECB" and self.log_subtype == "Latency":
            ax = fig.gca(projection='3d')
            latency = self.ecb_latency[method][blocks]
            xticks, yticks = np.meshgrid(self.xticks, self.yticks)
            xdata, ydata = np.meshgrid(self.xdata, self.ydata)
            zticks = np.array([latency[x][y] for x, y in zip(np.ravel(xdata), np.ravel(ydata))])
            zticks = zticks.reshape(xdata.shape)
            ax.plot_surface(xticks, yticks, zticks, alpha=0.6)
            xtick_labels = [self.xtick_labels[int(x)] for x in ax.get_xticks() if int(x) in range(len(self.xtick_labels))]
            ytick_labels = [self.ytick_labels[int(y)] for y in ax.get_yticks() if int(y) in range(len(self.ytick_labels))]
            for i in range(len(xtick_labels)):
                if (i % 2) == 1:
                    xtick_labels[i] = ""
            for i in range(len(ytick_labels)):
                if (i % 2) == 1:
                    ytick_labels[i] = ""
            ax.contour(xticks, yticks, zticks, zdir='x', offset=0, cmap=cm.coolwarm)
            ax.contour(xticks, yticks, zticks, zdir='y', offset=y_labels - 1, cmap=cm.coolwarm)
            # ax.contour(xticks, yticks, zticks, zdir='z', offset=0, cmap=cm.coolwarm)
            ax.set_xlabel('Chunk Size')
            ax.set_xlim(0, x_labels - 1)
            ax.set_ylabel('#Threads')
            ax.set_ylim(0, y_labels - 1)
            ax.set_zlabel('Latency (sec)')
            ax.set_zlim(0)
            ax.set_xticklabels(xtick_labels)
            ax.set_yticklabels(ytick_labels)

            plt.title('Latency - {}'.format(self.coder))
            plt_idx += 1

        # fig.tight_layout()
        if output_type == Visualization.PDF_OUTPUT:
            pp = PdfPages(output_path)
            pp.savefig()
            pp.close()
        elif output_type == Visualization.PNG_OUTPUT:
            fig.savefig(output_path)
            plt.close(fig)

    def __to_size(self, num):
        string = "{}B".format(num)
        if num >= 1024 and num % 1024 == 0:
            num /= 1024
            string = "{}KB".format(num)
        if num >= 1024 and num % 1024 == 0:
            num /= 1024
            string = "{}MB".format(num)
        if num >= 1024 and num % 1024 == 0:
            num /= 1024
            string = "{}GB".format(num)
        return string
