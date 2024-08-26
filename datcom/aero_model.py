import numpy as np
from typing import List
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

data = parse_datcom_output('datcom/datcom.out')

s_ref = data['reference_data']['S_ref']['value']
b_ref = data['reference_data']['b_ref']['value']
c_ref = data['reference_data']['c_ref']['value']  

# Moment reference
x_ref = data['reference_data']['x_ref']['value']
z_ref = data['reference_data']['z_ref']['value']
r_ref = [x_ref, 0, z_ref]


rigid_body_static = data['rigid_body_static']
alpha_values = rigid_body_static['ALPHA'].values
dependent_vars = rigid_body_static.iloc[:, 1:].values
rigid_body_static_interpolator = RegularGridInterpolator(
    (alpha_values,), dependent_vars, bounds_error=False, fill_value=None
)

rigid_body_dynamic = data['rigid_body_dynamic']
alpha_values = rigid_body_dynamic['ALPHA'].values
dependent_vars = rigid_body_dynamic.iloc[:, 1:].values
rigid_body_dynamic_interpolator = RegularGridInterpolator(
    (alpha_values,), dependent_vars, bounds_error=False, fill_value=None
)

alpha_range = rigid_body_static['ALPHA'].values.tolist()
control_surfaces = []

# Create interpolator for flaps if present in the data
flap_coef_increments_interpolator = None
flap_induced_drag_interpolator = None
if 'flaps' in data:
    control_surfaces.append('flaps')

    flap_coef_increments = data['flaps']['coef_increments']
    delta_values = flap_coef_increments['DELTA'].values
    dependent_vars = flap_coef_increments.iloc[:, 1:].values
    flap_coef_increments_interpolator = RegularGridInterpolator(
        (delta_values,), dependent_vars, bounds_error=False, fill_value=None
    )

    flap_induced_drag = data['flaps']['induced_drag_increments']
    alpha_values = flap_induced_drag.iloc[:, 0].tolist()
    delta_values = flap_induced_drag.columns.tolist()[1:]
    flap_induced_drag_interpolator = RegularGridInterpolator((alpha_values, delta_values), flap_induced_drag.values[:, 1:])

# Create interpolator for elevator if present in the data
elevator_coef_increments_interpolator = None
elevator_induced_drag_interpolator = None
if 'elevator' in data:
    control_surfaces.append('elevator')

    elevator_coef_increments = data['elevator']['coef_increments']
    delta_values = elevator_coef_increments['DELTA'].values
    dependent_vars = elevator_coef_increments.iloc[:, 1:].values
    elevator_coef_increments_interpolator = RegularGridInterpolator(
        (delta_values,), dependent_vars, bounds_error=False, fill_value=None
    )

    elevator_induced_drag = data['elevator']['induced_drag_increments']
    alpha_values = elevator_induced_drag.iloc[:, 0].tolist()
    delta_values = elevator_induced_drag.columns.tolist()[1:]
    elevator_induced_drag_interpolator = RegularGridInterpolator((alpha_values, delta_values), elevator_induced_drag.values[:, 1:])

# Create interpolator for ailerons if present in the data
aileron_roll_coef_interpolator = None
aileron_yaw_coef_interpolator = None
if 'ailerons' in data:
    control_surfaces.append('ailerons')

    aileron_roll_coef = data['ailerons']['roll_coefficient']
    delta_values = aileron_roll_coef['D_AILERON'].values
    dependent_vars = aileron_roll_coef.iloc[:, 1:].values.flatten()
    aileron_roll_coef_interpolator = RegularGridInterpolator(
        (delta_values,), dependent_vars, bounds_error=False, fill_value=None
    )

    aileron_yaw_coef = data['ailerons']['yaw_coefficient']
    alpha_values = aileron_yaw_coef.iloc[:, 0].tolist()
    delta_values = aileron_yaw_coef.columns.tolist()[1:]
    aileron_yaw_coef_interpolator = RegularGridInterpolator((alpha_values, delta_values), aileron_yaw_coef.values[:, 1:])


def rigid_body_static_coefficients(alpha, beta):

    # TODO: revist angular units in datcom input file generation and output parsing
    alpha = np.degrees(alpha)
    beta = np.degrees(beta)

    # interpolate on alpha  
    CD, CL, CMy, CN, CA, XCP, CLA, CMA, CYB, CNB, CLB = rigid_body_static_interpolator([alpha])[0]

    CY = CYB*beta
    CMx = CLB*beta
    CMz = CNB*beta

    # forces_aero = np.array([CD, CY, CL])
    # CF = R_wind2bod(alpha, beta) @ forces_aero

    CF = np.array([-CA, CY, -CN])
    CM = np.array([CMx, CMy, CMz])

    return CF, CM

def rigid_body_dynamic_coefficients(alpha, p, q, r):

    # TODO: revist angular units in datcom input file generation and output parsing
    alpha = np.degrees(alpha)
    p = np.degrees(p)
    q = np.degrees(q)
    r = np.degrees(r)

    CLQ, CMQ, CLP, CYP, CNP, CNR, CLR = rigid_body_dynamic_interpolator([alpha])[0]

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
        
    if coef_increments is not None:
        D_CL, D_CM, D_CL_max, D_CD_min = coef_increments([deflection])[0]
        D_CDI = induced_drag((alpha, deflection))
        
        CF = R_wind2bod(np.radians(alpha), np.radians(beta)) @ np.array([-D_CDI, 0, -D_CL])
        CM = np.array([0, D_CM, 0])
    else:
        CF = np.zeros(3)
        CM = np.zeros(3)
    
    return CF, CM

def asymmetric_control_surface_coefficients(alpha, deflection):
    alpha = np.degrees(alpha)
    deflection = np.degrees(deflection)

    total_deflection = deflection * 2

    D_CROLL = aileron_roll_coef_interpolator([deflection])[0]
    D_CYAW = aileron_yaw_coef_interpolator([alpha, total_deflection])[0]

    CF = np.array([0,0,0])
    CM = np.array([D_CROLL, 0, D_CYAW])
    
    return CF, CM

def aero_coefficients(alpha, beta=0, surfaces: dict = {}, p=0, q=0, r=0):

    # Coefficients in order CFx, CFy, CFz, CMx, CMy, CMz

    static_CF, static_CM = rigid_body_static_coefficients(alpha, beta)
    dynamic_CF, dynamic_CM = rigid_body_dynamic_coefficients(alpha, p, q, r)

    surfaces_CF = np.zeros(3)
    surfaces_CM = np.zeros(3)

    if 'flaps' in surfaces:
        flaps_CF, flaps_CM = symmetric_control_surface_coefficients('flaps', alpha, beta, surfaces['flaps'])
        surfaces_CF += flaps_CF
        surfaces_CM += flaps_CM
    if 'elevator' in surfaces:
        elevator_CF, elevator_CM = symmetric_control_surface_coefficients('elevator', alpha, beta, surfaces['elevator'])
        surfaces_CF += elevator_CF
        surfaces_CM += elevator_CM
    if 'ailerons' in surfaces:
        # Note that aileron deflection of 20 deg means +20 deg left aileron and -20 deg right aileron
        ailerons_CF, ailerons_CM = asymmetric_control_surface_coefficients(alpha, surfaces['ailerons'])
        surfaces_CF += ailerons_CF
        surfaces_CM += ailerons_CM
    CF = static_CF + dynamic_CF + surfaces_CF
    CM = static_CM + dynamic_CM + surfaces_CM   
    
    return CF, CM