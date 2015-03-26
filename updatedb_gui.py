__author__ = 'atlanmod'

from Tkinter import *
from tkFileDialog import *
import threading
import os
import re
from gitana import Gitana
import traceback

class UpdateDB_GUI(Tk):

    def __init__(self):
        Tk.__init__(self)
        self.initialize()
        self.title("Update DB")
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

        #insert db schema
        labelDBName = Label(self, text=u"DB name", anchor="w")
        labelDBName.grid(column=0, row=3, sticky='W')

        self.DBNameVariable = StringVar()
        self.entryDBName = Entry(self, textvariable=self.DBNameVariable, width=30)
        self.entryDBName.grid(column=1, row=3, sticky='W')

        #insert before date
        labelBeforeDate = Label(self, text=u"Before date (YYYY-mm-dd)", anchor="w")
        labelBeforeDate.grid(column=0, row=4, sticky='W')

        self.beforeDateVariable = StringVar()
        self.beforeDate = Entry(self, textvariable=self.beforeDateVariable, width=30)
        self.beforeDate.grid(column=1, row=4, sticky='W')

        ##########################
        #empty label
        emptyLabel = Label(self, anchor="w")
        emptyLabel.grid(column=0, row=5, sticky='WE')
        ##########################

        #Finish button
        self.buttonFinish = Button(self, text=u"Update", command=self.launch_thread_execute)
        self.buttonFinish.grid(column=1, row=6, sticky="E")

        #Abort interrupt
        self.buttonAbort = Button(self, text=u"Abort", command=self.launch_thread_interrupt)
        self.buttonAbort.grid(column=2, row=6, sticky="E")
        self.buttonAbort.config(state=DISABLED)

        self.info_execution = StringVar()
        labelExecuting = Label(self, textvariable=self.info_execution, anchor="w")
        labelExecuting.grid(column=0, row=6, sticky='EW')

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
            self.repoPathVariable.set("path cannot be empty!")
            flag = False
        else:
            if not self.check_path_existance(self.repoPathVariable.get()):
                self.repoPathVariable.set("not valid path!")
                flag = False

        if self.DBNameVariable.get() == "":
            self.DBNameVariable.set("cannot be empty!")
            flag = False
        else:
            self.DBNameVariable.set(re.sub(r'\W', '', self.DBNameVariable.get()).lower())

        if flag:
            self.execute_update()

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

    def execute_update(self):
        try:
            self.REPO_PATH = self.repoPathVariable.get()
            self.DBNAME = self.DBNameVariable.get()
            g = Gitana(self.DBNAME)
            g.updatedb(self.DBNAME, self.REPO_PATH)

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
     UpdateDB_GUI()

if __name__ == "__main__":
     main()
