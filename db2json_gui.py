__author__ = 'atlanmod'

from Tkinter import *
from tkFileDialog import *
import ttk
import threading
import os
import re
import traceback
from gitana import Gitana


class DB2JSON_GUI(Tk):

    JSON_FILE_NAME = 'output.json'
    JSON_DIRECTORY_PATH = './json'
    ALIASED = 'aliased'
    FILTERED = 'filtered'

    def __init__(self):
        Tk.__init__(self)
        self.initialize()
        self.title("Export DB to JSON")
        self.mainloop()

    def initialize(self):
        ##########################
        #empty label
        emptyLabel = Label(self, anchor="w")
        emptyLabel.grid(column=0, row=1, sticky='WE')
        ##########################

        #insert db schema
        labelDBName = Label(self, text=u"DB name", anchor="w")
        labelDBName.grid(column=0, row=3, sticky='W')

        self.DBNameVariable = StringVar()
        self.entryDBName = Entry(self, textvariable=self.DBNameVariable, width=30)
        self.entryDBName.grid(column=1, row=3, sticky='W')

        ##########################
        #empty label
        emptyLabel = Label(self, anchor="w")
        emptyLabel.grid(column=0, row=5, sticky='WE')
        ##########################

        #filtering resources label
        labelFiltering = Label(self, text=u"Filtering:", anchor="w")
        labelFiltering.grid(column=0, row=6, sticky='WE')

        #insert file for forbidden resources
        forbiddenResourcesPath = Label(self, text=u"Resources", anchor="w")
        forbiddenResourcesPath.grid(column=0, row=7, sticky='W')

        self.forbiddenResourcesPathVariable = StringVar()
        self.entryForbiddenResourcesPath = Entry(self, textvariable=self.forbiddenResourcesPathVariable, width=30)
        self.entryForbiddenResourcesPath.grid(column=1, row=7, sticky='W')

        buttonSearchForbiddenResources = Button(self, text=u"search", command=self.search_for_resource)
        buttonSearchForbiddenResources.grid(column=2, row=7, sticky="E")

        #insert file for forbidden extensions
        forbiddenExtsPath = Label(self, text=u"Extensions", anchor="w")
        forbiddenExtsPath.grid(column=0, row=8, sticky='W')

        self.forbiddenExtsPathVariable = StringVar()
        self.entryForbiddenExtsPath = Entry(self, textvariable=self.forbiddenExtsPathVariable, width=30)
        self.entryForbiddenExtsPath.grid(column=1, row=8, sticky='W')

        buttonSearchForbiddenExts = Button(self, text=u"search", command=self.search_for_extension)
        buttonSearchForbiddenExts.grid(column=2, row=8, sticky="E")

        #filtering type
        self.filteringTypeVariable = StringVar()
        labelFilteringType = Label(self, text=u"Type", anchor="w")
        labelFilteringType.grid(column=0, row=9, sticky='W')

        self.filteringTypeComboBox = ttk.Combobox(self, textvariable=self.filteringTypeVariable)
        self.filteringTypeComboBox['values'] = ('filter in', 'filter out')
        self.filteringTypeComboBox.current(0)
        self.filteringTypeComboBox.grid(column=1, row=9, sticky='W')

        ##########################
        #empty label
        emptyLabel_ = Label(self, anchor="w")
        emptyLabel_.grid(column=0, row=10, sticky='WE')

        ##########################
        #Aliasing label
        labelAliasing = Label(self, text=u"Aliasing:", anchor="w")
        labelAliasing.grid(column=0, row=11, sticky='WE')

        #insert file for aliasing users
        aliasingUsersLabel = Label(self, text=u"Users", anchor="w")
        aliasingUsersLabel.grid(column=0, row=12, sticky='W')

        self.aliasingUsersPathVariable = StringVar()
        self.entryAliasingUsersPath = Entry(self, textvariable=self.aliasingUsersPathVariable, width=30)
        self.entryAliasingUsersPath.grid(column=1, row=12, sticky='W')

        buttonSearchAliasingUsers = Button(self, text=u"search", command=self.search_for_aliases)
        buttonSearchAliasingUsers.grid(column=2, row=12, sticky="E")

        ##########################
        #empty label
        emptyLabel = Label(self, anchor="w")
        emptyLabel.grid(column=0, row=13, sticky='WE')
        ##########################

        #detail level
        self.detailLevelVariable = StringVar()
        labelDetailLevel = Label(self, text=u"Detail Level", anchor="w")
        labelDetailLevel.grid(column=0, row=14, sticky='W')

        self.detailLevelComboBox = ttk.Combobox(self, textvariable=self.detailLevelVariable)
        self.detailLevelComboBox['values'] = ('line', 'file')
        self.detailLevelComboBox.current(0)
        self.detailLevelComboBox.grid(column=1, row=14, sticky='W')

        ##########################
        #empty label
        emptyLabel = Label(self, anchor="w")
        emptyLabel.grid(column=0, row=15, sticky='WE')
        ##########################

        #Finish button
        self.buttonFinish = Button(self, text=u"Export", command=self.launch_thread_execute)
        self.buttonFinish.grid(column=1, row=16, sticky="E")

        #Abort interrupt
        self.buttonAbort = Button(self, text=u"Abort", command=self.launch_thread_interrupt)
        self.buttonAbort.grid(column=2, row=16, sticky="E")
        self.buttonAbort.config(state=DISABLED)

        self.info_execution = StringVar()
        labelExecuting = Label(self, textvariable=self.info_execution, anchor="w")
        labelExecuting.grid(column=0, row=16, sticky='EW')

        self.resizable(False, False)

    def search_for_resource(self):
        f = askopenfilename(parent=self, title='Choose a file',
                            filetypes=[("Forbidden-resource files", "*.frs")])
        self.forbiddenResourcesPathVariable.set(f)

    def search_for_extension(self):
        f = askopenfilename(parent=self, title='Choose a file', filetypes=[("Forbidden-extension files", "*.fex")])
        self.forbiddenExtsPathVariable.set(f)

    def search_for_aliases(self):
        f = askopenfilename(parent=self, title='Choose a file', filetypes=[("User-alias files", "*.nal")])
        self.aliasingUsersPathVariable.set(f)

    def launch_thread_execute(self):
        self.info_execution.set("Executing...")
        self.buttonFinish.config(state=DISABLED)
        self.buttonAbort.config(state=NORMAL)
        self.thread_execute = threading.Thread(target=self.validator_export)
        self.thread_execute.daemon = True
        self.thread_execute.start()

    def launch_thread_interrupt(self):
        self.buttonFinish.config(state=DISABLED)
        self.buttonAbort.config(state=NORMAL)
        self.thread_interrupt = threading.Thread(target=self.interrupt)
        self.thread_interrupt.daemon = True
        self.thread_interrupt.start()
        self.thread_interrupt.join()

    def validator_export(self):
        flag = True

        if self.DBNameVariable.get() == "":
            self.DBNameVariable.set("cannot be empty!")
            flag = False
        else:
            self.DBNameVariable.set(re.sub(r'\W', '', self.DBNameVariable.get()).lower())

        if self.forbiddenExtsPathVariable.get() != "":
            if not self.check_path_existance(self.forbiddenExtsPathVariable.get()):
                self.forbiddenExtsPathVariable.set("not valid!")
                flag = False
            else:
                if not self.check_extension(self.forbiddenExtsPathVariable.get(), 'fex'):
                    self.forbiddenExtsPathVariable.set("not valid ext (.fex)!")
                    flag = False

        if self.aliasingUsersPathVariable.get() != "":
            if not self.check_path_existance(self.aliasingUsersPathVariable.get()):
                self.aliasingUsersPathVariable.set("not valid!")
                flag = False
            else:
                if not self.check_extension(self.aliasingUsersPathVariable.get(), 'nal'):
                    self.aliasingUsersPathVariable.set("not valid ext (.nal)!")
                    flag = False

        if flag:
            self.execute_export()
        else:
            self.info_execution.set("Validation errors")
            self.buttonFinish.config(state=NORMAL)
            self.buttonAbort.config(state=DISABLED)

    def interrupt(self):
        self.info_execution.set("Aborting...")
        sys.exc_clear()
        sys.exc_traceback = sys.last_traceback = None
        os._exit(-1)

    def check_extension(self, string, extension):
        flag = True
        ext = string.split('.')[-1]
        if ext != extension:
            flag = False
        return flag

    def check_path_existance(self, string):
        flag = True
        if not os.path.exists(string):
            flag = False
        return flag

    def execute_export(self):
        try:
            self.DBNAME = self.DBNameVariable.get()
            self.OUTPUT_JSON = DB2JSON_GUI.JSON_DIRECTORY_PATH + '/' + DB2JSON_GUI.JSON_FILE_NAME
            self.FORBIDDEN_RESOURCES_PATH = self.forbiddenResourcesPathVariable.get()
            self.FORBIDDEN_EXTENSION_PATH = self.forbiddenExtsPathVariable.get()
            self.USER_ALIASES_PATH = self.aliasingUsersPathVariable.get()
            if self.detailLevelVariable.get() == "line":
                 self.LINE_DETAILS = True
            else:
                self.LINE_DETAILS = False

            if self.filteringTypeVariable.get() == "filter in":
                self.FILTER = "in"
            else:
                self.FILTER = "out"

            g = Gitana(self.DBNAME)
            g.db2json(self.DBNAME, self.OUTPUT_JSON, self.LINE_DETAILS)

            if self.FORBIDDEN_RESOURCES_PATH != "" or self.FORBIDDEN_EXTENSION_PATH != "":
                self.OUTPUT_FILTERED_JSON = DB2JSON_GUI.JSON_DIRECTORY_PATH + '/' + DB2JSON_GUI.FILTERED + '.' + self.FILTER + '.' + DB2JSON_GUI.JSON_FILE_NAME
                g.filtering(self.OUTPUT_JSON,
                            self.OUTPUT_FILTERED_JSON,
                            self.FORBIDDEN_RESOURCES_PATH,
                            self.FORBIDDEN_EXTENSION_PATH,
                            self.FILTER)

            if self.USER_ALIASES_PATH != "":
                if self.OUTPUT_FILTERED_JSON:
                    self.OUTPUT_ALIASES_JSON = DB2JSON_GUI.JSON_DIRECTORY_PATH + '/' + DB2JSON_GUI.FILTERED + '.' + self.FILTER + '.' + DB2JSON_GUI.ALIASED + '.' + DB2JSON_GUI.JSON_FILE_NAME
                else:
                    self.OUTPUT_ALIASES_JSON = DB2JSON_GUI.JSON_DIRECTORY_PATH + '/' + DB2JSON_GUI.ALIASED + '.' + DB2JSON_GUI.JSON_FILE_NAME

                g.aliasing(self.OUTPUT_JSON,
                           self.OUTPUT_ALIASES_JSON,
                           self.USER_ALIASES_PATH)

            self.info_execution.set("Finished")
            self.buttonFinish.config(state=NORMAL)
            self.buttonAbort.config(state=DISABLED)
        except Exception as e:
            print traceback.format_exc()
            self.info_execution.set("Failed")
            self.buttonFinish.config(state=NORMAL)
            self.buttonAbort.config(state=DISABLED)

    def start_export(self):
        label = Label(self, text=id)
        label.pack(side="top", fill="both", padx=10, pady=10)


def main():
     DB2JSON_GUI()

if __name__ == "__main__":
     main()
