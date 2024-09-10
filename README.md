![Python application](https://github.com/ArtifactAI/airplanes/actions/workflows/python-app.yml/badge.svg)

# Airplane Design Library for Artifact

This library is a collection of airplane design data for [Artifact](https://artifact.engineer) but is self-contained, and aircraft models can be independently compiled. Engineering Sketch Pad ([ESP](https://acdl.mit.edu/ESP/)) 3D models and US Digital Datcom ([DATCOM](https://www.pdas.com/datcom.html)) aerodynamics models can be generated from an aircraft configuration JSON in the `configurations` directory.

## Usage

Set up a virtual environment and install the requirements:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

The `./tests` directory contains unit tests for the ESP and DATCOM modules, which serve as examples of how to use the library. To run the tests:

```bash
python -m unittest discover -s tests
```

## Upcoming Features
- Create a pip package.