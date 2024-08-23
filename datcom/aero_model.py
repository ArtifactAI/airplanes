import numpy as np

from output_parser import parse_datcom_output

import pandas as pd
from scipy.interpolate import RegularGridInterpolator

def R_wind2bod(alpha, beta=0):
    # alpha and beta must be in radians
    R2_alpha = np.array([
        [np.cos(alpha),  0, -np.sin(alpha)],
        [0,              1,  0            ],
        [np.sin(alpha),  0,  np.cos(alpha)]
    ])

    R3_negBeta = np.array([
        [np.cos(-beta), np.sin(-beta), 0],
        [-np.sin(-beta),  np.cos(-beta), 0],
        [0, 0, 1],
    ])

    return R2_alpha @ R3_negBeta

class Interpolator:
    def __init__(self, n_independent_vars, data_file=None, dataframe=None):
        if data_file is not None:
            self.df = pd.read_csv(data_file)
        elif dataframe is not None:
            self.df = dataframe
        self.n_independent_vars = n_independent_vars
        self.independent_vars = self.df.iloc[:, :self.n_independent_vars].values
        self.dependent_vars = self.df.iloc[:, self.n_independent_vars:].values
        self.grid_axes = [sorted(set(self.independent_vars[:, i])) for i in range(self.n_independent_vars)]
        self.interpolators = [
            RegularGridInterpolator(self.grid_axes, self.dependent_vars[:, i].reshape([len(ax) for ax in self.grid_axes]))
            for i in range(self.dependent_vars.shape[1])
        ]

    def interpolate(self, *args, clamp=True):
        if not isinstance(args, list):
            args = [args]
        
        if clamp:
            # Clamp the input args to the grid boundaries
            lookup_args = []
            for i, arg in enumerate(args):
                min_val = min(self.grid_axes[i])
                max_val = max(self.grid_axes[i])
                lookup_args.append(max(min(arg, max_val), min_val))
        else:
            lookup_args = args
        
        return [interp(lookup_args).item() for interp in self.interpolators]
    

data = parse_datcom_output('datcom/datcom.out')

s_ref = data['reference_data']['S_ref']['value']
b_ref = data['reference_data']['b_ref']['value']
c_ref = data['reference_data']['c_ref']['value']  
x_ref = data['reference_data']['x_ref']['value']
z_ref = data['reference_data']['z_ref']['value']
r_ref = [x_ref, 0, z_ref]

rigid_body_static_interpolator = Interpolator(1, dataframe=data['rigid_body_static'])
rigid_body_dynamic_interpolator = Interpolator(1, dataframe=data['rigid_body_dynamic'])

# Create interpolator for flaps if present in the data
if 'flaps' in data:
    flap_coef_increments_interpolator = Interpolator(2, dataframe=data['flaps']['coef_increments'])
    flap_induced_drag_interpolator = Interpolator(2, dataframe=data['flaps']['induced_drag_increments'])

# Create interpolator for elevator if present in the data
if 'elevator' in data:
    elevator_coef_increments_interpolator = Interpolator(2, dataframe=data['elevator']['coef_increments'])
    elevator_induced_drag = data['elevator']['induced_drag_increments']
    alpha_values = elevator_induced_drag.iloc[:, 0].tolist()
    delta_values = elevator_induced_drag.columns.tolist()[1:]
    elevator_induced_drag_interpolator = RegularGridInterpolator((alpha_values, delta_values), elevator_induced_drag.values[:, 1:])

# Create interpolator for ailerons if present in the data
if 'ailerons' in data:
    aileron_roll_coef_interpolator = Interpolator(2, dataframe=data['ailerons']['roll_coefficient'])
    aileron_yaw_coef = data['ailerons']['yaw_coefficient']
    alpha_values = aileron_yaw_coef.iloc[:, 0].tolist()
    delta_values = aileron_yaw_coef.columns.tolist()[1:]
    aileron_yaw_coef_interpolator = RegularGridInterpolator((alpha_values, delta_values), aileron_yaw_coef.values[:, 1:])


def rigid_body_static_coefficients(alpha, beta):

    # TODO: revist angular units in datcom input file generation and output parsing
    alpha = np.degrees(alpha)
    beta = np.degrees(beta)

    # interpolate on alpha  
    CD, CL, CMy, CN, CA, XCP, CLA, CMA, CYB, CNB, CLB = rigid_body_static_interpolator.interpolate(alpha)

    CY = CYB*beta
    CMx = CLB*beta
    CMz = CNB*beta

    CF = np.array([-CA, CY, -CN])
    CM = np.array([CMx, CMy, CMz])

    return CF, CM

def rigid_body_dynamic_coefficients(alpha, beta, p, q, r):

    # TODO: revist angular units in datcom input file generation and output parsing
    alpha = np.degrees(alpha)
    beta = np.degrees(beta)
    p = np.degrees(p)
    q = np.degrees(q)
    r = np.degrees(r)

    CLQ, CMQ, CLP, CYP, CNP, CNR, CLR = rigid_body_dynamic_interpolator.interpolate(alpha)

    CY = CYP*q

    CMx = CLP*p + CLQ*q + CLR*r
    CMy = CMQ*q
    CMz = CNP*p + CNR*r

    CF = np.array([0, CY, 0])
    CM = np.array([CMx, CMy, CMz])

    return CF, CM

def symmetric_control_surface_coefficients(surface_name, alpha, beta, deflection):

    alpha = np.degrees(alpha)
    beta = np.degrees(beta)
    deflection = np.degrees(deflection)

    if surface_name == 'flaps':
        coef_increments = flap_coef_increments_interpolator
        induced_drag = flap_induced_drag_interpolator
    elif surface_name == 'elevator':
        coef_increments = elevator_coef_increments_interpolator
        induced_drag = elevator_induced_drag_interpolator
        
    D_CL, D_CM, D_CL_max, D_CD_min = coef_increments.interpolate(deflection)
    D_CDI = induced_drag.interpolate((alpha, deflection))

    CF = R_wind2bod(alpha, beta) @ np.array([-D_CDI, 0, -D_CL])
    CM = np.array([0, D_CM, 0])
    
    return CF, CM

def asymmetric_control_surface_coefficients(alpha, beta, deflection):
    alpha = np.degrees(alpha)
    beta = np.degrees(beta)
    deflection = np.degrees(deflection)

    total_deflection = deflection * 2

    D_CROLL = aileron_roll_coef_interpolator.interpolate(deflection)
    D_CYAW = aileron_yaw_coef_interpolator.interpolate((alpha, total_deflection))

    CF = np.array([0,0,0])
    CM = np.array([D_CROLL, 0, D_CYAW])
    
    return CF, CM

def aero_coefficients(alpha, beta, surfaces: List):

    # Coefficients in order CFx, CFy, CFz, CMx, CMy, CMz

    coefficients = aero_model.interpolate(alpha)
    
    # TODO: have AI write this function
    # Check for NaN values in coefficients and replace them with zero
    coefficients = [0 if np.isnan(coeff) else coeff for coeff in coefficients]

    CD, CL, CM, CN, CA, XCP, CLA, CMA, CYB, CNB, CLB = coefficients

    # In DATCOM Figure 5, +Z points up and +X points aft
    CZ = -CN # normal force coefficient from datcom points opposite body-fixed frame
    CX = -CA # axial force coefficient from datcom points opposite body-fixed frame

    CY = CYB*beta
    CMx = CLB*beta
    CMy = CM
    CMz = CNB*beta

    # rot = np.array([[np.cos(alpha), 0, -np.sin(alpha)], [0, 1, 0], [np.sin(alpha), 0, np.cos(alpha)]])
    # rotate
    # return np.zeros(3), np.zeros(3)
    return np.array([CX, CY, CZ]), np.array([CMx, CMy, CMz])
    
def aero_forces_moments(CF, CM, airspeed, params):
    # Calculate the aerodynamic forces and moments based on the provided coefficients and flight conditions
    # CF: Coefficient of Forces, a vector [CFx, CFy, CFz]
    # CM: Coefficient of Moments, a vector [CMx, CMy, CMz]

    rho, S_ref, b_ref, c_ref, r_ref, r_cg = params['density'], params['S_ref'], params['b_ref'], params['c_ref'], params['r_ref'], params['r_cg']
    
    q = .5 * rho * airspeed**2

    F = q * S_ref * CF

    # Calculate moments
    M = q * S_ref * np.array([b_ref * CM[0], c_ref * CM[1], b_ref * CM[2]])

    # Transfer moment from the datum to the center of gravity
    M += np.cross(r_ref - r_cg, F)

    return F, M

def calc_aerodynamics_outputs(t, x, u, params):

    airspeed = u[0]
    alpha = u[1]
    beta = u[2]

    CF, CM = aero_coefficients(0, alpha, beta, [0, 0, 0])

    return aero_forces_moments(CF, CM, airspeed, params)

