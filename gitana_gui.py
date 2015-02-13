__author__ = 'atlanmod'

from git2db import Git2Db
from db2json_old import Db2Json
from filter import Filter
from aliaser import Aliaser
from metric_calculation import Metrics
from Tkinter import *
from tkFileDialog import *
import ttk
import os
import logging
import getopt
import threading
import re
import traceback


class GitTracker(Tk):

    LOG_FILENAME = "gitana_log.log"
    NOTIFICATION = "git_tracker_notification"
    PROCESS_INFO = "git_tracker_process_info"
    GENERATED_JSON = "./generated_json"

    logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO)
    with open(LOG_FILENAME, "w") as log_file:
        pass

    def __init__(self, notify):
        Tk.__init__(self)

        self.NOTIFY = notify

        self.REPO_JSON_PATH = ""
        self.REPO_JSON_FILTERED_PATH = ""
        self.REPO_JSON_ALIASED_PATH = ""
        self.REPO_JSON_METRIC_PATH = ""

        self.remove_relics_previous_run()
        self.initialize_gui()
        self.title("Git Tracker")
        self.wm_protocol("WM_DELETE_WINDOW", self.launch_thread_interrupt)
        self.mainloop()

    def remove_relics_previous_run(self):
        if os.path.exists(self.PROCESS_INFO):
            process_info = open(self.PROCESS_INFO, "r")

            if os.path.getsize(self.PROCESS_INFO) > 0:
                last_line = process_info.readlines()[-1]

                #if the previous process failed, delete the file where the failure happened
                if last_line.startswith("start"):
                    file_path = re.sub("^.*file:", '', last_line).strip('\n')
                    if os.path.exists(file_path):
                        os.remove(file_path)

                if os.path.exists(self.NOTIFICATION):
                    os.remove(self.NOTIFICATION)

            #however, delete the process info file before starting the new run
            process_info.close()
            os.remove(self.PROCESS_INFO)

    def launch_thread_interrupt(self):
        self.buttonFinish.config(state=DISABLED)
        self.buttonAbort.config(state=NORMAL)
        self.thread_interrupt = threading.Thread(target=self.interrupt)
        self.thread_interrupt.daemon = True
        self.thread_interrupt.start()
        self.thread_interrupt.join()

    def interrupt(self):
        self.info_execution.set("Aborting...")
        sys.exc_clear()
        sys.exc_traceback = sys.last_traceback = None
        os._exit(-1)

    def initialize_gui(self):
        self.geometry("600x435+300+300")
        self.grid()

        ##########################
        #repo info label
        labelRepoInfo = Label(self, text=u"Repository Info:", anchor="w", width=30)
        labelRepoInfo.grid(column=0, row=1, sticky='WE')

        #select repo
        labelRepoPath = Label(self, text=u"Path", anchor="w", width=30)
        labelRepoPath.grid(column=0, row=2, sticky='W')

        self.repoPathVariable = StringVar()
        self.entryRepoPath = Entry(self, textvariable=self.repoPathVariable, width=50)
        self.entryRepoPath.grid(column=1, row=2, sticky='W')

        buttonSearchRepo = Button(self, text=u"search", command=self.search_for_directory)
        buttonSearchRepo.grid(column=2, row=2, sticky="E")

        #insert repo name
        labelRepoName = Label(self, text=u"Name", anchor="w", width=30)
        labelRepoName.grid(column=0, row=3, sticky='W')

        self.repoNameVariable = StringVar()
        self.entryRepoName = Entry(self, textvariable=self.repoNameVariable, width=50)
        self.entryRepoName.grid(column=1, row=3, sticky='W')

        #insert repo owner
        labelRepoOwner = Label(self, text=u"Owner", anchor="w", width=30)
        labelRepoOwner.grid(column=0, row=4, sticky='W')

        self.repoOwnerVariable = StringVar()
        self.entryRepoOwner = Entry(self, textvariable=self.repoOwnerVariable, width=50)
        self.entryRepoOwner.grid(column=1, row=4, sticky='W')

        ##########################
        #empty label
        emptyLabel = Label(self, anchor="w", width=30)
        emptyLabel.grid(column=0, row=5, sticky='WE')

        ##########################
        #filtering resources label
        labelFiltering = Label(self, text=u"Filtering:", anchor="w", width=30)
        labelFiltering.grid(column=0, row=6, sticky='WE')

        #insert file for forbidden resources
        forbiddenResourcesPath = Label(self, text=u"Resources", anchor="w", width=30)
        forbiddenResourcesPath.grid(column=0, row=7, sticky='W')

        self.forbiddenResourcesPathVariable = StringVar()
        self.entryForbiddenResourcesPath = Entry(self, textvariable=self.forbiddenResourcesPathVariable, width=50)
        self.entryForbiddenResourcesPath.grid(column=1, row=7, sticky='W')

        buttonSearchForbiddenResources = Button(self, text=u"search", command=self.search_for_resource)
        buttonSearchForbiddenResources.grid(column=2, row=7, sticky="E")

        #insert file for forbidden extensions
        forbiddenExtsPath = Label(self, text=u"Extensions", anchor="w", width=30)
        forbiddenExtsPath.grid(column=0, row=8, sticky='W')

        self.forbiddenExtsPathVariable = StringVar()
        self.entryForbiddenExtsPath = Entry(self, textvariable=self.forbiddenExtsPathVariable, width=50)
        self.entryForbiddenExtsPath.grid(column=1, row=8, sticky='W')

        buttonSearchForbiddenExts = Button(self, text=u"search", command=self.search_for_extension)
        buttonSearchForbiddenExts.grid(column=2, row=8, sticky="E")

        ##########################
        #empty label
        emptyLabel_ = Label(self, anchor="w", width=30)
        emptyLabel_.grid(column=0, row=9, sticky='WE')

        ##########################
        #Aliasing label
        labelAliasing = Label(self, text=u"Aliasing:", anchor="w", width=30)
        labelAliasing.grid(column=0, row=10, sticky='WE')

        #insert file for aliasing users
        aliasingUsersLabel = Label(self, text=u"Users", anchor="w", width=30)
        aliasingUsersLabel.grid(column=0, row=11, sticky='W')

        self.aliasingUsersPathVariable = StringVar()
        self.entryAliasingUsersPath = Entry(self, textvariable=self.aliasingUsersPathVariable, width=50)
        self.entryAliasingUsersPath.grid(column=1, row=11, sticky='W')

        buttonSearchAliasingUsers = Button(self, text=u"search", command=self.search_for_aliases)
        buttonSearchAliasingUsers.grid(column=2, row=11, sticky="E")

        ##########################
        #empty label
        emptyLabel = Label(self, anchor="w", width=30)
        emptyLabel.grid(column=0, row=12, sticky='WE')

        ##########################
        #Tuning label
        labelTuning = Label(self, text=u"Tuning:", anchor="w", width=30)
        labelTuning.grid(column=0, row=13, sticky='WE')

        #Primary expert knowledge
        labelPrimaryExpertKnowledge = Label(self, text=u"Primary Dev. Knowl.", anchor="w", width=30)
        labelPrimaryExpertKnowledge.grid(column=0, row=14, sticky='W')

        self.labelPrimaryExpertKnowledgeVariable = StringVar()
        entryLabelPrimaryExpertKnowledge = Entry(self, textvariable=self.labelPrimaryExpertKnowledgeVariable, width=30)
        self.labelPrimaryExpertKnowledgeVariable.set("1/D")
        entryLabelPrimaryExpertKnowledge.grid(column=1, row=14, sticky='W')

        #Secondary Expert knowledge proportion
        labelSecondaryExpertProportion = Label(self, text=u"Secondary Dev. Knowl. Prop.", anchor="w", width=40)
        labelSecondaryExpertProportion.grid(column=0, row=16, sticky='W')

        self.labelSecondaryExpertProportionVariable = StringVar()
        entryLabelSecondaryExpertProportion = Entry(self, textvariable=self.labelSecondaryExpertProportionVariable, width=30)
        self.labelSecondaryExpertProportionVariable.set("0.5")
        entryLabelSecondaryExpertProportion.grid(column=1, row=16, sticky='W')

        #detail level
        self.detailLevelVariable = StringVar()
        labelDetailLevel = Label(self, text=u"Detail Level", anchor="w", width=40)
        labelDetailLevel.grid(column=0, row=17, sticky='W')

        self.detailLevelComboBox = ttk.Combobox(self, textvariable=self.detailLevelVariable)
        self.detailLevelComboBox['values'] = ('line', 'file')
        self.detailLevelComboBox.current(0)
        self.detailLevelComboBox.grid(column=1, row=17, sticky='W')


        #metric
        labelMetric = Label(self, text=u"Metric", anchor="w", width=40)
        labelMetric.grid(column=0, row=18, sticky='W')

        self.metricComboBoxVariable = StringVar()
        self.metricComboBox = ttk.Combobox(self, textvariable=self.metricComboBoxVariable)
        self.metricComboBox['values'] = ('last change', 'multiple changes', 'distinct changes', 'weighted distinct changes')
        self.metricComboBox.current(0)
        self.metricComboBox.grid(column=1, row=18, sticky='W')

        #Finish button
        self.buttonFinish = Button(self, text=u"Execute", command=self.launch_thread_execute)
        self.buttonFinish.grid(column=3, row=19, sticky="E")

        #Abort interrupt
        self.buttonAbort = Button(self, text=u"Abort", command=self.launch_thread_interrupt)
        self.buttonAbort.grid(column=4, row=19, sticky="E")
        self.buttonAbort.config(state=DISABLED)

        self.info_execution = StringVar()
        labelExecuting = Label(self, textvariable=self.info_execution, anchor="w", width=40)
        labelExecuting.grid(column=0, row=20, sticky='EW')

        self.grid_columnconfigure(0, weight=1)
        self.resizable(True, False)

    def search_for_directory(self):
        dir = askdirectory(parent=self, title='Choose a directory')
        self.repoPathVariable.set(dir)
        try:
            repoName = dir.split('/')[-1]
            self.repoNameVariable.set(re.sub(r'\W', '', repoName).lower())
        except:
            try:
                repoName = dir.split('\\')[-1]
                self.repoNameVariable.set(re.sub(r'\W', '', repoName).lower())
            except:
                repoName = ''

    def search_for_resource(self):
        f = askopenfilename(parent=self, title='Choose a file',
                            filetypes=[("Forbidden-resource files", "*.forbres")])
        self.forbiddenResourcesPathVariable.set(f)

    def search_for_extension(self):
        f = askopenfilename(parent=self, title='Choose a file', filetypes=[("Forbidden-extension files", "*.forbext")])
        self.forbiddenExtsPathVariable.set(f)

    def search_for_aliases(self):
        f = askopenfilename(parent=self, title='Choose a file', filetypes=[("User-alias files", "*.usralias")])
        self.aliasingUsersPathVariable.set(f)

    def check_path_existance(self, string):
        flag = True
        if not os.path.exists(string):
            flag = False
        return flag

    def check_extension(self, string, extension):
        flag = True
        ext = string.split('.')[-1]
        if ext != extension:
            flag = False
        return flag

    def launch_thread_execute(self):
        self.info_execution.set("Executing...")
        self.buttonFinish.config(state=DISABLED)
        self.buttonAbort.config(state=NORMAL)
        self.thread_execute = threading.Thread(target=self.validator)
        self.thread_execute.daemon = True
        self.thread_execute.start()

    def validator(self):
        flag = True
        if self.repoPathVariable.get() == "":
            if self.repoNameVariable.get() == "" or self.repoOwnerVariable.get() == "":
                self.repoPathVariable.set("path cannot be empty if the name and owner are empty!")
                flag = False
        else:
            if not self.check_path_existance(self.repoPathVariable.get()):
                self.repoPathVariable.set("not valid path!")
                flag = False

        if self.repoNameVariable.get() == "":
            self.repoNameVariable.set("cannot be empty!")
            flag = False
        else:
            self.repoNameVariable.set(re.sub(r'\W', '', self.repoNameVariable.get()).lower())

        if self.labelPrimaryExpertKnowledgeVariable.get() == "":
            self.labelPrimaryExpertKnowledgeVariable.set("cannot be empty!")
            flag = False
        else:
            if self.labelPrimaryExpertKnowledgeVariable.get() != "1/D":
                try:
                    value = float(self.labelPrimaryExpertKnowledgeVariable.get())
                    if value < 0 or value >= 1:
                        self.labelPrimaryExpertKnowledgeVariable.set("(0,1] || 1/D")
                        flag = False
                except:
                    self.labelPrimaryExpertKnowledgeVariable.set("(0,1] || 1/D")
                    flag = False


        if self.labelSecondaryExpertProportionVariable.get() == "":
            self.labelSecondaryExpertProportionVariable.set("cannot be empty!")
            flag = False
        else:
            try:
                value = float(self.labelSecondaryExpertProportionVariable.get())
                if value < 0 or value >= 1:
                    self.labelSecondaryExpertProportionVariable.set("(0,1]")
                    flag = False
            except:
                flag = False
                self.labelSecondaryExpertProportionVariable.set("(0,1]")

        #optional
        if self.repoOwnerVariable.get() != "":
            self.repoOwnerVariable.set(re.sub(r'\W', '', self.repoOwnerVariable.get()))

        if self.forbiddenResourcesPathVariable.get() != "":
            if not self.check_path_existance(self.forbiddenResourcesPathVariable.get()):
                self.forbiddenResourcesPathVariable.set("not valid path!")
                flag = False
            else:
                if not self.check_extension(self.forbiddenResourcesPathVariable.get(), 'forbres'):
                    self.forbiddenResourcesPathVariable.set("not valid ext (.forbres)!")
                    flag = False

        if self.forbiddenExtsPathVariable.get() != "":
            if not self.check_path_existance(self.forbiddenExtsPathVariable.get()):
                self.forbiddenExtsPathVariable.set("not valid!")
                flag = False
            else:
                if not self.check_extension(self.forbiddenExtsPathVariable.get(), 'forbext'):
                    self.forbiddenExtsPathVariable.set("not valid ext (.forbext)!")
                    flag = False

        if self.aliasingUsersPathVariable.get() != "":
            if not self.check_path_existance(self.aliasingUsersPathVariable.get()):
                self.aliasingUsersPathVariable.set("not valid!")
                flag = False
            else:
                if not self.check_extension(self.aliasingUsersPathVariable.get(), 'usralias'):
                    self.aliasingUsersPathVariable.set("not valid ext (.usralias)!")
                    flag = False

        if flag:
            self.execute_process()

    def execute_process(self):
        self.init_process()
        self.start_process()
        self.duplicate_files()
        self.notify()
        self.info_execution.set("Finished")
        self.buttonFinish.config(state=NORMAL)
        self.buttonAbort.config(state=DISABLED)

    #duplicate files to use them in the visualization part, a backup with a meaningful name is kept for further requests
    def duplicate_files(self):
        files = [s for s in os.listdir(self.OUTPUT_DIRECTORY)
                 if os.path.isfile(os.path.join(self.OUTPUT_DIRECTORY, s))]
        files.sort(key=lambda s: os.path.getmtime(os.path.join(self.OUTPUT_DIRECTORY, s)))
        files.reverse()

        counter = 0
        for f in files:
            last_but_one = f.split('.')[-2]
            if last_but_one in ['branches', 'dirs', 'extension_relevance', 'exts', 'files', 'user_relevance', 'project_info']:
                with open(self.OUTPUT_DIRECTORY + f) as input:
                    with open(self.OUTPUT_DIRECTORY_VISUALIATION + last_but_one + ".json", "w") as output:
                        for line in input:
                            output.writelines(line)
                counter += 1

            if counter == 7:
                break

    def notify(self):
        if self.NOTIFY:
            notified = open(self.NOTIFICATION, "w")
            notified.close()
        sys.exc_clear()
        sys.exc_traceback = sys.last_traceback = None
        return

    def start_process(self):
        process_info = open(self.PROCESS_INFO, "w")
        process_info.write("process start\n")

        print "PROCESS STARTED"
        try:
            if self.GIT2DB_STEP:
                process_info.write("start GIT2DB\n")
                print "ANALYSING FILES"
                extractor = Git2Db(self.REPO_PATH, self.REPO_NAME, self.REPO_OWNER, logging)
                extractor.extract()
                process_info.write("end GIT2DB\n")
        except:
            logging.error("Git2Db: process failed due to: " + traceback.format_exc())
            process_info.close()
            os._exit(-1)

        output_json = self.REPO_JSON_PATH
        if self.DB2JSON_STEP:
            try:
                process_info.write("start DB2JSON. file:" + self.REPO_JSON_PATH + "\n")
                print "DEVELOPER KNOWLEDGE CALCULATION"
                exporter = Db2Json(self.DB_NAME, self.REPO_NAME, self.REPO_OWNER, output_json, self.LINE_DETAILS, logging)
                exporter.export()
                process_info.write("end DB2JSON\n")
            except:
                logging.error("Db2Json: process failed due to: " + traceback.format_exc())
                process_info.close()
                os._exit(-1)

        if self.FILTERING_STEP:
            try:
                print "FILTERING"
                input_json = output_json
                output_json = input_json.replace(self.JSON, self.FILTERED + self.JSON)
                self.REPO_JSON_FILTERED_PATH = output_json
                process_info.write("start FILTERING. file:" + self.REPO_JSON_FILTERED_PATH + "\n")
                filter = Filter(input_json, output_json, self.FORBIDDEN_RESOURCES_PATH, self.FORBIDDEN_EXTENSION_PATH, logging)
                filter.filter()
                process_info.write("end FILTERING\n")
            except:
                logging.error("Filtering: process failed due to: " + traceback.format_exc())
                process_info.close()
                os._exit(-1)

        if self.ALIASING_STEP:
            try:
                print "ALIASING"
                input_json = output_json
                output_json = input_json.replace(self.JSON, self.MERGED + self.JSON)
                self.REPO_JSON_ALIASED_PATH = output_json
                process_info.write("start ALIASING. file:" + self.REPO_JSON_ALIASED_PATH + "\n")
                merger = Aliaser(input_json, output_json, self.USER_ALIASES_PATH, logging)
                merger.execute()
                process_info.write("end ALIASING\n")
            except:
                logging.error("Aliasing: process failed due to: " + traceback.format_exc())
                process_info.close()
                os._exit(-1)

        print "BUS FACTOR CALCULATION"
        input_json = output_json
        output_json = input_json.replace(self.JSON, self.BUS_FACTOR + self.DEVELOPER_KNOWLEDGE_STRATEGY + self.JSON)
        try:
            self.REPO_JSON_METRIC_PATH = output_json
            process_info.write("start METRIC. file:" + self.REPO_JSON_METRIC_PATH + "\n")
            metrics = Metrics(input_json, output_json,
                              self.DEVELOPER_KNOWLEDGE_STRATEGY,
                              self.PRIMARY_EXPERT_KNOWLEDGE,
                              self.SECONDARY_EXPERT_KNOWLEDGE_PROPORTION, logging)
            metrics.export_bus_factor_information()
            process_info.write("end METRIC\n")
        except:
            logging.error("Metrics: process failed due to: " + traceback.format_exc())
            process_info.close()
            os._exit(-1)

        process_info.write("process end\n")
        process_info.close()

        print "PROCESS FINISHED"

    def init_process(self):
        self.OUTPUT_DIRECTORY = "./generated_json/"
        self.OUTPUT_DIRECTORY_VISUALIATION = "./data/"
        self.REPO_PATH = self.repoPathVariable.get()
        self.REPO_NAME = self.repoNameVariable.get()
        self.REPO_OWNER = self.repoOwnerVariable.get()
        self.FORBIDDEN_RESOURCES_PATH = self.forbiddenResourcesPathVariable.get()
        self.FORBIDDEN_EXTENSION_PATH = self.forbiddenExtsPathVariable.get()
        self.USER_ALIASES_PATH = self.aliasingUsersPathVariable.get()
        self.DB_NAME = Git2Db.GITANA + self.REPO_NAME + "_" + self.REPO_OWNER

        if self.detailLevelVariable.get() == "line":
             self.LINE_DETAILS = True
        else:
            self.LINE_DETAILS = False

        if self.labelPrimaryExpertKnowledgeVariable.get() == "1/D":
            self.PRIMARY_EXPERT_KNOWLEDGE = "default"
        else:
            self.PRIMARY_EXPERT_KNOWLEDGE = self.labelPrimaryExpertKnowledgeVariable.get()

        if self.labelSecondaryExpertProportionVariable.get() == "0.5":
            self.SECONDARY_EXPERT_KNOWLEDGE_PROPORTION = "default"
        else:
            self.SECONDARY_EXPERT_KNOWLEDGE_PROPORTION = self.labelSecondaryExpertProportionVariable.get()

        self.DEVELOPER_KNOWLEDGE_STRATEGY = self.metricComboBoxVariable.get().replace(' ', '_')


        self.JSON = ".json"
        if self.LINE_DETAILS:
            self.DETAILS = ".line-level-detail"
        else:
            self.DETAILS = ".file-level-detail"
        self.FILTERED = ".filtered"
        self.MERGED = ".merged"
        self.BUS_FACTOR = ".bus-factor."

        #create output directories
        if not os.path.exists(self.OUTPUT_DIRECTORY):
            os.makedirs(self.OUTPUT_DIRECTORY)
        if not os.path.exists(self.OUTPUT_DIRECTORY_VISUALIATION):
            os.makedirs(self.OUTPUT_DIRECTORY_VISUALIATION)

        if self.REPO_OWNER:
            self.REPO_JSON_PATH = self.OUTPUT_DIRECTORY + self.REPO_NAME + "." + self.REPO_OWNER + self.DETAILS + self.JSON
        else:
            self.REPO_JSON_PATH = self.OUTPUT_DIRECTORY + self.REPO_NAME + self.DETAILS + self.JSON

        #tool optimization (skipping steps)
        self.GIT2DB_STEP = True
        self.DB2JSON_STEP = True
        self.FILTERING_STEP = True
        self.ALIASING_STEP = True

        if self.REPO_PATH == "":
            self.GIT2DB_STEP = False
        if os.path.exists(self.REPO_JSON_PATH) and self.REPO_PATH == "":
            self.DB2JSON_STEP = False
        if self.FORBIDDEN_RESOURCES_PATH == "" and self.FORBIDDEN_EXTENSION_PATH == "":
            self.FILTERING_STEP = False
        if self.USER_ALIASES_PATH == "":
            self.ALIASING_STEP = False


def main(argv):
    notify = False
    try:
        opts, args = getopt.getopt(argv, "hn", ["notify="])
    except getopt.GetoptError:
        print 'GitTracker.py -n <notify>'
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print 'test.py -n <notify:True|False>'
            sys.exit()
        elif opt in ("-n", "--notify"):
            notify = bool(args[0])
    GitTracker(notify)

if __name__ == "__main__":
    main(sys.argv[1:])
