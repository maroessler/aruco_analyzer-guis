#!/usr/bin/env python
import os
import math
import yaml
import re
import numpy as np
import pyquaternion as pq
from scipy.spatial.transform import Rotation as R
from quaternion_helper import averageQuaternions, quaternion_distance
from natsort import natsorted
import matplotlib.pyplot as plt

def plot_position():
    base_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(base_path, 'position1')

    # load meta file
    meta_file = os.path.join(test_path, 'meta.yaml')
    with open(meta_file, 'r') as stream:
        try:
            meta = yaml.safe_load(stream)
        except yaml.YAMLError as e:
            print(e)
            exit()

    # get all data_files, remove meta.yaml
    # pattern = re.compile('[0-9]+_[0-9]+.csv')
    pattern = re.compile('3+_[0-9]+.csv')
    # pattern = re.compile('[0-9]+_7+.csv')
    data_files = natsorted(os.listdir(test_path))
    data_files = list(filter(lambda s: pattern.match(s), data_files))

    x_axis = []
    data = []

    for data_file in data_files:
        print(data_file)
        file = os.path.join(test_path, data_file)
        coordinates = tuple(map(int, (data_file.split('.')[0].split('_'))))
        expected = np.array([(coordinates[0]-3)*meta['square_size'], meta['height'], meta['distance'] + coordinates[1]*meta['square_size']])

        x_axis.append(expected[2]*100)

        with open(file) as csv_file:
            raw_data = np.genfromtxt(csv_file, delimiter=',')
            average_position = np.array([np.average(raw_data[:,1]), np.average(raw_data[:,2]), np.average(raw_data[:,3])])
            average_quat = pq.Quaternion(averageQuaternions(raw_data[:,4:])).normalised
            # rot = average_quat.yaw_pitch_roll
            # r = R.from_rotvec([-24/180.*np.pi,0,0])
            # average_position = r.apply(average_position)
            # rotate position
            # average_position = transform(average_position, average_quat.inverse)

            error = average_position-expected
            data.append(error*100)
            print(average_position)
            # print(error)
            # print(np.array([np.std(raw_data[:,1]), np.std(raw_data[:,2]), np.std(raw_data[:,3])])*100)



    _, ax = plt.subplots(1)
    ax.set_xlabel('z-axis position in cm')
    ax.set_ylabel('error in cm')
    ax.plot(x_axis, ([x[0] for x in data]), marker=',', ls='-', label='x', c='red')
    ax.plot(x_axis, ([x[1] for x in data]), marker=',', ls='-', label='y', c='green')
    ax.plot(x_axis, ([x[2] for x in data]), marker=',', ls='-', label='z', c='blue')

    # for ax in ax:
    # ax.set_ylim([-1.25, 1.25])
    ax.grid(True)
    ax.legend()

    # plt.suptitle(meta['title'])

    plt.show()

def transform(position, q):
    position_ = np.zeros((4))
    position_[1:] = position
    position = q * position_ * q.inverse

    return position.elements[1:]

def plot():
    test = '2'
    series = [
        '1', 
        '2', 
        '3', 
        '4',
        '5',
    ]
    base_path = os.path.dirname(os.path.realpath(__file__))
    test_path = os.path.join(base_path, test)

    rows = int(math.floor(math.sqrt(len(series))))
    cols = int(math.ceil(math.sqrt(len(series))))
    _, axes = plt.subplots(nrows=rows, ncols=cols)
    
    if type(axes) is np.ndarray:
        axes = axes.flatten()
    else:
        axes = np.asarray([axes])

    # plt.delaxes(axes[-1])

    for s, ax in zip(series, axes):
        series_path = os.path.join(test_path, s)
        plot_single(series_path, ax)

    # plt.suptitle('Difference between two consecutive measurement angles')
    plt.show()

def plot_single(series_path, ax):
    angles = natsorted(os.listdir(series_path))
    angles = list(map(int,filter(lambda s: s.isdigit(), angles)))

    ax.set_xticks(np.arange(0, 360+1, 45))
    ax.grid(True)
    ax.set_xlim([0,360])
    # ylim = 0.2
    ax.set_ylim([-1,2.5])

    reference_quat = None
    previous_quat = None
    results = list()
    results_per_axis = list()
    results2 = list()
    camera_angle = list()
    for angle in angles:
        file = os.path.join(series_path, str(angle))

        with open(file) as csv_file:
            data = np.genfromtxt(csv_file, delimiter=',')
            average_quat = pq.Quaternion(averageQuaternions(data[:,4:]))

            if reference_quat is None:
                previous_quat = average_quat
                reference_quat = average_quat

            # calculate camera angle
            camera_angle_ = clip_angle(math.degrees(average_quat.yaw_pitch_roll[2])+90)
            camera_angle.append(camera_angle_)

            ## difference between two consecutive attitudes
            if previous_quat is average_quat:
                results_per_axis.append((0,0,-2))
                results.append(0)
            else:
                delta_quat = previous_quat.inverse * average_quat
                euler = map(math.degrees, delta_quat.yaw_pitch_roll)
                results_per_axis.append((euler[2], euler[1], euler[0]))
                results.append(abs(delta_quat.degrees)-2)
                previous_quat = average_quat

            ## error between calculated attitude and estimated attitude
            ## not reliable since dependent on accuracy of reference_quat
            # delta_angle = pq.Quaternion(axis=(0,0,1), degrees=-angle)
            # desired_quat = reference_quat * delta_angle
            # error = abs((desired_quat.inverse * average_quat).degrees)
            # results.append(error)  
                  
            ## not reliable since dependent on accuracy of reference_quat
            # corrected_quat = reference_quat.inverse * average_quat
            # euler = map(math.degrees, corrected_quat.yaw_pitch_roll)
            # results_per_axis.append((euler[2], euler[1], (clip_angle(180-angle-euler[0]))))

            # error between reference attitude and estimated attitude
            distance = abs((reference_quat.inverse * average_quat).degrees)
            if angle<180:
                error = angle - distance
            else:
                error = angle - 360 + distance
            results2.append(abs(error))

    camera_angle = np.average(camera_angle)

    avg = np.average(results)
    std = np.std(results)
    e_max = np.max(np.absolute(results))

    ax.text(0.99, 0.25, 'avg: {:.3f}'.format(avg), horizontalalignment='right', verticalalignment='top', transform=ax.transAxes)
    ax.text(0.99, 0.15, 'std: {:.3f}'.format(std), horizontalalignment='right', verticalalignment='top', transform=ax.transAxes)
    ax.text(0.99, 0.05, 'max: {:.3f}'.format(e_max), horizontalalignment='right', verticalalignment='top', transform=ax.transAxes)

    # avg = np.average(results2)
    # std = np.std(results2)
    # e_max = np.max(np.absolute(results2))

    # ax.text(0.2, 0.25, 'avg: {:.3f}'.format(avg), horizontalalignment='right', verticalalignment='top', transform=ax.transAxes)
    # ax.text(0.2, 0.15, 'std: {:.3f}'.format(std), horizontalalignment='right', verticalalignment='top', transform=ax.transAxes)
    # ax.text(0.2, 0.05, 'max: {:.3f}'.format(e_max), horizontalalignment='right', verticalalignment='top', transform=ax.transAxes)

    angles = [angles[i] for i in xrange(0, len(angles), 10)]
    results = [results[i] for i in xrange(0, len(results), 10)]
    results_per_axis = [results_per_axis[i] for i in xrange(0, len(results_per_axis), 10)]
    results2 = [results2[i] for i in xrange(0, len(results2), 10)]

    # ax.plot(angles, results, marker=',', ls='-', c='black')
    ax.plot(angles, ([x[0] for x in results_per_axis]), marker=',', ls='-', label='x', c='red')
    ax.plot(angles, ([x[1] for x in results_per_axis]), marker=',', ls='-', label='y', c='green')
    ax.plot(angles, ([-x[2] for x in results_per_axis]), marker=',', ls='-', label='z', c='blue')
    # ax.plot(angles, results2, marker=',', ls='-', c='brown')

    ax.set_title('Camera Angle: {:.3f}'.format(camera_angle))

    ax.legend()

def clip_angle(angle):
    return angle%360-180

if __name__ == "__main__":
    plot_position()
