"""
 SYNOPSIS

     SnowRisk.py

 DESCRIPTION

     This script performs COF, POF, and Risk calculations for snow operations

 REQUIREMENTS

     Python 3
     arcpy
 """

import arcpy
import logging
import os
import sys
import traceback
import math
from logging.handlers import RotatingFileHandler


def start_rotating_logging(log_file=None, max_bytes=10000, backup_count=1, suppress_requests_messages=True):
    """Creates a logger that outputs to stdout and a log file; outputs start and completion of functions or attribution of functions"""

    formatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    # Paths to desired log file
    script_folder = os.path.dirname(sys.argv[0])
    script_name = os.path.basename(sys.argv[0])
    script_name_no_ext = os.path.splitext(script_name)[0]
    log_folder = os.path.join(script_folder, "Log_Files")
    if not log_file:
        log_file = os.path.join(log_folder, f"{script_name_no_ext}.log")

    # Start logging
    the_logger = logging.getLogger(script_name)
    the_logger.setLevel(logging.DEBUG)

    # Add the rotating file handler
    log_handler = RotatingFileHandler(filename=log_file, maxBytes=max_bytes, backupCount=backup_count)
    log_handler.setLevel(logging.DEBUG)
    log_handler.setFormatter(formatter)
    the_logger.addHandler(log_handler)

    # Add the console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    the_logger.addHandler(console_handler)

    # Suppress SSL warnings in logs if instructed to
    if suppress_requests_messages:
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

    return the_logger


def SnowRisk():

    # Environment
    arcpy.env.overwriteOutput = True

    # Paths
    gdb_folder = r"F:\Shares\FGDB_Services\Data"
    risk_fgdb = os.path.join(gdb_folder, "SnowRisk.gdb")
    snow_risk = os.path.join(risk_fgdb, "SnowRisk")
    snow_risk_layer = "SnowRisk"

    def initialize():
        """Create a feature layer to work with"""

        arcpy.MakeFeatureLayer_management(snow_risk, "SnowRisk")

    def consequence():
        """Calculate individual COF scores based off of various fields in the feature layer

        Fields:
        Bus routes -- Presence of bus routes and what type of route
        Functional classification - The purpose and use of the segment
        Slope - How steep a segment is
        AADT - IDOT calculated annual average daily traffic
        Trouble spot justifications - Uses info surveyed from plow drivers and historical precedence to justify a segment as a trouble spot
        Crashes - Crash totals
        Surface materials - Type of material the segment's surface is such as bituminous
        Sinuosity - How curved or winding the segment is
        """

        # SMTD Bus Routes
        routes = [["SNOW_FID = 'NORTE' or (SMTD_DAY = '0' Or SMTD_NIGHT = '0')", "1"],  # 0 - No SMTD bus routes
                  ["SNOW_FID <> 'NORTE' or (SMTD_DAY = '1' Or SMTD_NIGHT = '1')", "3"],  # 3 - Day and night
                  ["SNOW_FID <> 'NORTE' AND SMTD_DAY = '2'", "4"]]  # 4 - Express SMTD bus routes like exchange/transfer areas
        for route in routes:
            selection = arcpy.SelectLayerByAttribute_management(snow_risk_layer, "NEW_SELECTION", route[0])
            arcpy.CalculateField_management(selection, "COF_SMTD", route[1], "PYTHON3")

        # Functional Classifications
        classifications = [["SNOW_FID = 'NORTE'", "0"],  # 0 - NORTE
                           ["SNOW_FID <> 'NORTE' AND FC = '7'", "1"],  # 1  - Local road or street
                           ["SNOW_FID <> 'NORTE' AND FC = '6'", "2"],  # 2 - Minor collector
                           ["SNOW_FID <> 'NORTE' AND FC = '5'", "3"],  # 3 - Major collector
                           ["SNOW_FID <> 'NORTE' AND (FC = '4' or FC='3')", "4"]]  # 4 - Arterials
        for classification in classifications:
            selection = arcpy.SelectLayerByAttribute_management(snow_risk_layer, "NEW_SELECTION", classification[0])
            arcpy.CalculateField_management(selection, "COF_FC", classification[1], "PYTHON3")

        # Slopes
        slopes = [["SNOW_FID = 'NORTE'", "0"],  # 0 - NORTE
                  ["SNOW_FID <> 'NORTE' AND SNOW_SLOPE <= 1.999", "1"],  # 1 - 0-2%
                  ["SNOW_FID <> 'NORTE' AND (SNOW_SLOPE >= 2 AND SNOW_SLOPE <= 2.999)", "2"],  # 2 - 2-3%
                  ["SNOW_FID <> 'NORTE' AND (SNOW_SLOPE >= 3 AND SNOW_SLOPE <= 3.999)", "3"],  # 3 - 3-4%
                  ["SNOW_FID <> 'NORTE' AND SNOW_SLOPE >= 4", "4"]]  # 4 - 4%+
        for slope in slopes:
            selection = arcpy.SelectLayerByAttribute_management(snow_risk_layer, "NEW_SELECTION", slope[0])
            arcpy.CalculateField_management(selection, "COF_SLOPE", slope[1], "PYTHON3")

        # Traffic Annual Averages (AADT)
        averages = [["SNOW_FID = 'NORTE'", "0"],  # 0 - NORTE
                    ["SNOW_FID <> 'NORTE' AND (AADT >= 0 AND AADT <= 750)", "1"],  # 1 - Less than 750
                    ["SNOW_FID <> 'NORTE' AND (AADT >= 751 AND AADT <= 1400)", "2"],  # 2 - 750 - 1400
                    ["SNOW_FID <> 'NORTE' AND (AADT >= 1401 AND AADT <= 3100)", "3"],  # 3 - > 1400 � 3100
                    ["SNOW_FID <> 'NORTE' AND AADT > 3100", "4"]]  # 4 - 3100+
        for average in averages:
            selection = arcpy.SelectLayerByAttribute_management(snow_risk_layer, "NEW_SELECTION", average[0])
            arcpy.CalculateField_management(selection, "COF_AADT", average[1], "PYTHON3")

        # Trouble Spot Justification
        troubles = [["SNOW_FID = 'NORTE'", "0"],  # 0 - NORTE
                    ["SNOW_FID <> 'NORTE' AND SNOW_TRBL IN ('12')", "1"],  # 1 - 12
                    ["SNOW_FID <> 'NORTE' AND SNOW_TRBL IN ('10', '11')", "2"],  # 2 - 10,11
                    ["SNOW_FID <> 'NORTE' AND SNOW_TRBL IN ('07', '13')", "3"],  # 3 - 7,13
                    ["SNOW_FID <> 'NORTE' AND SNOW_TRBL IN ('01', '02', '03', '04', '06')", "4"]]  # 4 - 1,2,3,4,6
        for trouble in troubles:
            selection = arcpy.SelectLayerByAttribute_management(snow_risk_layer, "NEW_SELECTION", trouble[0])
            arcpy.CalculateField_management(selection, "COF_TRBL", trouble[1], "PYTHON3")

        crashes = [["SNOW_FID = 'NORTE'", "0"],  # 0 - NORTE
                   ["SNOW_FID <> 'NORTE' AND SNOW_CRASH = 1", "1"],  # 1 - 1 crash
                   ["SNOW_FID <> 'NORTE' AND SNOW_CRASH = 2", "2"],  # 2 - 2 crashes
                   ["SNOW_FID <> 'NORTE' AND SNOW_CRASH = 3", "3"],  # 3 - 3 crashes
                   ["SNOW_FID <> 'NORTE' AND SNOW_CRASH = 4", "4"]]  # 4 - 3+ crashes
        for crash in crashes:
            selection = arcpy.SelectLayerByAttribute_management(snow_risk_layer, "NEW_SELECTION", crash[0])
            arcpy.CalculateField_management(selection, "COF_CRASH", crash[1], "PYTHON3")

        materials = [["SNOW_FID = 'NORTE'", "0"],  # 0 - NORTE
                     ["SNOW_FID <> 'NORTE' AND SURF_TYP IN ('501', '510', '520', '525', '530', '540', '550', '560', '600', '610', '615', '620', '625', '630', '640', '650')", "1"],  # 1 - Asphalt
                     ["SNOW_FID <> 'NORTE' AND (SURF_TYP = '300' OR SURF_TYP = '500')", "2"],  # 2 - Bituminous Surface Treatment (Oil & Chip)
                     ["SNOW_FID <> 'NORTE' AND SURF_TYP LIKE '7%'", "3"],  # 3 - Concrete
                     ["SNOW_FID <> 'NORTE' AND SURF_TYP LIKE '8%'", "4"]]  # 4 - Brick
        for material in materials:
            selection = arcpy.SelectLayerByAttribute_management(snow_risk_layer, "NEW_SELECTION", material[0])
            arcpy.CalculateField_management(selection, "COF_SURF", material[1], "PYTHON3")

        # Sinuosity distance formula expressions; loop distance splits closed loops into 2 segments equal to 50% of the shape length and separately calculates the linear distance
        loop_distance = "!Shape.length!/(math.sqrt((!Shape.firstpoint.X!-!Shape!.positionAlongLine(0.5, True).firstpoint.X)**2+(!Shape.firstpoint.Y!-!Shape!.positionAlongLine(0.5, True).firstpoint.Y)**2) + " \
                        "math.sqrt((!Shape!.positionAlongLine(0.5, True).firstpoint.X-!Shape.lastpoint.X!)**2+(!Shape!.positionAlongLine(0.5, True).firstpoint.Y-!Shape.lastpoint.Y!)**2))"

        # Calculate sinuosity (curve length/linear length) then weight it based on speed limit
        selection_sinuosity = arcpy.SelectLayerByAttribute_management(snow_risk_layer, "NEW_SELECTION", "Shape_Length > 0")
        arcpy.CalculateField_management(selection_sinuosity, "SINUOSITY", loop_distance, "PYTHON3")

        # Calculate sinuosity if it is a loop
        selection_nulls = arcpy.SelectLayerByAttribute_management(snow_risk_layer, "NEW_SELECTION", "SINUOSITY IS NULL And Shape_Length > 0")
        arcpy.CalculateField_management(selection_nulls, "SINUOSITY", "30", "PYTHON3")

        # Sinuosity
        curves = [["SINUOSITY <= 1.02 AND SINUOSITY > .98", "1"],  # Sinuosity < 1 does not exist by definition but converting float-->double makes 1 values equal .999
                  ["SINUOSITY <= 1.05 AND SINUOSITY > 1.02", "2"],
                  ["SINUOSITY <= 1.1 AND SINUOSITY > 1.05", "3"],
                  ["SINUOSITY <= 30 AND SINUOSITY > 1.1", "4"]]
        for curve in curves:
            selection = arcpy.SelectLayerByAttribute_management(snow_risk_layer, "NEW_SELECTION", curve[0])
            arcpy.CalculateField_management(selection, "COF_SINE", curve[1], "PYTHON3")
        arcpy.SelectLayerByAttribute_management(snow_risk_layer, "CLEAR_SELECTION")

        # Calculate Total COF Score using the risk assessment process

        # Calculate the two weighed sections of COF
        economic_factor = "!COF_FC!+!COF_SLOPE!+!COF_AADT!+!COF_TRBL!+!COF_CRASH!"
        social_factor = "!COF_SMTD!+!COF_FC!+!COF_SLOPE!+!COF_AADT!+!COF_TRBL!+!COF_CRASH!+!COF_SURF!+!COF_SINE!"
        economic_factor_total = 24
        social_factor_total = 32
        economic_factor_weight = .75
        social_factor_weight = .25

        # Calculate final COF
        cof = f"(((({economic_factor})/{economic_factor_total})*{economic_factor_weight}) + ((({social_factor})/{social_factor_total})*{social_factor_weight}))*4"
        selection = arcpy.SelectLayerByAttribute_management(snow_risk_layer, "NEW_SELECTION", "SNOW_FID <> 'NORTE'")
        arcpy.CalculateField_management(selection, "COF", f"(round({cof}*4))/4", "PYTHON3")

    def probability():
        """Calculate POF scores using fields in the feature layer; uses static travel time calculation layers

        Fields:
        Salt - Distance from salt facilities
        Fleet - Distance from fleet maintenance facilities
        Lanes - Total number of lanes (lanes and special lanes)

        """
        # Salt distances layers
        salt_5 = os.path.join(risk_fgdb, "Salt_5")
        salt_10 = os.path.join(risk_fgdb, "Salt_10")
        salt_15 = os.path.join(risk_fgdb, "Salt_15")
        salt_20 = os.path.join(risk_fgdb, "Salt_20")

        # Fleet distances layers
        fleet_5 = os.path.join(risk_fgdb, "Fleet_5")
        fleet_10 = os.path.join(risk_fgdb, "Fleet_10")
        fleet_15 = os.path.join(risk_fgdb, "Fleet_15")
        fleet_20 = os.path.join(risk_fgdb, "Fleet_20")

        # Calculate total number of lanes
        arcpy.CalculateField_management(snow_risk_layer, "LN_TOTAL", "!LNS!+!LN_SPC_NBR!", "PYTHON3")

        # Distance to salt domes
        salts = [[salt_5, "1"],  # 1 - 5 minutes or less
                 [salt_10, "2"],  # 2 - 10 minutes or less
                 [salt_15, "3"],  # 3 - 15 minutes or less
                 [salt_20, "4"]]  # 4 - 20 minutes or less
        for salt in salts:
            selection = arcpy.SelectLayerByLocation_management(snow_risk_layer, "HAVE_THEIR_CENTER_IN", salt[0], None, "NEW_SELECTION")
            subset_selection = arcpy.SelectLayerByAttribute_management(selection, "SUBSET_SELECTION", "SNOW_FID <> 'NORTE'")
            arcpy.CalculateField_management(subset_selection, "POF_SALT", salt[1], "PYTHON3")

        # Distance to fleet garage
        fleets = [[fleet_5, "1"],  # 1 - 5 minutes or less
                  [fleet_10, "2"],  # 2 - 10 minutes or less
                  [fleet_15, "3"],  # 3 - 15 minutes or less
                  [fleet_20, "4"]]  # 4 - 20 minutes or less
        for fleet in fleets:
            selection = arcpy.SelectLayerByLocation_management(snow_risk_layer, "HAVE_THEIR_CENTER_IN", fleet[0], None, "NEW_SELECTION")
            subset_selection = arcpy.SelectLayerByAttribute_management(selection, "SUBSET_SELECTION", "SNOW_FID <> 'NORTE'")
            arcpy.CalculateField_management(subset_selection, "POF_FLEET", fleet[1], "PYTHON3")

        # Total number of lanes
        lanes = [["LN_TOTAL = 1", "1"],
                 ["LN_TOTAL = 2", "2"],
                 ["LN_TOTAL = 3", "3"],
                 ["LN_TOTAL >= 4", "4"]]
        for total in lanes:
            selection = arcpy.SelectLayerByAttribute_management(snow_risk_layer, "NEW_SELECTION", total[0])
            arcpy.CalculateField_management(selection, "POF_LANES", total[1], "PYTHON3")

        arcpy.SelectLayerByAttribute_management(snow_risk_layer, "CLEAR_SELECTION")

        # Calculate the two weighed section using the risk assessment process
        fleet_factor = "!POF_SALT!+!POF_FLEET!"
        lanes_factor = "!POF_LANES!"
        fleet_factor_total = 8
        lanes_factor_total = 4
        fleet_factor_weight = .50
        lanes_factor_weight = .50

        # Calculate final POF and risk score
        pof = f"(((({fleet_factor})/{fleet_factor_total})*{fleet_factor_weight}) + ((({lanes_factor})/{lanes_factor_total})*{lanes_factor_weight}))*4"
        arcpy.CalculateField_management(snow_risk_layer, "POF", f"(round({pof}*4)/4)", "PYTHON3")
        arcpy.CalculateField_management(snow_risk_layer, "RISK", "!COF!*!POF!", "PYTHON3")

    # Log file paths
    script_folder = os.path.dirname(sys.argv[0])
    script_name_no_ext = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    log_folder = os.path.join(script_folder, "Log_Files")
    log_file = os.path.join(log_folder, f"{script_name_no_ext}.log")
    logger = start_rotating_logging(log_file, 10000, 1, True)

    # Run the above functions with logger error catching and formatting
    try:

        logger.info("")
        logger.info("--- Script Execution Started ---")

        logger.info("--- --- --- --- Initializing Start")
        initialize()
        logger.info("--- --- --- --- Initializing Complete")

        logger.info("--- --- --- --- Consequence of Failure Start")
        consequence()
        logger.info("--- --- --- --- Consequence of Failure Complete")

        logger.info("--- --- --- --- Probability of Failure Start")
        probability()
        logger.info("--- --- --- --- Probability of Failure Complete")

    except ValueError as e:
        exc_traceback = sys.exc_info()[2]
        error_text = f'Line: {exc_traceback.tb_lineno} --- {e}'
        try:
            logger.error(error_text)
        except NameError:
            print(error_text)

    except (IOError, KeyError, NameError, IndexError, TypeError, UnboundLocalError):
        tbinfo = traceback.format_exc()
        try:
            logger.error(tbinfo)
        except NameError:
            print(tbinfo)

    finally:
        try:
            logger.info("--- Script Execution Completed ---")
            logging.shutdown()
        except NameError:
            pass


def main():
    SnowRisk()


if __name__ == '__main__':
    main()
