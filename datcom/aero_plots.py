import numpy as np
import matplotlib.pyplot as plt

from aero_model import *

def pitch_plane_dataset(coefficients):
    CF_wind = []
    CM_body = []
    for index, cf_cm in enumerate(coefficients):
        cf = cf_cm[0]
        cm = cf_cm[1]
        R = R_wind2bod(np.radians(alpha_range[index])).T
        cf[0] = -cf[0]
        cf[2] = -cf[2]
        CF_wind.append(R @ cf)
        CM_body.append(cm)
    # Extract drag and lift
    drag = [force[0] for force in CF_wind]
    lift = [force[2] for force in CF_wind]
    pitching = [moment[1] for moment in CM_body]
    return drag, lift, pitching

def plot_pitch_plane(datasets, labels):

    fig_lift = plt.figure()
    fig_drag = plt.figure()
    fig_pitching = plt.figure()

    for dataset, label in zip(datasets, labels):
        drag, lift, pitching = pitch_plane_dataset(dataset)
        # Plot lift versus alpha
        plt.figure(fig_lift.number)
        plt.plot(alpha_range, lift, label=label)
        plt.xlabel('Alpha (degrees)')
        plt.ylabel('CL')
        plt.title('Lift vs Alpha')
        plt.legend()
        plt.grid(True)

        plt.figure(fig_drag.number)
        plt.plot(alpha_range, drag, label=label)
        plt.xlabel('Alpha (degrees)')
        plt.ylabel('CD')
        plt.title('Drag vs Alpha')
        plt.legend()
        plt.grid(True)

        plt.figure(fig_pitching.number)
        plt.plot(alpha_range, pitching, label=label)
        plt.xlabel('Alpha (degrees)')
        plt.ylabel('CM')
        plt.title('Pitching Moment vs Alpha')
        plt.legend()
        plt.grid(True)

        # Plot drag polar (Lift vs Drag)
        # plt.plot(drag, lift, label='Drag Polar', label=label)
        # plt.xlabel('Drag')
        # plt.ylabel('Lift')
        # plt.title('Drag Polar')
        # plt.legend()
        # plt.grid(True)
    plt.show()


# Plot CL versus alpha
surfaces = {
   'flaps' : 0,
   'elevator': np.radians(10),
   'ailerons': 0
}

# Case: All surfaces zero
coefficients = [aero_coefficients(np.radians(alpha)) for alpha in alpha_range]
coefficients_elevator = [aero_coefficients(np.radians(alpha), surfaces=surfaces) for alpha in alpha_range]

plot_pitch_plane([coefficients, coefficients_elevator], ['All surfaces zero', 'Elevator 10 deg'])
