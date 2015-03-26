__author__ = 'atlanmod'

from Tkinter import *
from tkFileDialog import *
import threading
import os
import re
from gitana import Gitana
import traceback

class Git2DB_GUI(Tk):

    def __init__(self):
        Tk.__init__(self)
        self.initialize()
        self.title("Import DB")
        self.mainloop()

    def initialize(self):
        ##########################
        #empty label
        emptyLabel = Label(self, anchor="w")
        emptyLabel.grid(column=0, row=1, sticky='WE')
        ##########################

        #select repo
        labelRepoPath = Label(self, text=u"Repo path", anchor="w")
        labelRepoPath.grid(column=0, row=2, sticky='W')

        self.repoPathVariable = StringVar()
        self.entryRepoPath = Entry(self, textvariable=self.repoPathVariable, width=30)
        self.entryRepoPath.grid(column=1, row=2, sticky='W')

        buttonSearchRepo = Button(self, text=u"search", command=self.search_for_directory)
        buttonSearchRepo.grid(column=2, row=2, sticky="E")

        #insert repo name
        labelRepoName = Label(self, text=u"Name", anchor="w")
        labelRepoName.grid(column=0, row=3, sticky='W')

        self.repoNameVariable = StringVar()
        self.entryRepoName = Entry(self, textvariable=self.repoNameVariable, width=30)
        self.entryRepoName.grid(column=1, row=3, sticky='W')

        #insert repo owner
        labelRepoOwner = Label(self, text=u"Owner", anchor="w")
        labelRepoOwner.grid(column=0, row=4, sticky='W')

        self.repoOwnerVariable = StringVar()
        self.entryRepoOwner = Entry(self, textvariable=self.repoOwnerVariable, width=30)
        self.entryRepoOwner.grid(column=1, row=4, sticky='W')

        #insert before date
        labelBeforeDate = Label(self, text=u"Before date (YYYY-mm-dd)", anchor="w")
        labelBeforeDate.grid(column=0, row=5, sticky='W')

        self.beforeDateVariable = StringVar()
        self.beforeDate = Entry(self, textvariable=self.beforeDateVariable, width=30)
        self.beforeDate.grid(column=1, row=5, sticky='W')

        ##########################
        #empty label
        emptyLabel = Label(self, anchor="w")
        emptyLabel.grid(column=0, row=6, sticky='WE')
        ##########################

        #Finish button
        self.buttonFinish = Button(self, text=u"Import", command=self.launch_thread_execute)
        self.buttonFinish.grid(column=1, row=7, sticky="E")

        #Abort interrupt
        self.buttonAbort = Button(self, text=u"Abort", command=self.launch_thread_interrupt)
        self.buttonAbort.grid(column=2, row=7, sticky="E")
        self.buttonAbort.config(state=DISABLED)

        self.info_execution = StringVar()
        labelExecuting = Label(self, textvariable=self.info_execution, anchor="w")
        labelExecuting.grid(column=0, row=7, sticky='EW')

        self.resizable(False, False)

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

    def launch_thread_execute(self):
        self.info_execution.set("Executing...")
        self.buttonFinish.config(state=DISABLED)
        self.buttonAbort.config(state=NORMAL)
        self.thread_execute = threading.Thread(target=self.validator_import)
        self.thread_execute.daemon = True
        self.thread_execute.start()

    def launch_thread_interrupt(self):
        self.buttonFinish.config(state=DISABLED)
        self.buttonAbort.config(state=NORMAL)
        self.thread_interrupt = threading.Thread(target=self.interrupt)
        self.thread_interrupt.daemon = True
        self.thread_interrupt.start()
        self.thread_interrupt.join()

    def validator_import(self):
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

        if flag:
            self.execute_import()

    def interrupt(self):
        self.info_execution.set("Aborting...")
        sys.exc_clear()
        sys.exc_traceback = sys.last_traceback = None
        os._exit(-1)

    def check_path_existance(self, string):
        flag = True
        if not os.path.exists(string):
            flag = False
        return flag

    def execute_import(self):
        try:
            self.REPO_PATH = self.repoPathVariable.get()
            self.REPO_NAME = self.repoNameVariable.get()
            self.REPO_OWNER = self.repoOwnerVariable.get()
            self.BEFORE_DATE = None
            if self.beforeDateVariable.get() != '':
                self.BEFORE_DATE = self.beforeDateVariable.get()
            schema = self.REPO_OWNER + "_" + self.REPO_NAME
            g = Gitana(schema)
            g.init_dbschema(schema)
            g.git2db_before_date(schema, self.REPO_PATH, self.BEFORE_DATE)

            self.info_execution.set("Finished")
            self.buttonFinish.config(state=NORMAL)
            self.buttonAbort.config(state=DISABLED)
        except:
            print traceback.format_exc()
            self.info_execution.set("Failed")
            self.buttonFinish.config(state=NORMAL)
            self.buttonAbort.config(state=DISABLED)

    def start_export(self):
        label = Label(self, text=id)
        label.pack(side="top", fill="both", padx=10, pady=10)


def main():
     Git2DB_GUI()

if __name__ == "__main__":
     main()
