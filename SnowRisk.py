"""
 SYNOPSIS

     SnowRisk.py

 DESCRIPTION

     This script performs COF calculation for roads for snow operations

 REQUIREMENTS

     Python 3
     arcpy
 """

import arcpy
import logging
import os
import sys
import traceback
from logging.handlers import RotatingFileHandler


def start_rotating_logging(log_path=None,
                           max_bytes=100000,
                           backup_count=2,
                           suppress_requests_messages=True):
    """
    This function starts logging with a rotating file handler.  If no log
    path is provided it will start logging in the same folder as the script,
    with the same name as the script.
    Parameters
    ----------
    log_path : str
        the path to use in creating the log file
    max_bytes : int
        the maximum number of bytes to use in each log file
    backup_count : int
        the number of backup files to create
    suppress_requests_messages : bool
        If True, then SSL warnings from the requests and urllib3
        modules will be suppressed
    Returns
    -------
    the_logger : logging.logger
        the logger object, ready to use
    """
    formatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s",
                                  datefmt="%Y-%m-%d %H:%M:%S")

    # If no log path was provided, construct one
    script_path = sys.argv[0]
    script_folder = os.path.dirname(script_path)
    script_name = os.path.splitext(os.path.basename(script_path))[0]
    if not log_path:
        log_path = os.path.join(script_folder, "{}.log".format(script_name))

    # Start logging
    the_logger = logging.getLogger(script_name)
    the_logger.setLevel(logging.DEBUG)

    # Add the rotating file handler
    log_handler = RotatingFileHandler(filename=log_path,
                                      maxBytes=max_bytes,
                                      backupCount=backup_count)
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


def is_valid_path(parser, path):
    """
    Check to see if a provided path is valid.  Works with argparse
    Parameters
    ----------
    parser : argparse.ArgumentParser
        The argument parser object
    path : str
        The path to evaluate whether it exists or not
    Returns
    ----------
    path : str
        If the path exists, it is returned  if not, a
        parser.error is raised.
    """
    if not os.path.exists(path):
        parser.error("The path {0} does not exist!".format(path))
    else:
        return path


def SnowRisk():
    # Environment
    arcpy.env.overwriteOutput = True
    arcpy.parallelProcessingFactor = "7"
    arcpy.SetLogHistory(False)

    # Paths
    fgdb_folder = r"Z:\Data"
    imspfld_sde = os.path.join(fgdb_folder, r"RoadwayInfo.gdb")
    roadway_information = os.path.join(imspfld_sde, r"FacilitiesStreets\RoadwayInformation")

    # GDB Paths
    script_folder = os.path.dirname(sys.argv[0])
    temp_fgdb = os.path.join(script_folder, "temp.gdb")  # temp fgdb
    snow_risk_temp = os.path.join(temp_fgdb, "SnowRisk_temp")  # Temp output in temp GDB
    snow_risk_mem = r"memory\roadway_information_mem"  # Memory output in temp GDB
    snow_risk = os.path.join(temp_fgdb, "SnowRisk")  # Final output in temp GDBs

    # Check to see if SnowCOF exists. If not, create it using SDE data. If so, append SDE data to the table
    if not arcpy.Exists(snow_risk):
        arcpy.FeatureClassToFeatureClass_conversion(roadway_information, temp_fgdb, "SnowRisk", '',
                                                    r'ROAD_NAME "Street Name" true true false 75 Text 0 0,First,#,RoadwayInformation,ROAD_NAME,0,75;'
                                                    r'FC "Functional Classification" true true false 1 Text 0 0,First,#,RoadwayInformation,FC,0,1;'
                                                    r'AADT "Annual Average Daily Traffic" true true false 8 Double 0 0,First,#,RoadwayInformation,AADT,-1,-1;'
                                                    r'AADT_YR "AADT Year" true true false 4 Text 0 0,First,#,RoadwayInformation,AADT_YR,0,4;'
                                                    r'SURF_TYP "Original Surface Type" true true false 50 Text 0 0,First,#,RoadwayInformation,SURF_TYP,0,50;'
                                                    r'SNOW_FID "Snow Route Identifier" true true false 7 Text 0 0,First,#,RoadwayInformation,SNOW_FID,0,7;'
                                                    r'SNOW_DIST "Snow District" true true false 3 Text 0 0,First,#,RoadwayInformation,SNOW_DIST,0,3;'
                                                    r'SNOW_TYPE "Snow Type (Priority)" true true false 1 Text 0 0,First,#,RoadwayInformation,SNOW_TYPE,0,1;'
                                                    r'SNOW__RT_NBR "Snow Route Number" true true false 10 Text 0 0,First,#,RoadwayInformation,SNOW__RT_NBR,0,10;'
                                                    r'SNOW_TRBL "Snow Trouble Spot Justification" true true false 2 Text 0 0,First,#,RoadwayInformation,SNOW_TRBL,0,2;'
                                                    r'SNOW_SLOPE "Calculated Profile Grade" true true false 8 Double 0 0,First,#,RoadwayInformation,SNOW_SLOPE,-1,-1;'
                                                    r'SNOW_TIME "Calculated Plow-time ( E-E based on Lane Miles)" true true false 8 Double 0 0,First,#,RoadwayInformation,SNOW_TIME,-1,-1;'
                                                    r'SMTD_DAY "SMTD Day Service" true true false 1 Text 0 0,First,#,RoadwayInformation,SMTD_DAY,0,1;'
                                                    r'SMTD_NIGHT "SMTD Night Service" true true false 1 Text 0 0,First,#,RoadwayInformation,SMTD_NIGHT,0,1;'
                                                    r'SMTD_SUPPL "SMTD Supplemental Service" true true false 1 Text 0 0,First,#,RoadwayInformation,SMTD_SUPPL,0,1;'
                                                    r'NUMB1 "Number 1" true true false 8 Double 0 0,First,#,RoadwayInformation,NUMB1,-1,-1;'
                                                    r'COF_SMTD "COF Score for SMTD Bus Routes" true true false 2 Short 0 0,First,#;'
                                                    r'COF_FC "COF Score for Functional Classification" true true false 2 Short 0 0,First,#;'
                                                    r'COF_SLOPE "COF Score for Slope" true true false 2 Short 0 0,First,#;'
                                                    r'COF_AADT "COF Score for AADT" true true false 2 Short 0 0,First,#;'
                                                    r'COF "Total COF Score" true true false 2 Short 0 0,First,#;'
                                                    r'COF_TRBL "COF Score for Trouble Spot Justifications" true true false 2 Short 0 0,First,#;'
                                                    r'COF_CRASH "COF Score for Crash Totals" true true false 2 Short 0 0,First,#;'
                                                    r'COF_SURF "COF Score for Surface Types (and not surfing)" true true false 4 Long 0 0,First,#;'
                                                    r'COF_AVG "Average COF Score" true true false 8 Double 0 0,First,#;'
                                                    r'POF_SALT "POF Score for Time to Salt Dome" true true false 2 Short 0 0,First,#;'
                                                    r'POF_FLEET "POF Score for Time to Fleet Facility" true true false 2 Short 0 0,First,#;'
                                                    r'LNS "Through Lane Count" true true false 8 Double 0 0,First,#,RoadwayInformation,LNS,-1,-1;'
                                                    r'LN_SPC_NBR "Special Lane Count" true true false 8 Double 0 0,First,#,RoadwayInformation,LN_SPC_NBR,-1,-1;'
                                                    r'LN_TOTAL "Total Lane Count" true true false 8 Double 0 0,First,#;'
                                                    r'POF_LANES "POF Score for Lane Count" true true false 8 Double 0 0,First,#', '')
        # Add fields to the new table
        arcpy.AddFields_management(snow_risk,
                                   [["COF_TRBL", "SHORT", None, "COF Score for Trouble Spot Justifications"],
                                    ["COF_CRASH", "SHORT", None, "COF Score for Crash Totals"],
                                    ["COF_SURF", "SHORT", None, "COF Score for Surface Types (and not surfing)"],
                                    ["COF_AVG", "DOUBLE", None, "Average COF Score"]])
    else:
        arcpy.DeleteRows_management(snow_risk)
        arcpy.Append_management(roadway_information, snow_risk, "NO_TEST",
                                r'ROAD_NAME "Street Name" true true false 75 Text 0 0,First,#,RoadwayInformation,ROAD_NAME,0,75;'
                                r'FC "Functional Classification" true true false 1 Text 0 0,First,#,RoadwayInformation,FC,0,1;'
                                r'AADT "Annual Average Daily Traffic" true true false 8 Double 0 0,First,#,RoadwayInformation,AADT,-1,-1;'
                                r'AADT_YR "AADT Year" true true false 4 Text 0 0,First,#,RoadwayInformation,AADT_YR,0,4;'
                                r'SURF_TYP "Original Surface Type" true true false 50 Text 0 0,First,#,RoadwayInformation,SURF_TYP,0,50;'
                                r'SNOW_FID "Snow Route Identifier" true true false 7 Text 0 0,First,#,RoadwayInformation,SNOW_FID,0,7;'
                                r'SNOW_DIST "Snow District" true true false 3 Text 0 0,First,#,RoadwayInformation,SNOW_DIST,0,3;'
                                r'SNOW_TYPE "Snow Type (Priority)" true true false 1 Text 0 0,First,#,RoadwayInformation,SNOW_TYPE,0,1;'
                                r'SNOW__RT_NBR "Snow Route Number" true true false 10 Text 0 0,First,#,RoadwayInformation,SNOW__RT_NBR,0,10;'
                                r'SNOW_TRBL "Snow Trouble Spot Justification" true true false 2 Text 0 0,First,#,RoadwayInformation,SNOW_TRBL,0,2;'
                                r'SNOW_SLOPE "Calculated Profile Grade" true true false 8 Double 0 0,First,#,RoadwayInformation,SNOW_SLOPE,-1,-1;'
                                r'SNOW_TIME "Calculated Plow-time ( E-E based on Lane Miles)" true true false 8 Double 0 0,First,#,RoadwayInformation,SNOW_TIME,-1,-1;'
                                r'SMTD_DAY "SMTD Day Service" true true false 1 Text 0 0,First,#,RoadwayInformation,SMTD_DAY,0,1;'
                                r'SMTD_NIGHT "SMTD Night Service" true true false 1 Text 0 0,First,#,RoadwayInformation,SMTD_NIGHT,0,1;'
                                r'SMTD_SUPPL "SMTD Supplemental Service" true true false 1 Text 0 0,First,#,RoadwayInformation,SMTD_SUPPL,0,1;'
                                r'NUMB1 "Number 1" true true false 8 Double 0 0,First,#,RoadwayInformation,NUMB1,-1,-1;'
                                r'COF_SMTD "COF Score for SMTD Bus Routes" true true false 2 Short 0 0,First,#;'
                                r'COF_FC "COF Score for Functional Classification" true true false 2 Short 0 0,First,#;'
                                r'COF_SLOPE "COF Score for Slope" true true false 2 Short 0 0,First,#;'
                                r'COF_AADT "COF Score for AADT" true true false 2 Short 0 0,First,#;'
                                r'COF "Total COF Score" true true false 2 Short 0 0,First,#;'
                                r'COF_TRBL "COF Score for Trouble Spot Justifications" true true false 2 Short 0 0,First,#;'
                                r'COF_CRASH "COF Score for Crash Totals" true true false 2 Short 0 0,First,#;'
                                r'COF_SURF "COF Score for Surface Types (and not surfing)" true true false 4 Long 0 0,First,#;'
                                r'COF_AVG "Average COF Score" true true false 8 Double 0 0,First,#;'
                                r'POF_SALT "POF Score for Time to Salt Dome" true true false 2 Short 0 0,First,#;'
                                r'POF_FLEET "POF Score for Time to Fleet Facility" true true false 2 Short 0 0,First,#;'
                                r'LNS "Through Lane Count" true true false 8 Double 0 0,First,#,RoadwayInformation,LNS,-1,-1;'
                                r'LN_SPC_NBR "Special Lane Count" true true false 8 Double 0 0,First,#,RoadwayInformation,LN_SPC_NBR,-1,-1;'
                                r'LN_TOTAL "Total Lane Count" true true false 8 Double 0 0,First,#;'
                                r'POF_LANES "POF Score for Lane Count" true true false 8 Double 0 0,First,#', '', '')

    # Create a temporary SnowCOF layer to work with, prevents the error of using the same data source for future appends
    if not arcpy.Exists(snow_risk_temp):
        arcpy.FeatureClassToFeatureClass_conversion(snow_risk, temp_fgdb, "SnowRisk_temp")
    else:
        arcpy.DeleteRows_management(snow_risk_temp)
        arcpy.Append_management(snow_risk, snow_risk_temp)

    # Create a feature layer in memory to work with
    arcpy.MakeFeatureLayer_management(snow_risk_temp, snow_risk_mem)

    # Calculate individual COF scores based off of fields in the feature layer
    # Bus routes, functional classifications, slopes, AADT, trouble spot justifications, crashes, surface materials

    # SMTD Bus Routes
    routes = [["SNOW_FID = 'NORTE' or (SMTD_DAY = '0' And SMTD_NIGHT = '0')", "0"],  # 0 - No SMTD bus routes
              ["SNOW_FID <> 'NORTE' AND ((SMTD_DAY = '0' And SMTD_NIGHT = '1') or (SMTD_DAY = '1' OR SMTD_NIGHT = '0'))", "2"],  # 2 - Day or night SMTD bus routes
              ["SNOW_FID = 'NORTE' or (SMTD_DAY = '1' And SMTD_NIGHT = '1')", "3"],  # 3 - Day and night
              ["SNOW_FID <> 'NORTE' AND SMTD_DAY = '2'", "4"]]  # 4 - Express SMTD bus routes like exchange/transfer areas
    for route in routes:
        selection = arcpy.SelectLayerByAttribute_management(snow_risk_mem, "NEW_SELECTION", route[0])
        arcpy.CalculateField_management(selection, "COF_SMTD", route[1], "PYTHON3")

    # Functional Classifications
    classifications = [["SNOW_FID = 'NORTE'", "0"],  # 0 - NORTE
                       ["SNOW_FID <> 'NORTE' AND FC = '7'", "1"],  # 1  - Local road or street
                       ["SNOW_FID <> 'NORTE' AND FC = '6'", "2"],  # 2 - Minor collector
                       ["SNOW_FID <> 'NORTE' AND FC = '5'", "3"],  # 3 - Major collector
                       ["SNOW_FID <> 'NORTE' AND (FC = '4' or FC='3')", "4"]]  # 4 - Arterials
    for classification in classifications:
        selection = arcpy.SelectLayerByAttribute_management(snow_risk_mem, "NEW_SELECTION", classification[0])
        arcpy.CalculateField_management(selection, "COF_FC", classification[1], "PYTHON3")

    # Slopes
    slopes = [["SNOW_FID = 'NORTE'", "0"],  # 0 - NORTE
              ["SNOW_FID <> 'NORTE' AND SNOW_SLOPE < 1.999", "1"],  # 1 - 0-2%
              ["SNOW_FID <> 'NORTE' AND (SNOW_SLOPE >= 2 AND SNOW_SLOPE <= 2.999)", "2"],  # 2 - 2-3%
              ["SNOW_FID <> 'NORTE' AND (SNOW_SLOPE >= 3 AND SNOW_SLOPE <= 3.999)", "3"],  # 3 - 3-4%
              ["SNOW_FID <> 'NORTE' AND SNOW_SLOPE >= 4", "4"]]  # 4 - 4%+
    for slope in slopes:
        selection = arcpy.SelectLayerByAttribute_management(snow_risk_mem, "NEW_SELECTION", slope[0])
        arcpy.CalculateField_management(selection, "COF_SLOPE", slope[1], "PYTHON3")

    # Traffic Annual Averages (AADT)
    averages = [["SNOW_FID = 'NORTE'", "0"],  # 0 - NORTE
                ["SNOW_FID <> 'NORTE' AND (AADT >= 0 AND AADT <= 750)", "1"],  # 1 - Less than 750
                ["SNOW_FID <> 'NORTE' AND (AADT >= 751 AND AADT <= 1400)", "2"],  # 2 - 750 - 1400
                ["SNOW_FID <> 'NORTE' AND (AADT >= 1401 AND AADT <= 3100)", "3"],  # 3 - > 1400 � 3100
                ["SNOW_FID <> 'NORTE' AND AADT > 3100", "4"]]  # 4 - 3100+
    for average in averages:
        selection = arcpy.SelectLayerByAttribute_management(snow_risk_mem, "NEW_SELECTION", average[0])
        arcpy.CalculateField_management(selection, "COF_AADT", average[1], "PYTHON3")

    # snow_trbl trouble spots
    troubles = [["SNOW_FID = 'NORTE'", "0"],  # 0 - NORTE
                ["SNOW_FID <> 'NORTE' AND SNOW_TRBL IN ('12')", "1"],  # 1 - 12
                ["SNOW_FID <> 'NORTE' AND SNOW_TRBL IN ('10', '11')", "2"],  # 2 - 10,11
                ["SNOW_FID <> 'NORTE' AND SNOW_TRBL IN ('07', '13')", "3"],  # 3 - 7,13
                ["SNOW_FID <> 'NORTE' AND SNOW_TRBL IN ('01', '02', '03', '04', '06')", "4"]]  # 4 - 1,2,3,4,6
    for trouble in troubles:
        selection = arcpy.SelectLayerByAttribute_management(snow_risk_mem, "NEW_SELECTION", trouble[0])
        arcpy.CalculateField_management(selection, "COF_TRBL", trouble[1], "PYTHON3")

    crashes = [["SNOW_FID = 'NORTE'", "0"],  # 0 - NORTE
               ["SNOW_FID <> 'NORTE' AND NUMB1 = 1", "1"],  # 1 - 1 crash
               ["SNOW_FID <> 'NORTE' AND NUMB1 = 2", "2"],  # 2 - 2 crashes
               ["SNOW_FID <> 'NORTE' AND NUMB1 = 3", "3"],  # 3 - 3 crashes
               ["SNOW_FID <> 'NORTE' AND NUMB1 = 4", "4"]]  # 4 - 3+ crashes
    for crash in crashes:
        selection = arcpy.SelectLayerByAttribute_management(snow_risk_mem, "NEW_SELECTION", crash[0])
        arcpy.CalculateField_management(selection, "COF_CRASH", crash[1], "PYTHON3")

    materials = [["SNOW_FID = 'NORTE'", "0"],  # 0 - NORTE
                 ["SNOW_FID <> 'NORTE' AND SURF_TYP IN ('501', '510', '520', '525', '530', '540', '550', '560', '600', '610', '615', '620', '625', '630', '640', '650')", "1"],  # 1 - Asphalt
                 ["SNOW_FID <> 'NORTE' AND (SURF_TYP = '300' OR SURF_TYP = '500')", "2"],  # 2 - Bituminous Surface Treatment (Oil & Chip)
                 ["SNOW_FID <> 'NORTE' AND SURF_TYP LIKE '7%'", "3"],  # 3 - Concrete
                 ["SNOW_FID <> 'NORTE' AND SURF_TYP LIKE '8%'", "4"]]  # 4 - Brick
    for material in materials:
        selection = arcpy.SelectLayerByAttribute_management(snow_risk_mem, "NEW_SELECTION", material[0])
        arcpy.CalculateField_management(selection, "COF_SURF", material[1], "PYTHON3")

    # Clear last selection
    arcpy.SelectLayerByAttribute_management(snow_risk_mem, "CLEAR_SELECTION")

    # Calculate Total COF Score using the previous four calculated fields, then calculate average
    selection = arcpy.SelectLayerByAttribute_management(snow_risk_mem, "NEW_SELECTION", "SNOW_FID <> 'NORTE'")
    arcpy.CalculateField_management(selection, "COF", "!COF_SMTD!+!COF_FC!+(!COF_SLOPE!*!COF_AADT!)+!COF_TRBL!+!COF_CRASH!+!COF_SURF!", "PYTHON3")
    arcpy.CalculateField_management(selection, "COF_AVG", "!COF!/7", "PYTHON3")

    # Calculate individual POF scores based off of fields in the feature layer
    # Total lane miles, drive time from salt domes, drive time from fleet facility

    # Salt distances layers
    salt_5 = os.path.join(temp_fgdb, "Salt_5")
    salt_10 = os.path.join(temp_fgdb, "Salt_10")
    salt_15 = os.path.join(temp_fgdb, "Salt_15")
    salt_20 = os.path.join(temp_fgdb, "Salt_20")

    # Fleet distances layers
    fleet_5 = os.path.join(temp_fgdb, "Fleet_5")
    fleet_10 = os.path.join(temp_fgdb, "Fleet_10")
    fleet_15 = os.path.join(temp_fgdb, "Fleet_15")
    fleet_20 = os.path.join(temp_fgdb, "Fleet_20")

    # Calculate total number of lanes
    arcpy.CalculateField_management(snow_risk_mem, "LN_TOTAL", "!LNS!+!LN_SPC_NBR!", "PYTHON3")

    # Distance to salt domes
    salts = [[salt_5, "1"],  # 1 - 5 minutes or less
             [salt_10, "2"],  # 2 - 10 minutes or less
             [salt_15, "3"],  # 3 - 15 minutes or less
             [salt_20, "4"]]  # 4 - 20 minutes or less
    for salt in salts:
        selection = arcpy.SelectLayerByLocation_management(snow_risk_mem, "HAVE_THEIR_CENTER_IN", salt[0], None, "NEW_SELECTION")
        subset_selection = arcpy.SelectLayerByAttribute_management(selection, "SUBSET_SELECTION", "SNOW_FID <> 'NORTE'")
        arcpy.CalculateField_management(subset_selection, "POF_SALT", salt[1], "PYTHON3")

    # Distance to fleet garage
    fleets = [[fleet_5, "1"],  # 1 - 5 minutes or less
              [fleet_10, "2"],  # 2 - 10 minutes or less
              [fleet_15, "3"],  # 3 - 15 minutes or less
              [fleet_20, "4"]]  # 4 - 20 minutes or less
    for fleet in fleets:
        selection = arcpy.SelectLayerByLocation_management(snow_risk_mem, "HAVE_THEIR_CENTER_IN", fleet[0], None, "NEW_SELECTION")
        subset_selection = arcpy.SelectLayerByAttribute_management(selection, "SUBSET_SELECTION", "SNOW_FID <> 'NORTE'")
        arcpy.CalculateField_management(subset_selection, "POF_FLEET", fleet[1], "PYTHON3")

    lanes = [["LN_TOTAL = 2", "1"],
             ["LN_TOTAL = 3", "2"],
             ["LN_TOTAL = 4", "3"],
             ["LN_TOTAL >= 5", "4"]]
    for total in lanes:
        selection = arcpy.SelectLayerByAttribute_management(snow_risk_mem, "NEW_SELECTION", total[0])
        arcpy.CalculateField_management(selection, "POF_LANES", total[1], "PYTHON3")

    # Delete roads that aren't part of a route (NORTE)
    delete = arcpy.SelectLayerByAttribute_management(snow_risk_mem, "NEW_SELECTION", "SNOW_FID = 'NORTE'")
    arcpy.DeleteFeatures_management(delete)

    # Clear last selection then append new info to SnowCOF
    arcpy.SelectLayerByAttribute_management(snow_risk_mem, "CLEAR_SELECTION")
    arcpy.DeleteRows_management(snow_risk)
    arcpy.Append_management(snow_risk_mem, snow_risk, "NO_TEST")


def main():
    """
    Main execution code
    """
    # Make a few variables to use
    # script_folder = os.path.dirname(sys.argv[0])
    log_file_folder = r"C:\Scripts\SnowRisk\Log_files"
    script_name_no_ext = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    log_file = os.path.join(log_file_folder, "{}.log".format(script_name_no_ext))
    logger = None

    try:

        # Get logging going
        logger = start_rotating_logging(log_path=log_file,
                                        max_bytes=100000,
                                        backup_count=2,
                                        suppress_requests_messages=True)
        logger.info("")
        logger.info("--- Script Execution Started ---")

        SnowRisk()
        logger.info("Completed SnowRisk processing")

    except ValueError as e:
        exc_traceback = sys.exc_info()[2]
        error_text = 'Line: {0} --- {1}'.format(exc_traceback.tb_lineno, e)
        try:
            logger.error(error_text)
        except NameError:
            print(error_text)

    except (IOError, KeyError, NameError, IndexError, TypeError, UnboundLocalError, arcpy.ExecuteError):
        tbinfo = traceback.format_exc()
        try:
            logger.error(tbinfo)
        except NameError:
            print(tbinfo)

    finally:
        # Shut down logging
        try:
            logger.info("--- Script Execution Completed ---")
            logging.shutdown()
        except NameError:
            pass


if __name__ == '__main__':
    main()
