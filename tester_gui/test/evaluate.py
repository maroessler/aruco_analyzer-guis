#!/usr/bin/env python

import os
import math
import numpy as np
from scipy import stats
import pyquaternion as pq
from quaternion_helper import averageQuaternions, quaternion_distance
from natsort import natsorted
import matplotlib.pyplot as plt

def plot_distance():
    _, ax = plt.subplots(nrows=1, ncols=1)
    ax.set_xlim([0,210])
    ax.set_ylim([5,-45])

    property = 'distance'
    board = 'board10_4'

    base_path = os.path.dirname(os.path.realpath(__file__))
    series_path = os.path.join(base_path, property)
    board_path = os.path.join(series_path, board)
    values = natsorted(os.listdir(board_path))

    results = {}
    results[board] = np.array([])

    for value in values:
        value_path = os.path.join(board_path, value)
        target_distance = float(value) / 10.

        with open(value_path) as csv_file:
            data = np.genfromtxt(csv_file, delimiter=',')
            avg = np.average(data[:,3])*100
            std = np.std(data[:,3])
            error = target_distance - avg
            results[board] = np.append(results[board], error)
            print('{}={:.3f}: avg: {:.3f}, std: {:.3f}'.format(property, target_distance, error, std))

    distances = [float(value)/10. for value in values]
    errors = results[board]
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(distances[:-3], errors[:-3])
    ax.plot(distances, errors, label='{}'.format('error'), marker='x', linestyle='-')

    x = np.array(distances)
    y = slope*x+intercept
    z = results[board] - y
    ax.plot(x, y, '-r', label='linear fit')
    ax.plot(x, z, '-g', label='corrected error', marker='x')

    ax.set_xlabel(r'Target Distance (cm)')
    ax.set_ylabel(r'Deviation (cm)')
    ax.set_title('{}:{}'.format(board, property))
    ax.legend()
    ax.grid(True)

    plt.show()

def plot_property(board, property):
    _, ax = plt.subplots(nrows=1, ncols=1)

    base_path = os.path.dirname(os.path.realpath(__file__))
    series_path = os.path.join(base_path, property)
    board_path = os.path.join(series_path, board)
    values = natsorted(os.listdir(board_path))

    results = {}

    for value in values:
        results[value] = np.array([])
        value_path = os.path.join(board_path, value)
        angles = natsorted(os.listdir(value_path))

        for angle in angles:
            angle_path = os.path.join(value_path, angle)

            with open(angle_path) as csv_file:
                data = np.genfromtxt(csv_file, delimiter=',')
                avg = np.average(data[:,1])
                std = np.std(data[:,1])
                average_quat = averageQuaternions(data[:,4:])
                average_quat = pq.Quaternion(average_quat)

                if angle == angles[0]:
                    reference_quat = average_quat

                desired_angle = int(angle)
                distance = quaternion_distance(reference_quat, average_quat, u='deg')
                
                if desired_angle < 180:
                    error = desired_angle - distance
                else:
                    error = desired_angle - 360 + distance

                results[value] = np.append(results[value], error)

        avg = np.average(results[value])
        std = np.std(results[value])
        e_max = np.max(np.absolute(results[value]))
        print('{}={:3}: avg: {:3f}, std: {:3f}, e_max: {:3f}'.format(property, value, avg, std, e_max))

        ax.plot([int(angle) for angle in angles], results[value], label='{}'.format(value), marker='x', linestyle='-')

    ax.set_xlabel(r'Target Angle ($^\circ$)')
    ax.set_ylabel(r'Deviation ($^\circ$)')
    ax.set_xticks(np.arange(0, 360+1, 45))
    ax.set_title('{}:{}'.format(board, property))
    ax.legend()
    ax.grid(True)

    plt.show()

def plot_property_summary():
    results = {}
    series = [
        'CAP_PROP_BRIGHTNESS',
        'CAP_PROP_CONTRAST',
        'CAP_PROP_SATURATION',
    ]
    boards = [
        'board10_6',
        'board10_8',
    ]

    _, axes = plt.subplots(nrows=2, ncols=3)

    faxes = axes.flatten()

    for i, ax in enumerate(faxes):
    #     ax.axhline(color='black')
        ax.set_xlim([-5,105])
        ax.set_ylim([-0.01,0.41])
        ax.set_xlabel('Property Setting (%)')
        ax.set_ylabel(r'Deviation ($^\circ$)')

    base_path = os.path.dirname(os.path.realpath(__file__))

    for i, board in enumerate(boards):
        
        for j, s in enumerate(series):
            series_path = os.path.join(base_path, s)
            board_path = os.path.join(series_path, board)
            values = natsorted(os.listdir(board_path))

            avg_list = list()
            std_list = list()
            emax_list = list()

            for value in values:
                results[value] = np.array([])
                value_path = os.path.join(board_path, value)
                angles = natsorted(os.listdir(value_path))

                for angle in angles:
                    angle_path = os.path.join(value_path, angle)

                    with open(angle_path) as csv_file:

                        data = np.genfromtxt(csv_file, delimiter=',')
                        avg = np.average(data[:,1])
                        std = np.std(data[:,1])

                        average_quat = averageQuaternions(data[:,4:])
                        average_quat = pq.Quaternion(average_quat)

                        if angle == angles[0]:
                            reference_quat = average_quat

                        desired_angle = int(angle)
                        distance = quaternion_distance(reference_quat, average_quat, u='deg')
                        
                        if desired_angle < 180:
                            error = desired_angle - distance
                        else:
                            error = desired_angle - 360 + distance

                        results[value] = np.append(results[value], error)

                avg = np.average(results[value])
                std = np.std(results[value])
                e_max = np.max(np.absolute(results[value]))
                print('{}={:3}: avg: {:3f}, std: {:3f}, e_max: {:3f}'.format(s, value, avg, std, e_max))

                avg_list.append(avg)
                std_list.append(std)
                emax_list.append(e_max)

            axes[i][j].plot([int(v) for v in values], avg_list, marker='x', label='avg')
            axes[i][j].plot([int(v) for v in values], std_list, marker='x', label='std')
            axes[i][j].plot([int(v) for v in values], emax_list, marker='x', label='e_max')
            axes[i][j].set_title('{}:{}'.format(board, s))
            axes[i][j].legend()
            axes[i][j].grid(True)

    plt.show()

def plot():
    series = '5'
    base_path = os.path.dirname(os.path.realpath(__file__))
    series_path = os.path.join(base_path, series)
    markers = natsorted(os.listdir(series_path))
    markers.remove('meta')

    cols = math.ceil(math.sqrt(len(markers)))
    rows = math.floor(math.sqrt(len(markers)))

    titles = {
        '5' : 'ArUco Marker 5cm',
        '10' : 'ArUco Marker 10cm',
        'board2' : 'ArUco Board 2x2',
        'board5' : 'ArUco Board 5x5',
        'board7' : 'ArUco Board 7x7',
        'board10' : 'ArUco Board 10x10',
        'board15' : 'ArUco Board 15x15',
    }
    results = {}

    _, axes = plt.subplots(nrows=rows, ncols=cols)
    axes = axes.flatten()

    for i, ax in enumerate(axes):
        if i >= len(markers):
            ax.set_visible(False)
        ax.axhline(color='black')
        ax.set_xlim([-5,365])
        ax.set_ylim([-0.25,0.25])
        ax.set_xlabel(r'Target Angle ($^\circ$)')
        ax.set_ylabel(r'Deviation ($^\circ$)')

    for i, marker in enumerate(markers):
        marker_path = os.path.join(series_path, marker)
        if not os.path.isdir(marker_path):
            print('marker not found')
            continue
        results[marker] = np.array([])
        angles = natsorted(os.listdir(marker_path))
        angles = list(filter(lambda s: s.isdigit(), angles))

        reference_quat = pq.Quaternion()
        for angle in angles:
            desired_angle = int(angle)
            file = os.path.join(marker_path, angle)

            with open(file) as csv_file:
                data = np.genfromtxt(csv_file, delimiter=',')
                avg = np.average(data[:,1])
                std = np.std(data[:,1])
                average_quat = averageQuaternions(data[:,4:])
                average_quat = pq.Quaternion(average_quat)

                if angle == angles[0]:
                    reference_quat = average_quat

                distance = quaternion_distance(reference_quat, average_quat, u='deg')

                if desired_angle < 180:
                    error = desired_angle - distance
                else:
                    error = desired_angle - 360 + distance

                results[marker] = np.append(results[marker], error)
                print('angle {:3}: {:.3f}'.format(desired_angle, error))

        avg = np.average(results[marker])
        std = np.std(results[marker])
        e_max = np.max(np.absolute(results[marker]))
        axes[i].text(0.99, 0.95, 'avg: {:.3f}'.format(avg), horizontalalignment='right', verticalalignment='top', transform=axes[i].transAxes)
        axes[i].text(0.99, 0.85, 'std: {:.3f}'.format(std), horizontalalignment='right', verticalalignment='top', transform=axes[i].transAxes)
        axes[i].text(0.99, 0.75, 'max: {:.3f}'.format(e_max), horizontalalignment='right', verticalalignment='top', transform=axes[i].transAxes)

        angles = [int(angle) for angle in angles]
        
        axes[i].set_xticks(np.arange(0, 360+1, 45))
        axes[i].scatter(x=angles, y=results[marker], marker='x')
        axes[i].set_title(titles[marker])
        # axes[i].legend()
        axes[i].grid(True)

    plt.show()

if __name__ == "__main__":
    plot()
    plot_property_summary()
    plot_property(board='board10_6', property='CAP_PROP_CONTRAST')
    plot_distance()