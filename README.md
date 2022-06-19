# Cocktail Creator
The goal of this project is to implement a Case-Based Reasoning (CBR) system for a cocktail recipe creator. 
A CBR system operates on the main assumption that similar problems have similar solutions and that a solution that 
worked in the past is likely to work again in the future. Moreover, it can adapt one or more solutions in order to meet 
the requirements of its current problem.

Authors: Edison Bejarano, Grecia Reyes, Santiago del Rey and Yazmina Zurita.

## Contents
This project contains the necessary folders and files to run the application Cocktail Creator.

The project is structured as follows:

    - documentation         [The folder contains a PDF report with the details about the CBR system and a User Manual PDF]
    - data                  [The folder contains the original dataset used in the project in CSV format, a processed version of the dataset, the case base in XML format, and the case library in XML format]
    - src                   [The folder contains the implementation of the CBR system, the GUI and the CLI tool, and some scripts to perform one time tasks like automatic testing and data preprocessing]
    - tests                 [The folder contains the unit tests for the Case Library]
    - COPYING               [The license of the project]
    - definitions.py        [The file contains some global definitions for the CBR system]
    - pyproject.toml        [The file contains information about the project like the authors and the project dependencies]
    - README.txt            [A README explaining the contents of the project]
    - requirements.txt      [The file contains the project dependencies to be installed]
    

## How to run the Cocktail CBR

### Prerequisites
You need to create a Python environment and install the required dependencies listed in the `requirements.txt` file 
with the following commands:

```python
python -m venv .venv
python -m pip install -r requirements.txt
```

Alternatively, you can create the environment and install the dependencies by using the `pyproject.toml` file and 
[Poetry](https://python-poetry.org/ "Poetry - Python dependency management and packaging made easy") dependency manager.

Poetry installation:
```python
poetry install
```
### Running the system
To run the system using the GUI you can run:
```python
python src/app/app.py
```
To run the system using the CLI you can run:
```python
python src/app/cbr_cli.py
```

The scripts found in the `src` folder can be run in the same fashion.
