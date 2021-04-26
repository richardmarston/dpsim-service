from models.analysis_response import AnalysisResponse  # noqa: E501
from multiprocessing import Pool, Array, Queue, Manager
from flask import make_response
from enum  import Enum
from glob  import glob
import os, traceback, tempfile
import connexion
import requests

import dpsimpy
import results_db

from io import BytesIO
import zipfile

class LogFile:
    def __init__(self, analysis_id, filename):
        self.analysis_id = analysis_id
        self.filename = filename
        self.data = ""

    def write(self, data):
        self.data += data

    def close(self):
        results_db.add_log(self.analysis_id, self.filename, self.data)

class ResultFile(LogFile):
    def __init__(self, analysis_id, filename):
        super().__init__(analysis_id, filename)

    def close(self):
        results_db.add_result(self.analysis_id, self.filename, self.data)

def ok_func(arg):
    filep = open("debug/callback.out", "w")
    filep.write(str(arg))
    filep.close()

def error_func(arg):
    filep = open("debug/callback.err", "w")
    filep.write(str(arg))
    filep.close()

class SimRunner:
    def __init__(self, msg):
        self.analysis_id = msg['analysis_id']
        self.name = msg['name']
        self.out = LogFile(self.analysis_id, "debug/" + "Analysis_" + str(self.analysis_id) + ".out")
        self.err = LogFile(self.analysis_id, "debug/" + "Analysis_" + str(self.analysis_id) + ".err")
        self.model_id = msg['model_id']
        self.analysis_name = "Analysis_" + str(self.analysis_id)
        self.csv_data = msg['csv_data']

    # This function writes the xml files to disk so that dpsim can read them in.
    # This function should not be required when we have updated dpsim to accept
    # the input files as in-memory data.
    @staticmethod
    def create_files(files):
        filenames = []
        for filedata in files:
            fp, path = tempfile.mkstemp(suffix=".xml", text=True)
            os.write(fp, bytes(filedata, "utf-8"));
            os.close(fp);
            filenames.append(path)
        return filenames

    def get_model_data(self, model_id):
        url = "http://cim-service:8080/models/"+str(model_id)+"/export"
        response = requests.get(url)
        self.out.write("Response: " + str(response) + "\n")
        json_str = str(response.json())
        truncated_response = (json_str[:75] + '..') if len(json_str) > 75 else json_str
        self.out.write("Response json (truncated): " + truncated_response + "\n")
        return response.json()

    def send_file_to_db(self, filename, filetype):
        if filetype == "result":
            db_file = ResultFile(self.analysis_id, filename)
        elif filetype == "log":
            db_file = LogFile(self.analysis_id, filename)
        with open(filename) as f:
            db_file.write(f.read())
        db_file.close()

    def send_data_to_db(self, filename, filetype, data):
        if filetype == "result":
            db_file = ResultFile(self.analysis_id, filename)
        elif filetype == "log":
            db_file = LogFile(self.analysis_id, filename)
        db_file.write(data)
        db_file.close()

    def execute_dpsimpy(self):
        #initialise dpsimpy
        logger = dpsimpy.Logger(self.analysis_name)
        reader = dpsimpy.CIMReader(self.analysis_name)
        system = reader.loadCIM(50, self.filenames, dpsimpy.Domain.SP, dpsimpy.PhaseType.Single)
        if system == None:
            self.err.write("Could not start dpsimpy with files: " + self.filenames)
            TaskExecutor.status_list[self.analysis_id] = TaskExecutor.Status.error.value
            return
        self.read_load_profiles(system)
        sim = dpsimpy.Simulation(self.analysis_name)
        sim.set_system(system)
        sim.set_domain(dpsimpy.Domain.SP)
        sim.set_solver(dpsimpy.Solver.NRP)
        for node in system.nodes:
            logger.log_attribute(node.name()+'.V', 'v', node);
        sim.add_logger(logger)
        sim.run()

    def read_load_profiles(self, system):
        self.files = []
        self.csv_directory = None
        if self.csv_data:
            try:
                fp = BytesIO(self.csv_data)
                with zipfile.ZipFile(fp, "r") as zipfilep:
                    zipfilep.extractall("CSV_DATA_Analysis_" + str(self.analysis_id))
                self.csv_directory = "CSV_DATA_Analysis_" + str(self.analysis_id)
            except Exception as e:
                self.err.write("Failed to apply csv data: " + e)

        if self.csv_directory:
            assignList = { }
            for num in [1, 3, 4, 5, 6, 8, 10, 11, 12, 14]:
                assignList['LOAD-H-' + str(num)] = 'Load_H_' + str(num)
            for num in [1, 3, 7, 9, 10, 12, 13, 14]:
                assignList['LOAD-I-' + str(num)] = 'Load_I_' + str(num)
            self.csvreader = dpsimpy.CSVReader(self.name, self.csv_directory, assignList, dpsimpy.LogLevel.info)
            self.csvreader.assignLoadProfile(system, 0, 1, 300, dpsimpy.CSVReaderMode.MANUAL, dpsimpy.CSVReaderFormat.SECONDS)

    def run(self):
        try:
            self.out.write("Running analysis: " + str(self.analysis_id) + "\n")
            TaskExecutor.status_list[self.analysis_id] = TaskExecutor.Status.running.value

            files = self.get_model_data(self.model_id)

            # prepare the files for dpsim to read. we should make dpsim accept data blobs.
            # however, that requires work in 3 projects and a technical discussion first.
            self.filenames = SimRunner.create_files(files)

            self.execute_dpsimpy()

            # clean up the files that we created
            for tempname in self.filenames:
                os.unlink(tempname)

            log_filename = "logs/" + self.analysis_name + "_CIM.log"
            result_filename = "logs/" + self.analysis_name + ".csv"
            self.send_file_to_db(log_filename, "log")
            self.send_file_to_db(result_filename, "result")

            TaskExecutor.status_list[self.analysis_id] = TaskExecutor.Status.complete.value

        except Exception as e:
            self.err.write("analysis failed: " + str(self.analysis_id) + " with: " + str(e) + os.linesep)
            backtrace = traceback.format_exc()
            self.err.write("backtrace: " + str(backtrace) + os.linesep)
            TaskExecutor.status_list[self.analysis_id] = TaskExecutor.Status.error.value
        finally:
            self.err.close()
            self.out.close()

class TaskExecutor:
    """
        This singleton class polls the request queue and
        allocates tasks to the process pool.
    """

    _task_executor = None

    # This status list is shared between the main process
    # and the child processes.
    status_list = None
    num_procs = 1
    # TODO: We currently have a limit of 1000 runs.
    # If this is to be long running, and not just a
    # short-lived Kubernetes job, we need a circular
    # buffer or disk backing for the task details.
    max_analysis=1000

    class Status(Enum):
        not_requested_yet = 0
        requested = 1
        running = 2
        complete = 3
        error = 4

    def __init__(self):
        if not os.path.exists('debug'):
            os.makedirs('debug')
        self.out = open("debug/main.out", "w")
        self.err = open("debug/main.err", "w")
        self.log("Starting")
        self.tasks = []
        self.manager = Manager()
        self.run_queue = self.manager.Queue()
        self.pool = Pool(processes=TaskExecutor.num_procs)
        for i in range(TaskExecutor.num_procs):
            self.pool.apply_async(TaskExecutor.wait_for_run_command, (self.run_queue,), callback=ok_func, error_callback=error_func)

    def close(self):
        self.pool.close()
        self.pool.join()
        self.out.close()
        self.err.close()

    def __del__(self):
        self.close()

    def log(self, message):
        self.out.write(message + "\n")
        self.out.flush()

    def error(self, message):
        self.err.write(message + "\n")
        self.err.flush()

    @staticmethod
    def get_task_executor():
        if TaskExecutor._task_executor is None:
            TaskExecutor.status_list = Array('I', TaskExecutor.max_analysis)
            TaskExecutor.model_list = Array('I', TaskExecutor.max_analysis)
            TaskExecutor._task_executor = TaskExecutor()
        return TaskExecutor._task_executor

    def request_analysis(self, params):
        analysis_id = len(self.tasks)
        params['analysis_id'] = analysis_id
        self.tasks.append(params)
        TaskExecutor.status_list[analysis_id] = TaskExecutor.Status.requested.value
        self.log("Putting request for analysis " + str(analysis_id) + " on run queue.")
        self.run_queue.put(self.tasks[analysis_id])
        return analysis_id

    @staticmethod
    def get_status(analysis_id):
        if TaskExecutor.max_analysis > analysis_id:
            return TaskExecutor.Status(TaskExecutor.status_list[analysis_id]).name
        else:
            self.error("No analysis found with id: " + str(analysis_id))
            return -1

    @staticmethod
    def get_all_status():
        analysis_id = 0
        analyses = []
        while TaskExecutor.status_list != None and \
              TaskExecutor.Status(TaskExecutor.status_list[analysis_id]).name != TaskExecutor.Status.not_requested_yet.name:
            analyses.append({ "id": analysis_id, "status": TaskExecutor.Status(TaskExecutor.status_list[analysis_id]).name })
            analysis_id +=1
        return analyses

    def get_debug_logs(self):
        files = glob( "debug/*")
        log_string = ""
        for file_ in files:
            try:
                with open(file_) as f:
                    log_string += os.linesep + file_ + ":" + os.linesep + os.linesep + f.read()
            except Exception as e:
                log_string = "Failed to read: " + file_ + " because: " + e + "\n"
                self.error("Failed to read: " + file_)
        return log_string

    def get_analysis_logs(self, analysis_id):
        if analysis_id >= len(self.tasks):
            return "Analysis id not recognised: " + str(analysis_id) + os.linesep

        files = results_db.get_logs(analysis_id)
        log_string = ""
        for filename in files:
            log_string += os.linesep + filename + ":" + os.linesep + os.linesep + str(files[filename])
        return log_string

    def get_results(self, analysis_id):
        if analysis_id >= len(self.tasks):
            return "Analysis id not recognised: " + str(analysis_id) + os.linesep

        files = results_db.get_results(analysis_id)
        log_string = ""
        for filename in files:
            log_string += os.linesep + filename + ":" + os.linesep + os.linesep + files[filename]
        return log_string

    @staticmethod
    def wait_for_run_command(queue):
        while True:
            msg = queue.get()
            runner = SimRunner(msg)
            result = runner.run()

def add_analysis():  # noqa: E501
    """Add a new analysis
     # noqa: E501
    :rtype: AnalysisResponse
    """
    model_id = connexion.request.form['modelid']
    name     = connexion.request.form['name']
    csv_file = connexion.request.files["csv_data"]
    if csv_file:
        csv_data = csv_file.stream.read()
    else:
        csv_data = None
    taskExecutor = TaskExecutor.get_task_executor()
    taskExecutor.log("Analysis requested for model id: " + str(model_id))
    analysis_id = TaskExecutor.get_task_executor().request_analysis({ "model_id": model_id, "name": name, "csv_data": csv_data })
    taskExecutor.log("Analysis requested with id: " + str(analysis_id))

    return_object = { "analysis_id": analysis_id, "model_id": model_id, "name": name }

    return return_object

def delete_analysis(id_):  # noqa: E501
    """Delete specific analysis including results

     # noqa: E501

    :param id: Analysis id
    :type id: int

    :rtype: AnalysisResponse
    """
    raise Exception('Unimplemented')


def get_all_analysis():  # noqa: E501
    """Get all network models

     # noqa: E501


    :rtype: List[AnalysisResponse]
    """
    return TaskExecutor.get_all_status()


def get_analysis(id_):  # noqa: E501
    """Get specific analysis status

     # noqa: E501

    :param id: Analysis id
    :type id: int

    :rtype: AnalysisResponse
    """
    status = TaskExecutor.get_status(id_)
    return { "status": status, "id": id_ }

def get_analysis_results(id_):  # noqa: E501
    """Get specific analysis status and results

     # noqa: E501

    :param id: Analysis id
    :type id: int

    :rtype: AnalysisResponse
    """
    taskExecutor = TaskExecutor.get_task_executor()
    response = make_response(taskExecutor.get_results(id_))
    response.mimetype = "text/plain"
    return response

def get_analysis_logs(id_):  # noqa: E501
    """Get specific analysis status and results

     # noqa: E501

    :param id: Analysis id
    :type id: int

    :rtype: AnalysisResponse
    """
    taskExecutor = TaskExecutor.get_task_executor()
    response = make_response(taskExecutor.get_analysis_logs(id_))
    response.mimetype = "text/plain"
    return response

def get_debug_logs():  # noqa: E501
    """Get specific analysis status and results

     # noqa: E501

    :param id: Analysis id
    :type id: int

    :rtype: AnalysisResponse
    """
    taskExecutor = TaskExecutor.get_task_executor()
    response = make_response(taskExecutor.get_debug_logs())
    response.mimetype = "text/plain"
    return response
