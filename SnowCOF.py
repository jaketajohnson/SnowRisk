"""
 SYNOPSIS

     SnowLines.py

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


def SnowConsequence():

    # Environment
    arcpy.env.overwriteOutput = True
    arcpy.parallelProcessingFactor = "7"
    arcpy.SetLogHistory(False)

    # Paths
    fgdb_folder = r"F:\Shares\FGDB_Services"
    imspfld_sde = os.path.join(fgdb_folder, r"DatabaseConnections\COSPW@imSPFLD@MCWINTCWDB.sde")
    sde_segments = os.path.join(imspfld_sde, r"imSPFLD.COSPW.FacilitiesStreets\imSPFLD.COSPW.RoadwayInformation")

    # GDB Paths
    script_folder = os.path.dirname(sys.argv[0])


def main():
    """
    Main execution code
    """
    # Make a few variables to use
    # script_folder = os.path.dirname(sys.argv[0])
    log_file_folder = r"C:\Scripts\SnowCOF\Log_Files"
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

        SnowConsequence()
        logger.info("Completed SnowConsequences processing")

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
