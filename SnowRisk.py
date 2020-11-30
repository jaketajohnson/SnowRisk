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


def ScriptLogging():
    """Enables console and log file logging; see test script for comments on functionality"""
    current_directory = os.getcwd()
    script_filename = os.path.basename(sys.argv[0])
    log_filename = os.path.splitext(script_filename)[0]
    log_file = os.path.join(current_directory, f"{log_filename}.log")
    if not os.path.exists(log_file):
        with open(log_file, "w"):
            pass
    message_formatting = "%(asctime)s - %(levelname)s - %(message)s"
    date_formatting = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=message_formatting, datefmt=date_formatting)
    logging_output = logging.getLogger(f"{log_filename}")
    logging_output.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logging_output.addHandler(console_handler)
    logging.basicConfig(format=message_formatting, datefmt=date_formatting, filename=log_file, filemode="w", level=logging.INFO)
    return logging_output


def SnowRisk():

    # Logging
    def logging_lines(name):
        """Use this wrapper to insert a message before and after the function for logging purposes"""
        if type(name) == str:
            def logging_decorator(function):
                def logging_wrapper():
                    logger.info(f"{name} Start")
                    function()
                    logger.info(f"{name} Complete")
                return logging_wrapper
            return logging_decorator
    logger = ScriptLogging()
    logger.info("Script Execution Start")

    # Environment
    arcpy.env.overwriteOutput = True

    # Paths
    fgdb_services = r"F:\Shares\FGDB_Services"
    data = os.path.join(fgdb_services, "Data")
    risk_fgdb = os.path.join(data, "SnowRisk.gdb")
    snow_risk = os.path.join(risk_fgdb, "SnowRisk")
    snow_rank = os.path.join(risk_fgdb, "SnowRank")
    snow_risk_minor = os.path.join(risk_fgdb, "SnowRiskMinor")
    snow_risk_minor_dissolved = os.path.join(risk_fgdb, "SnowRiskMinor_dissolved")
    database_connections = os.path.join(fgdb_services, "DatabaseConnections")
    sde = os.path.join(database_connections, "COSPW@imSPFLD@MCWINTCWDB.sde")
    facilities_streets = os.path.join(sde, "FacilitiesStreets")
    roadway_information = os.path.join(facilities_streets, "RoadwayInformation")
    fleet = os.path.join(risk_fgdb, "Fleet")
    salt = os.path.join(risk_fgdb, "Salt")

    @logging_lines("Initialize")
    def initialize():
        """Create a feature layer to work with"""

        # Copy over roadway information
        arcpy.FeatureClassToFeatureClass_conversion(roadway_information, risk_fgdb, "SnowRisk", "SNOW_DIST IS NOT NULL",
                                                    fr"ROAD_NAME 'ROAD_NAME' true true false 255 Text 0 0,First,#,{roadway_information},ROAD_NAME,0,75;"
                                                    fr"FC 'Functional Classification' true true false 1 Text 0 0,First,#,{roadway_information},FC,0,1;"
                                                    fr"AADT 'Annual Average Daily Traffic' true true false 8 Double 8 38,First,#,{roadway_information},AADT,-1,-1;"
                                                    fr"AADT_YR 'AADT Year' true true false 4 Text 0 0,First,#,{roadway_information},AADT_YR,0,4;"
                                                    fr"LN_MI 'Through Lane Miles' true true false 8 Double 8 38,First,#,{roadway_information},LN_MI,-1,-1;"
                                                    fr"LN_SPC_NBR 'Special Lane Count' true true false 8 Double 8 38,First,#,{roadway_information},LN_SPC_NBR,-1,-1;"
                                                    fr"LN_TOTALMI 'Total Lane Miles' true true false 8 Double 8 38,First,#,{roadway_information},LN_TOTALMI,-1,-1;"
                                                    fr"LNS 'Through Lane Count' true true false 8 Short 8 38,First,#,{roadway_information},LNS,-1,-1;"
                                                    fr"SMTD_DAY 'SMTD Day Service' true true false 1 Text 0 0,First,#,{roadway_information},SMTD_DAY,0,1;"
                                                    fr"SMTD_NIGHT 'SMTD Night Service' true true false 1 Text 0 0,First,#,{roadway_information},SMTD_NIGHT,0,1;"
                                                    fr"SMTD_SUPPL 'SMTD Supplemental Service' true true false 1 Text 0 0,First,#,{roadway_information},SMTD_SUPPL,0,1;"
                                                    fr"SNOW_CRASH 'Snow Crash Numbers' true true false 255 Short 0 0,First,#,{roadway_information},NUMB1,-1,-1;"
                                                    fr"SNOW_DIST 'Snow District' true true false 3 Text 0 0,First,#,{roadway_information},SNOW_DIST,0,3;"
                                                    fr"SNOW_FID 'Snow Route Identifier' true true false 7 Text 0 0,First,#,{roadway_information},SNOW_FID,0,7;"
                                                    fr"SNOW_RT_NBR 'SNOW_RT_NBR' true true false 10 Text 0 0,First,#,{roadway_information},SNOW__RT_NBR,0,10;"
                                                    fr"SNOW_SLOPE 'Calculated Profile Grade' true true false 8 Double 8 38,First,#,{roadway_information},SNOW_SLOPE,-1,-1;"
                                                    fr"SNOW_TYPE 'Snow Type (Priority)' true true false 1 Text 0 0,First,#,{roadway_information},SNOW_TYPE,0,1;"
                                                    fr"SNOW_TIME 'Calculated Plow-time (E-E based on Lane Miles)' true true false 8 Double 8 38,First,#,{roadway_information},SNOW_TIME,-1,-1;"
                                                    fr"SNOW_TRBL 'Snow Trouble Spot Justification' true true false 2 Text 0 0,First,#,{roadway_information},SNOW_TRBL,0,2;"
                                                    fr"SURF_TYP 'Original Surface Type' true true false 50 Text 0 0,First,#,{roadway_information},SURF_TYP,0,50")

        # Add the fields to use
        arcpy.AddFields_management(snow_risk, [["LN_TOTAL", "Short", "Total Lane Count"],
                                               ["SINUOSITY", "Double", "Sinuosity"],
                                               ["COF", "Double", "Total COF Score"],
                                               ["COF_SAFETY", "Double", "Safety COF Score"],
                                               ["COF_AADT", "Short", "AADT Score"],
                                               ["COF_CRASH", "Short", "Crash Data Score"],
                                               ["COF_FC", "Short", "FC Score"],
                                               ["COF_SINE", "Short", "Sinuosity Score"],
                                               ["COF_SLOPE", "Short", "Slope Score"],
                                               ["COF_SMTD", "Short", "SMTD Bus Routes Score"],
                                               ["COF_SURF", "Short", "Surface Type Score"],
                                               ["COF_TRBL", "Short", "Trouble Spot Score"],
                                               ["POF", "Double", "Total POF Score"],
                                               ["POF_FLEET", "Short", "Distance to Fleet Score"],
                                               ["POF_LANES", "Short", "Lane Count Score"],
                                               ["POF_SALT", "Short", "Distance to Salt Score"],
                                               ["POF_WEATHER", "Short", "Predicted Cumulative Precipitation"],
                                               ["RISK", "Double", "Total Risk Score"],
                                               ["RISK_SAFETY", "Double", "Safety Risk Score"]])
        arcpy.MakeFeatureLayer_management(snow_risk, "SnowRisk")
        logger.info("Initialize Complete")

    def RiskProcessor(risk_type, segment_list, field, name):
        """Template for looping through rank lists and calculating fields"""
        if risk_type and segment_list and field and name:
            if risk_type == "consequence":
                logger.info(f"{name} Start")
                for segment in segment_list:
                    logger.info(f"{segment[1]}")
                    segment_selection = arcpy.SelectLayerByAttribute_management("SnowRisk", "NEW_SELECTION", segment[0])
                    arcpy.CalculateField_management(segment_selection, field, segment[1], "PYTHON3")
                logger.info(f"{name} Complete")
            elif risk_type == "probability":
                logger.info(f"{name} Start")
                for segment in segment_list:
                    selection = arcpy.SelectLayerByLocation_management("SnowRisk", "HAVE_THEIR_CENTER_IN", segment[0], None, "NEW_SELECTION")
                    subset_selection = arcpy.SelectLayerByAttribute_management(selection, "SUBSET_SELECTION", "SNOW_FID <> 'NORTE'")
                    arcpy.CalculateField_management(subset_selection, field, segment[1], "PYTHON3")
                logger.info(f"{name} Complete")
            else:
                raise ValueError("Incorrect risk type")
        else:
            raise NameError

    @logging_lines("Consequence")
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
        routes = [["SNOW_FID = 'NORTE'", "0"],  # 0 - Not a snow route and no bus routes
                  ["SNOW_FID <> 'NORTE' AND (SMTD_DAY = '0' OR SMTD_NIGHT = '0')", "1"],  # 1 - No SMTD bus routes
                  ["SNOW_FID <> 'NORTE' AND (SMTD_DAY = '1' OR SMTD_NIGHT = '1')", "3"],  # 3 - Day or night
                  ["SNOW_FID <> 'NORTE' AND (SMTD_DAY = '2' OR SMTD_NIGHT = '2')", "4"]]  # 4 - Express SMTD bus routes like exchange/transfer areas

        # Functional Classifications
        classifications = [["SNOW_FID = 'NORTE'", "0"],  # 0 - NORTE
                           ["SNOW_FID <> 'NORTE' AND FC = '7'", "1"],  # 1  - Local road or street
                           ["SNOW_FID <> 'NORTE' AND FC = '6'", "2"],  # 2 - Minor collector
                           ["SNOW_FID <> 'NORTE' AND FC = '5'", "3"],  # 3 - Major collector
                           ["SNOW_FID <> 'NORTE' AND (FC = '4' OR FC='3')", "4"]]  # 4 - Arterials

        # Slopes
        slopes = [["SNOW_FID = 'NORTE'", "0"],  # 0 - NORTE
                  ["SNOW_FID <> 'NORTE' AND SNOW_SLOPE <= 1.999", "1"],  # 1 - 0-2%
                  ["SNOW_FID <> 'NORTE' AND (SNOW_SLOPE >= 2 AND SNOW_SLOPE <= 2.999)", "2"],  # 2 - 2-3%
                  ["SNOW_FID <> 'NORTE' AND (SNOW_SLOPE >= 3 AND SNOW_SLOPE <= 3.999)", "3"],  # 3 - 3-4%
                  ["SNOW_FID <> 'NORTE' AND SNOW_SLOPE >= 4", "4"]]  # 4 - 4%+

        # Traffic Annual Averages (AADT)
        averages = [["SNOW_FID = 'NORTE'", "0"],  # 0 - NORTE
                    ["SNOW_FID <> 'NORTE' AND (AADT >= 0 AND AADT <= 750)", "1"],  # 1 - Less than 750
                    ["SNOW_FID <> 'NORTE' AND (AADT >= 751 AND AADT <= 1400)", "2"],  # 2 - 750 - 1400
                    ["SNOW_FID <> 'NORTE' AND (AADT >= 1401 AND AADT <= 3100)", "3"],  # 3 - > 1400 - 3100
                    ["SNOW_FID <> 'NORTE' AND AADT > 3100", "4"]]  # 4 - 3100+

        # Trouble Spot Justification
        troubles = [["SNOW_FID = 'NORTE'", "0"],  # 0 - NORTE
                    ["SNOW_FID <> 'NORTE' AND SNOW_TRBL IN ('12')", "1"],  # 1 - 12
                    ["SNOW_FID <> 'NORTE' AND SNOW_TRBL IN ('10', '11')", "2"],  # 2 - 10,11
                    ["SNOW_FID <> 'NORTE' AND SNOW_TRBL IN ('07', '13')", "3"],  # 3 - 7,13
                    ["SNOW_FID <> 'NORTE' AND SNOW_TRBL IN ('01', '02', '03', '04', '06')", "4"]]  # 4 - 1,2,3,4,6

        # Crash statistics
        crashes = [["SNOW_FID = 'NORTE'", "0"],  # 0 - NORTE
                   ["SNOW_FID <> 'NORTE' AND SNOW_CRASH = 0", "1"],  # 1 - 0 crashes
                   ["SNOW_FID <> 'NORTE' AND SNOW_CRASH = 1", "2"],  # 2 - 1 crashes
                   ["SNOW_FID <> 'NORTE' AND SNOW_CRASH = 2", "3"],  # 3 - 2 crashes
                   ["SNOW_FID <> 'NORTE' AND SNOW_CRASH >= 3", "4"]]  # 4 - 3+ crashes

        # Road materials
        materials = [["SNOW_FID = 'NORTE'", "0"],  # 0 - NORTE
                     ["SNOW_FID <> 'NORTE' AND SURF_TYP IN ('501', '510', '520', '525', '530', '540', '550', '560', '600', '610', '615', '620', '625', '630', '640', '650')", "1"],  # 1 - Asphalt
                     ["SNOW_FID <> 'NORTE' AND (SURF_TYP = '300' OR SURF_TYP = '500')", "2"],  # 2 - Bituminous Surface Treatment (Oil & Chip)
                     ["SNOW_FID <> 'NORTE' AND SURF_TYP LIKE '7%'", "3"],  # 3 - Concrete
                     ["SNOW_FID <> 'NORTE' AND SURF_TYP LIKE '8%'", "4"]]  # 4 - Brick

        # Sinuosity
        curves = [["SINUOSITY <= 1.02 AND SINUOSITY > .98", "1"],  # Sinuosity < 1 does not exist by definition but converting float-->double makes 1 values equal .999
                  ["SINUOSITY <= 1.05 AND SINUOSITY > 1.02", "2"],
                  ["SINUOSITY <= 1.1 AND SINUOSITY > 1.05", "3"],
                  ["SINUOSITY <= 29 AND SINUOSITY > 1.1", "4"]]

        @logging_lines("Sinuosity")
        def sinuosity():
            """Calculates the sinuosity value of each segment before giving it a rank"""

            # Sinuosity distance formula expressions; loop distance splits closed loops into 2 segments equal to 50% of the shape length and separately calculates the linear distance
            loop_distance = "!Shape.length!/(math.sqrt((!Shape.firstpoint.X!-!Shape!.positionAlongLine(0.5, True).firstpoint.X)**2 +" \
                            "(!Shape.firstpoint.Y!-!Shape!.positionAlongLine(0.5, True).firstpoint.Y)**2) + " \
                            "math.sqrt((!Shape!.positionAlongLine(0.5, True).firstpoint.X-!Shape.lastpoint.X!)**2 +" \
                            "(!Shape!.positionAlongLine(0.5, True).firstpoint.Y-!Shape.lastpoint.Y!)**2))"

            # Calculate sinuosity (curve length/linear length)
            selection_sinuosity = arcpy.SelectLayerByAttribute_management("SnowRisk", "NEW_SELECTION", "Shape_Length > 0")
            arcpy.CalculateField_management(selection_sinuosity, "SINUOSITY", loop_distance, "PYTHON3")

            # Calculate sinuosity if it has returned null thus far
            selection_nulls = arcpy.SelectLayerByAttribute_management("SnowRisk", "NEW_SELECTION", "SINUOSITY IS NULL AND Shape_Length > 0")
            arcpy.CalculateField_management(selection_nulls, "SINUOSITY", "30", "PYTHON3")

        @logging_lines("COF Total")
        def total_cof_scores():
            """Calculate Total COF Score using the risk assessment process"""

            # Calculate the two weighed sections of COF
            safety_factor = "!COF_FC!+!COF_SLOPE!+!COF_AADT!+!COF_TRBL!+!COF_CRASH!"
            safety_factor_average = f"{safety_factor}/5"
            social_factor = "!COF_SMTD!+!COF_FC!+!COF_SLOPE!+!COF_AADT!+!COF_TRBL!+!COF_CRASH!+!COF_SURF!+!COF_SINE!"
            safety_factor_total = 20
            safety_factor_average_total = 20
            social_factor_total = 32
            safety_factor_weight = .75
            social_factor_weight = .25

            # Calculate final COF, Risk, and Risk with only safety factors used
            cof = f"(((({safety_factor})/{safety_factor_total})*{safety_factor_weight}) + ((({social_factor})/{social_factor_total})*{social_factor_weight}))*4"
            cof_safety = f"(({safety_factor_average})/{safety_factor_average_total})*4"
            selection = arcpy.SelectLayerByAttribute_management("SnowRisk", "NEW_SELECTION", "SNOW_FID <> 'NORTE'")
            arcpy.CalculateField_management(selection, "COF", f"(round({cof}*10))/10", "PYTHON3")
            arcpy.CalculateField_management(selection, "COF_SAFETY", f"(round({cof_safety}*10))/10", "PYTHON3")
            logger.info("COF Totals Complete6")

        # Scoring
        RiskProcessor("consequence", routes, "COF_SMTD", "Bus Routes")
        RiskProcessor("consequence", classifications, "COF_FC", "Functional Classifications")
        RiskProcessor("consequence", slopes, "COF_SLOPE", "Slopes")
        RiskProcessor("consequence", averages, "COF_AADT", "AADT")
        RiskProcessor("consequence", troubles, "COF_TRBL", "Trouble Spots")
        RiskProcessor("consequence", crashes, "COF_CRASH", "Crash Data")
        RiskProcessor("consequence", materials, "COF_SURF", "Surface Materials")
        sinuosity()
        RiskProcessor("consequence", curves, "COF_SINE", "Sinuosity")
        total_cof_scores()

    @logging_lines("Probability")
    def probability():
        """Calculate POF scores using fields in the feature layer; uses static travel time calculation layers

        Fields:
        Salt - Distance from salt facilities
        Fleet - Distance from fleet maintenance facilities
        Lanes - Total number of lanes (lanes and special lanes)

        """

        # Salt distances layers
        salt_5 = os.path.join(salt, "Salt_5")
        salt_10 = os.path.join(salt, "Salt_10")
        salt_15 = os.path.join(salt, "Salt_15")
        salt_20 = os.path.join(salt, "Salt_20")

        # Fleet distances layers
        fleet_5 = os.path.join(fleet, "Fleet_5")
        fleet_10 = os.path.join(fleet, "Fleet_10")
        fleet_15 = os.path.join(fleet, "Fleet_15")
        fleet_20 = os.path.join(fleet, "Fleet_20")

        # Calculate total number of lanes
        arcpy.CalculateField_management("SnowRisk", "LN_TOTAL", "!LNS!+!LN_SPC_NBR!", "PYTHON3")

        # Distance to salt domes
        salt_domes = [[salt_5, "1"],  # 1 - 5 minutes or less
                      [salt_10, "2"],  # 2 - 10 minutes or less
                      [salt_15, "3"],  # 3 - 15 minutes or less
                      [salt_20, "4"]]  # 4 - 20 minutes or less

        # Distance to fleet garage
        fleet_garages = [[fleet_5, "1"],  # 1 - 5 minutes or less
                         [fleet_10, "2"],  # 2 - 10 minutes or less
                         [fleet_15, "3"],  # 3 - 15 minutes or less
                         [fleet_20, "4"]]  # 4 - 20 minutes or less

        # Total number of lanes
        lanes = [["LN_TOTAL <= 2 OR LN_TOTAL is NULL", "1"],
                 ["LN_TOTAL = 3", "2"],
                 ["LN_TOTAL = 4", "3"],
                 ["LN_TOTAL >= 5", "4"]]

        @logging_lines("Total POF")
        def total_pof_scores():
            """Calculate the two weighed section using the risk assessment process"""
            arcpy.SelectLayerByAttribute_management("SnowRisk", "CLEAR_SELECTION")
            mechanical_factor = "!POF_SALT!+!POF_FLEET!"
            weather_factor = "!POF_SALT!+!POF_LANES!"
            mechanical_factor_total = 8
            weather_factor_total = 8
            mechanical_factor_weight = .50
            weather_factor_weight = .50

            # Calculate final POF and risk score
            pof = f"(((({mechanical_factor})/{mechanical_factor_total})*{mechanical_factor_weight}) + ((({weather_factor})/{weather_factor_total})*{weather_factor_weight}))*4"
            arcpy.CalculateFields_management("SnowRisk", "PYTHON3", [["POF", f"(round({pof}*10)/10)"],
                                                                     ["RISK", "(round((!COF!*!POF!)*10)/10)"],
                                                                     ["RISK_SAFETY", "(round((!COF_SAFETY!*!POF!)*10)/10)"]])

        # Scoring
        RiskProcessor("probability", salt_domes, "POF_SALT", "Salt Domes")
        RiskProcessor("probability", fleet_garages, "POF_FLEET", "Fleet Garages")
        RiskProcessor("consequence", lanes, "POF_LANES", "Lane Counts")
        total_pof_scores()

    @logging_lines("Risk Minor")
    def risk_minor():
        """Create a risk scores using only minor arterials and local roads"""

        arcpy.FeatureClassToFeatureClass_conversion(snow_risk, risk_fgdb, "SnowRiskMinor", "FC IN ('6', '7')")
        arcpy.MakeFeatureLayer_management(snow_risk_minor, "SnowRiskMinor")

        # COF without AADT and FC
        safety_factor_minor = "!COF_SLOPE!+!COF_TRBL!+!COF_CRASH!"
        social_factor_minor = "!COF_SMTD!+!COF_SLOPE!+!COF_TRBL!+!COF_CRASH!+!COF_SURF!+!COF_SINE!"
        safety_factor_total = 12
        social_factor_total = 24
        safety_factor_weight = .75
        social_factor_weight = .25
        cof_minor = f"(((({safety_factor_minor})/{safety_factor_total})*{safety_factor_weight}) + ((({social_factor_minor})/{social_factor_total})*{social_factor_weight}))*4"

        # Calculate COF and Risk
        selection_minor = arcpy.SelectLayerByAttribute_management("SnowRiskMinor", "NEW_SELECTION", "SNOW_FID <> 'NORTE'")
        arcpy.CalculateField_management(selection_minor, "COF", f"round(({cof_minor}), 2)", "PYTHON3")
        arcpy.CalculateField_management(selection_minor, "RISK", "round((!COF!*!POF!), 2)", "PYTHON3")
        arcpy.Dissolve_management("SnowRiskMinor", snow_risk_minor_dissolved, ["ROAD_NAME", "SNOW_TYPE", "SNOW_DIST"], [["COF", "MEAN"], ["POF", "MEAN"], ["RISK", "MEAN"]], "SINGLE_PART")

    @logging_lines("Risk Rank")
    def risk_rank():
        """Rank risk scores for minor roads, descending order (highest rank = highest score)"""

        # Dissolve SnowRisk
        arcpy.MakeFeatureLayer_management(snow_risk, "SnowRisk")
        arcpy.Dissolve_management(snow_risk, snow_rank, ["SNOW_DIST", "SNOW_TYPE", "ROAD_NAME", "SNOW_RT_NBR"], [["COF", "MEAN"], ["POF", "MEAN"], ["RISK", "MEAN"], ["AADT", "MEAN"],
                                                                                                                 ["LN_TOTALMI", "SUM"]])

        # Add three rank fields, one for total, one for within its district, and one for within its route; also add a field for the first 3 digits of the route number and a full name
        arcpy.MakeFeatureLayer_management(snow_rank, "SnowRank")
        arcpy.AddFields_management("SnowRank", [["SNOW_RT_SHORT", "SHORT", "Snow Route Short", "4", "0"],
                                                ["SNOW_RT_NAME", "TEXT", "Snow Route Name", "40", "0"],
                                                ["RANK", "SHORT", "Total Rank", "4", "0"],
                                                ["RANK_DISTRICT", "SHORT", "District Rank", "4", "0"],
                                                ["RANK_ROUTE", "SHORT", "Route Rank", "4", "0"]])

        # Template for ranking
        def ranking(table, field):
            rank = 1
            clause = (None, "ORDER BY MEAN_COF DESC")
            with arcpy.da.UpdateCursor(table, field, sql_clause=clause) as cursor:
                for score in cursor:
                    score[0] = rank
                    cursor.updateRow(score)
                    rank += 1
            del cursor

        # Total rank
        ranking("SnowRank", "RANK")

        # Rank by district then by type/priority in that district
        districts = ["D1", "D2", "D3", "D4", "D5", "D6", "CBD"]
        subdistricts = ["101", "102", "201", "202", "301", "302", "401", "402", "501", "601", "602", "701", "702"]
        for district in districts:
            selected_districts = arcpy.SelectLayerByAttribute_management(snow_rank, "NEW_SELECTION", f"SNOW_DIST = '{district}'")
            ranking(selected_districts, "RANK_DISTRICT")

            for subdistrict in subdistricts:
                selected_priorities = arcpy.SelectLayerByAttribute_management(snow_rank, "NEW_SELECTION", f"SNOW_RT_NBR LIKE '{subdistrict}'")
                ranking(selected_priorities, "RANK_ROUTE")

        # Calculate the first three digits of the route number
        arcpy.CalculateField_management(snow_rank, "SNOW_RT_SHORT", "!SNOW_RT_NBR![:3]", "PYTHON3", )

        # Calculate the district name, e.g. District 1 Section A
        code_block = """def route(field):
            if field[2] == "1":
                letter = "A"
            elif field[2] == "2":
                letter = "B"
            else:
                letter = "0"

            number = field[0]
            name = f"District {number} Subgroup {letter}"
            return name"""
        arcpy.CalculateField_management(snow_rank, "SNOW_RT_NAME", "route(!SNOW_RT_NBR!)", "PYTHON3", code_block)

    # Try running above scripts
    try:
        initialize()
        consequence()
        probability()
        risk_minor()
        risk_rank()
    except (IOError, KeyError, NameError, IndexError, TypeError, UnboundLocalError, ValueError):
        traceback_info = traceback.format_exc()
        try:
            logger.info(traceback_info)
        except NameError:
            print(traceback_info)
    except arcpy.ExecuteError:
        try:
            logger.error(arcpy.GetMessages(2))
        except NameError:
            print(arcpy.GetMessages(2))
    except:
        logger.exception("Picked up an exception!")
    finally:
        try:
            logger.info("Script Execution Complete")
        except NameError:
            pass


def main():
    SnowRisk()


if __name__ == '__main__':
    main()
