__author__ = 'atlanmod'

from Tkinter import *
from PIL import ImageTk, Image
import subprocess


class GUI(Tk):

    def __init__(self):
        Tk.__init__(self)

        self.initialize()
        self.title("Gitana")
        self.mainloop()

    def initialize(self):
        img = ImageTk.PhotoImage(Image.open("gitana_img.png"))
        labelImg = Label(image=img)
        labelImg.image = img
        labelImg.grid(row=2, columnspan=3, rowspan=10, sticky='WE')

        ##########################
        #import to db label
        self.importButton = Button(self, text=u"Import Git to DB", command=self.start_import, width=15)
        self.importButton.grid(column=0, row=13)

        #update db
        self.updateButton = Button(self, text=u"Update DB", command=self.start_update, width=15)
        self.updateButton.grid(column=1, row=13)

        #export to JSON
        self.exportButton = Button(self, text=u"Export DB to JSON", command=self.start_export, width=15)
        self.exportButton.grid(column=2, row=13)

        self.grid_columnconfigure(0, weight=1)
        self.resizable(False, False)

    def start_import(self):
        proc = subprocess.Popen({sys.executable, "git2db_gui.py"})
        proc.communicate()

    def start_update(self):
        proc = subprocess.Popen({sys.executable, "updatedb_gui.py"})
        proc.communicate()

    def start_export(self):
        proc = subprocess.Popen({sys.executable, "db2json_gui.py"})
        proc.communicate()


def main():
    GUI()

if __name__ == "__main__":
    main()
