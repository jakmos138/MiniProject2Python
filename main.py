import os
import sys
import time
import sqlite3
import requests
import json
import webbrowser
import re
from tkinter import *
from tkinter import ttk
from urllib.parse import urlparse
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


jsonUrl = "https://raw.githubusercontent.com/algolia/datasets/master/recipes/recipes.json"
darkColor = "gray20"
lightColor = "snow2"


def filePath(imgName):
    return os.path.join(os.path.dirname(__file__), imgName)


def connectToDatabase():
    return sqlite3.connect(":memory:")


def downloadAndStoreData(url, db, root):
    cursor = db.cursor()
    # check if table exist

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", ("Recipes",))
    if cursor.fetchone() != None:
        widget = root.nametowidget("bottomF").nametowidget("statusLine")
        widget.config(text = "Status: Cannot fetch data. The database already Exist")
        #TODO Inform User
        return

    startTime = time.time()
    try:
        jsonData = requests.get(url).content
        parsed_url = urlparse(url)
        filename = str(os.path.basename(parsed_url.path))
    except:
        widget = root.nametowidget("bottomF").nametowidget("statusLine")
        widget.config(text = "Status: Cannot fetch data. The network error.")
        

    jsonData = json.loads(jsonData)
    print(len(jsonData))
    cursor.execute('''CREATE TABLE Recipes (
                   Name text,
                   Servings int,
                   Rating float,
                   Url text
        )''')
    for item in jsonData:
        cursor.execute('''
                       INSERT INTO Recipes (Name, Servings, Rating, Url) VALUES (?, ?, ?, ?)
                       ''', (item['recipe_name'], item["servings"], item["rating"], item["url"]) )
    
    db.commit()
    widget = root.nametowidget("bottomF").nametowidget("statusLine")
    widget.config(text = "Status: Fetched data. It took {:.4f} seconds.".format(time.time() - startTime))
    widget = root.nametowidget("infoF").nametowidget("titleLabel")
    widget.config(text = filename)
    

def clearData(db, root):
    startTime = time.time()
    cursor = db.cursor()
    try:
        cursor.execute("DROP Table Recipes")
    except sqlite3.OperationalError:
        widget = root.nametowidget("bottomF").nametowidget("statusLine")
        widget.config(text = "Status: No database to clear.")
    db.commit()
    widget = root.nametowidget("bottomF").nametowidget("statusLine")
    widget.config(text = "Status: Cleared data. It took {:.4f} seconds.".format(time.time() - startTime))
    widget = root.nametowidget("bottomF").nametowidget("aggregationLabel")
    widget.config(text = "")
    widget = root.nametowidget("infoF").nametowidget("titleLabel")
    widget.config(text = "No file loaded")
    if root.getvar(name = "displayChosen") != 0:
        widget = root.nametowidget("mainF").nametowidget("display")
        widget.pack_forget()
    root.setvar(name = "displayChosen", value = 0)
    print(root.getvar(name = "displayChosen"))


def printDatabase(db, root):
    cursor = db.cursor()
    try:
        cursor.execute("SELECT * from Recipes")
    except sqlite3.OperationalError:
        return
    print(*cursor.fetchall(), sep = "\n")


def averageAggregation(db, root, column):
    startTime = time.time()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT AVG(" + column + ") from Recipes")
    except sqlite3.OperationalError:
        widget = root.nametowidget("bottomF").nametowidget("statusLine")
        widget.config(text = "Status: Can't aggregate data. No database present.")
        return
    widget = root.nametowidget("bottomF").nametowidget("aggregationLabel")
    average = cursor.fetchone()[0]
    widget.config(text = "Average value of " + column + " column is {:.2f}.".format(average))
    widget = root.nametowidget("bottomF").nametowidget("statusLine")
    widget.config(text = "Status: Aggregation done. It took {:.4f} seconds.".format(time.time() - startTime))


def displayDataInTable(db, root):
    startTime = time.time()
    cursor = db.cursor()
    if root.getvar(name = "displayChosen") == 1:
        widget = root.nametowidget("bottomF").nametowidget("statusLine")
        widget.config(text = "Status: Can't display table. The table is already present.")
        return

    try:
        cursor.execute("SELECT * from Recipes")
    except sqlite3.OperationalError:
        widget = root.nametowidget("bottomF").nametowidget("statusLine")
        widget.config(text = "Status: Can't display table. No database present.")
        return
    root.setvar(name = "displayChosen", value = 1)

    container = Frame(root.nametowidget("mainF"), name = "display")
    container.pack(fill='both', expand=True)
    table = ttk.Treeview(container, columns=("Name", "Servings", "Rating", "Url"), show='headings')
    
    table.heading("Name", text="Name")
    table.heading("Servings", text="Servings")
    table.heading("Rating", text="Rating")
    table.heading("Url", text = "Url")

    widget = root.nametowidget("bottomF").nametowidget("statusLine")
    widget.config(text = "Status: Table displayed. It took {:.4f} seconds.".format(time.time() - startTime))
    
    table.column("Servings", width=60, anchor=CENTER)
    table.column("Rating", width=60, anchor=CENTER)

    for items in cursor.fetchall():
        table.insert("", "end", values = items)

    scrollbar = ttk.Scrollbar(container, orient=VERTICAL, command=table.yview)
    table.configure(yscroll=scrollbar.set)
    scrollbar.pack(side=RIGHT, fill=Y)
        
    table.pack()
    
    
    def onUrlClick(event):
        item_id = table.identify_row(event.y)
        if item_id:
            values = table.item(item_id, "values")
            url = values[3]
            webbrowser.open(url)

    table.bind("<Button-1>", onUrlClick)
    table.pack(fill = "both", expand = True)
    

def displayGraphOfRatings(db, root):
    startTime = time.time()
    cursor = db.cursor()
    if root.getvar(name = "displayChosen") == 2:
        widget = root.nametowidget("bottomF").nametowidget("statusLine")
        widget.config(text = "Status: Can't display graph. The graph is already present.")
        return

    try:
        cursor.execute("SELECT Rating from Recipes")
    except sqlite3.OperationalError:
        widget = root.nametowidget("bottomF").nametowidget("statusLine")
        widget.config(text = "Status: Can't display graph. No database present.")
        return
    root.setvar(name = "displayChosen", value = 2)
    rangesDict = {
    '0.0-0.5': 0,
    '0.5-1.0': 0,
    '1.1-1.6': 0,
    '1.6-2.0': 0,
    '2.1-2.6': 0,
    '2.6-3.0': 0,
    '3.1-3.6': 0,
    '3.6-4.0': 0,
    '4.1-4.6': 0,
    '4.6-5.0': 0
    }
    def stringToRange(rangeString, value):
        rangeMatch = re.search(r"(\d+.\d+)-(\d+.\d+)", rangeString)
        if rangeMatch:
            return float(rangeMatch.group(1)) <  value < float(rangeMatch.group(2)) + 0.05
        return False

    for rating in cursor.fetchall():
        for sizeRange in rangesDict.keys():
            if stringToRange(sizeRange, rating[0]):
                rangesDict[sizeRange] += 1
    fig = plt.figure(figsize=(10,6))
    ax = fig.add_subplot(111)
    ax.bar(list(rangesDict.keys()), list(rangesDict.values()))
    ax.set_xlabel("Rating")
    ax.set_ylabel("Count")
    ax.set_title("Distribution of Ratings")
    ax.tick_params(axis='x', labelsize=6)
    container = Frame(root.nametowidget("mainF"), name = "display" )
    container.pack()
    canvas = FigureCanvasTkAgg(fig, master = container)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=BOTH, expand=True)
    widget = root.nametowidget("bottomF").nametowidget("statusLine")
    widget.config(text = "Status: Graph displayed. It took {:.4f} seconds.".format(time.time() - startTime))
    # clean up
    def onClose():
        canvas.get_tk_widget().destroy()
        fig.clear()
        db.close()
        root.quit()
    root.protocol("WM_DELETE_WINDOW", onClose)

    




def changeWidgetOptions(widget, options, widgetType=None):
    for child in widget.winfo_children():
        if widgetType == None or isinstance(child, widgetType):
            try:
                child.config(**options)
            except TclError:
                pass
        changeWidgetOptions(child, options)


def darkMode(root, enable):
    enable = enable.get()
    if enable:
        rootCol, backCol, fontCol = darkColor, "grey30", "khaki1"
    else:
        rootCol, backCol, fontCol = lightColor, "grey80", "black"
    
    root.configure(background = rootCol)
    changeWidgetOptions(root, {"bg": backCol, "fg": fontCol}, Menu)
    changeWidgetOptions(root, {"bg": rootCol, "highlightbackground": fontCol}, Frame)
    changeWidgetOptions(root, {"bg": backCol, "fg": fontCol}, Button)
    changeWidgetOptions(root, {"bg": backCol, "fg": fontCol}, Label)
    changeWidgetOptions(root, {"bg": backCol}, Checkbutton)
    style = ttk.Style()
    style.configure("Treeview", background = backCol, foreground = fontCol)
    style.configure("Treeview.Heading", background = rootCol)




def run():
    # root configuration
    root = Tk()
    root.title("Mini Project 2")
    root.geometry("600x600")

    db = connectToDatabase()

    # menu configuration
    menu = Menu(root)
    root.config(menu=menu)
    options = Menu(menu)
    menu.add_cascade(label='Options', menu=options)
    options.add_command(label='Fetch Data', command = lambda: downloadAndStoreData(jsonUrl, db, root))
    options.add_command(label='Clear Data', command = lambda: clearData(db, root))
    options.add_command(label="Print Data", command = lambda: printDatabase(db, root))
    var = IntVar()
    options.add_checkbutton(label = "Dark Mode", variable = var, onvalue = 1, offvalue = 0, command = lambda: darkMode(root, var))
    options.add_separator()
    options.add_command(label='Exit', command=root.quit)
    
    # frames setup
    root.grid_rowconfigure(0, weight=1) 
    root.grid_rowconfigure(1, weight=7)
    root.grid_rowconfigure(2, weight=2)
    root.grid_columnconfigure(0, weight=5)
    root.grid_columnconfigure(1, weight=1)
    infoFrame = Frame(root, highlightbackground="black", highlightthickness=1, name = "infoF")
    buttonsFrame = Frame(root, highlightbackground="black", highlightthickness=1, name = "buttonsF")
    bottomFrame = Frame(root, highlightbackground="black", highlightthickness=1, name = "bottomF")
    mainFrame = Frame(root, highlightbackground="black", highlightthickness=1, name = "mainF")

    infoFrame.grid(column=0, row=0, columnspan=2, sticky='nsew')
    mainFrame.grid(column=0, row=1, sticky='nsew')
    buttonsFrame.grid(column=1, row=1, sticky='nsew')  
    bottomFrame.grid(column=0, row=2, columnspan=2, sticky='nsew')

    infoFrame.pack_propagate(False)
    buttonsFrame.pack_propagate(False)
    bottomFrame.pack_propagate(False)
    mainFrame.pack_propagate(False)
    
    # info frame
    titleLabel = Label(infoFrame, text = "", name = "titleLabel")
    titleLabel.pack(pady = 10)

    # bottom frame
    aggrLabel = Label(bottomFrame, text = "", name = "aggregationLabel")
    aggrLabel.pack(pady = 10)

    statusLine = Label(bottomFrame, text = "Status: ", name = "statusLine")
    statusLine.pack(pady = 10)

    # button frame
    avgRatingButton = Button(buttonsFrame, text = "Average of\n Rating Column", command = lambda: averageAggregation(db, root, "Rating"))
    avgRatingButton.pack(pady = 10)
    avgServingsButton = Button(buttonsFrame, text = "Average of\n Servings Column", command = lambda: averageAggregation(db, root, "Servings"))
    avgServingsButton.pack(pady = 10)
    displayChosen = IntVar(root, name = "displayChosen")
    displayTableButton = Button(buttonsFrame, text = "Display Table", command = lambda: displayDataInTable(db, root))
    displayTableButton.pack(pady = 10)
    displayGraphButton = Button(buttonsFrame, text = "Display Graph\n of Ratings", command = lambda: displayGraphOfRatings(db, root))
    displayGraphButton.pack(pady = 10)
    
    # main frame
    

   

    # final setup
    downloadAndStoreData(jsonUrl, db, root)
    darkMode(root, var)
    root.mainloop()
    db.close()
    print("end")


if __name__ == "__main__":
    run()