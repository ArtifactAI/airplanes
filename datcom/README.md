# USAF Digital DATCOM

The USAF Digital DATCOM is a tool for calculating the aerodynamic characteristics of an aircraft. This project generates Datcom input files from a JSON configuration file. It is a part of the Airplane Design Library for Artifact.

## Current State
The library currently supports aircraft configurations with the following characteristics:

- Single wing
- Horizontal tail alone, or horizontal and vertical tails
- NACA 4-series airfoil sections
- Fuselage with circular and elliptical cross-sections
- Combinations of the the above
- Wing flaps and ailerons
- Elevator on horizontal tail
- All control surfaces are of 'plain' type

## Usage
The file `generate_input.py` is a script that generates the input file for the datcom executable from the aircraft configuration JSON. `parse_output.py` is a script that parses the output file into Pandas dataframes. `aero_model.py` contains the functions for calculating the aerodynamic coefficients, and `aero_plots.py` contains the functions for plotting the data.


## Future Configurations
Datcom supports a much wider variety of configurations, which will be added to this library. We plan to expand support for the following configurations:

- [ ] Additional airfoil section characteristics
- [ ] All-moving horizontal tail
- [ ] Canard
- [ ] Twin vertical tail (though Datcom does not support V-tails)
- [ ] Supersonic and low aspect-ratio wings
- [ ] More complex fuselage cross-sections
- [ ] Propeller and jet effects
- [ ] Additional high-lift and control devices (e.g., slats, complex flap systems)
- [ ] Better integration with [ESP model](../esp) for calculation of exposed semispan (SSPNE)
- [ ] Probably more...

## Use Cases
1. **Preliminary Aircraft Design**: Quickly generate aerodynamic data for conceptual aircraft designs.
2. **Design Iteration**: Easily modify aircraft parameters and analyze the resulting changes in aerodynamic characteristics.
3. **Educational Tool**: Serve as a learning platform for students and enthusiasts to understand aircraft design principles and aerodynamics.
4. **Control Design and Simulation**: Generate the necessary aerodynamic data for control system design, physics simulation, and software-in-the-loop testing.

## Output Parsing Assumptions
The output parser assumes that the datcom input file is built up such that the final case has all lifting surfaces (any or all of wing, horizontal tail, vertical tail, and vertical fin). Prior configurations are thrown out. Control surfaces can be added to the datcom input file in any order for accurate output parsing, though the order is enforced in the input file buildup function.

Currently angles and derivatives are in degrees or 1/degrees. Consider changing everything to radians.

## Upcoming Features
- Unit testing
- Improved documentation and user guides
- More thorough error handling and input validation
- Support for additional aircraft components and configurations
- Integration with other aerodynamic analysis tools

We welcome contributions and feedback from the community to help improve and expand the capabilities of this library.

