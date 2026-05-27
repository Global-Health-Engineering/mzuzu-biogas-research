[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20407897.svg)](https://doi.org/10.5281/zenodo.20407897)

# Solar Sludge Pasteurization Control System

This repository contains the engineering files, firmware, and analysis scripts for a solar-powered sludge pasteurization system deployed in Mzuzu, Malawi. The system automates the thermal treatment of anaerobic digester effluent to ensure safe, pathogen-free discharge.

## Electronics Design
Hardware design files developed in KiCad.
- solar_pasteurization_controller: The main PCB project including schematics (mcu, power, solar_charger, actuators), PCB layout, and 3D models.
- simulations: SPICE simulations for the power switching circuitry.

## Microcontroller Software
Primary system firmware built using Zephyr RTOS.
- nucleo_l432kc_program_ert_algo: The production firmware implementing the retention time estimation algorithm. Needs to be tested.
- LoRa_TX / LoRa_RX: Simple LoRa scripts for testing. LoRa RX runs on the STM32L432KC eval-board that is connected to the research hut laptop.
- nucleo_l432kc_program_no_rtc: The production firmware implementing the threshold-based control logic.

## Arduino Software
Software that runs on the 2 Arduinos inside the Mzuzu research hut.
- luca_electronics: The software that runs on the microcontroller that's part of Luca Jakobs' biogas pasteurizer system.
- shared_plumbing_electronics: This pertains to the infrastructure electronics.

## Measurements
Data processing and experimental analysis scripts (Python).
- Heat Exchanger Efficiency: Scripts to calculate the h values and thermal efficiency from raw .csv data.
- espinosa_d_values: Logarithmic fit scripts for pathogen inactivation kinetics with data points taken from Deniz Cinar's paper.
- solcast_data_analysis: Analysis of solar irradiance data for the Mzuzu region.
- data_analysis_scripts: Contains the Python scripts for analyzing the .csv data files that can be found in the mzuzu-biogas-research git repo. That repo contains up-to-date data from the research site. 

## PC Software
High-level data handling and parsing for the research hut PC.
- nucleo_parser: Parses the USB packets sent by the LoRa RX microcontroller.
- edb_parser: Parses the USB packets sent by the infrastructure microcontroller. This is called *edb_parser* because it evolved from a simple automation of the EDB (effluent distribution) box.
- lj_parser: Parses the USB packets sent by the biogas pasteurization system microcontroller

For questions, please contact me through:
rcppolat@gmail.com
