'''
Sergio Chairez
Maksym Sagadin
Front End GUI for movies_back.py
'''

import os
import sqlite3
from os import path
import sys
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as tkmb
import webbrowser

db = sqlite3.connect('movies.db')
cur = db.cursor()


# Additional code for running GUI application on Mac
# these modules and the code below will be covered in module 4
def gui2fg():
    """Brings tkinter GUI to foreground on Mac
       Call gui2fg() after creating main window and before mainloop() start
    """
    if sys.platform == 'darwin':
        tmpl = 'tell application "System Events" to set frontmost of every process whose unix id is %d to true'
        os.system("/usr/bin/osascript -e '%s'" % (tmpl % os.getpid()))

class MainWin(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Current Movies')

        self.container = tk.Frame(self)
        choice_label = tk.Label(background='blue',
                                text='Find current movie',
                                fg='white',
                                font=('Helvetica', 16)).grid()

        self.buttons()
        self.protocol("WM_DELETE_WINDOW", self.on_exit)

    def buttons(self):
        '''
        This function creates the buttons for the Main Window
        '''
        buttons_frame = tk.Frame(self)
        buttons_frame.grid(
            row=0, column=1, sticky='nsew', padx=10, pady=10)
        buttons_frame.columnconfigure(0, weight=0)
        buttons_frame.columnconfigure(1, weight=0)
        buttons_frame.columnconfigure(2, weight=0)

        self.by_name_button = tk.Button(
            buttons_frame, text='By Name',
            command=self._movie_by_name)
        self.by_name_button.grid(
            row=0, column=1, sticky='ew', padx=15, pady=10)

        self.by_genre_button = tk.Button(
            buttons_frame, text='By Genre', command=self._genre_by_name)

        self.by_genre_button.grid(
            row=0, column=2, sticky='ew', padx=15, pady=10)

        self.but_about = tk.Button(buttons_frame, text="About",
                                   command=self._about_info)
        self.but_about.grid(
            row=0, column=3, sticky='ew', padx=15, pady=10)

    # button1 logic
    def _movie_by_name(self):
        '''
        This function calls the dialog window to search by movies and if a choice
        is selected then it opens the URL link
        '''
        dialWin = DialogWin(self, searchby='movie')
        self.wait_window(dialWin)

        choice = dialWin.get_choice_movie()
        # print(choice)
        if choice != "":
            link_str = f"SELECT m.link FROM movies_table m WHERE m.name LIKE '%{choice}%'"
            link_result = cur.execute(link_str).fetchone()[0]
            # print(link_result)
            webbrowser.open(link_result)

    # button2 logic
    def _genre_by_name(self):
        '''
        This function calls the dialog window to search by genres and when a choice
        is selected it shows all the movies containing that genre
        '''
        capture_genre_titles = cur.execute(
            "SELECT (genre) FROM genres_table ORDER BY genre").fetchall()
        dialWin = DialogWin(
            self, genres=capture_genre_titles, searchby='genre')
        self.wait_window(dialWin)
        choice = dialWin.get_choice_genre()
        if choice != "":
            capture_movies_w_genre_choice_str = '''
            SELECT
                m.name, m.rating, m.length, g0.genre AS "genre0", g1.genre AS "genre1", 
                g2.genre AS "genre2", g3.genre AS "genre3", g4.genre AS "genre4"
            FROM movies_table m
                LEFT JOIN genres_table g0 ON g0.genre_id = m.genre0
                LEFT JOIN genres_table g1 ON g1.genre_id = m.genre1
                LEFT JOIN genres_table g2 ON g2.genre_id = m.genre2
                LEFT JOIN genres_table g3 ON g3.genre_id = m.genre3
                LEFT JOIN genres_table g4 ON g4.genre_id = m.genre4
            '''
            capture_movies_w_genre_choice_str += f" WHERE g0.genre = '{choice}'"
            for i in range(1, 5):
                capture_movies_w_genre_choice_str += f" OR g{i}.genre = '{choice}'"
                i += 1

            vals = cur.execute(capture_movies_w_genre_choice_str).fetchall()
            # to get genre choice in the title of DisplayWin later on
            vals.append(choice)
            displayWin = DisplayWin(self, *vals)

    # button3 logic
    def _about_info(self):
        ''' This function shows the creators info '''
        credits = "Credits:\nSergio Chairez\nMaksym Sagadin"
        tkmb.showinfo("Credits", credits)

    def on_exit(self):
        '''
        This function opens a message box asking if the user wants to quit
        Then quits out of the program if the user clicks yes
        '''
        if tkmb.askyesno("Exit", "Do you want to quit the application?"):
            self.quit()
            db.close()

class DisplayWin(tk.Toplevel):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master)
        self.title(f'Genre: {args[-1]}')

        self.displayFrame = tk.Frame(self)
        self.displayFrame.grid(
            row=16, column=0, sticky='nsew', padx=10, pady=20)

        self.listbox = tk.Listbox(
            self.displayFrame, selectmode=tk.SINGLE, width=60, height=12)
        # listbox.grid(height=12)
        # listbox.config(width=0)

        self._genres_list_for_movie = []
        for elems in range(len(args) - 1):
            self.listbox.insert(
                tk.END, f'{args[elems][0]} rating: {args[elems][1]} length: {args[elems][2]} min')
            self._genres_list_for_movie.append(args[elems][3:])
    
        self.listbox.pack(anchor=tk.W)

        self.listbox.bind('<<ListboxSelect>>', self.printout)
        label1 = tk.Label(self.displayFrame,
                          text="Click on a movie to see all its genres").pack()

        self.output = tk.StringVar()
        tk.Label(self.displayFrame, textvariable=self.output).pack()

    def printout(self, event):
        '''
        This function prints out the genre(s) from the selected movie
        in the list box
        '''
        idx = int(self.listbox.curselection()[0])
        genres = self._genres_list_for_movie[idx]
        str1 = ""
        for g in genres:
            if g is not None:
                str1 += ' ' + str(g) + ', '
        # str1 = str1[:-2]
        # print(str1)
        self.output.set("genres: " + str1[:-2])

class DialogWin(tk.Toplevel):
    def __init__(self, master, genres=None, searchby=None):
        super().__init__(master)
        self.focus_set()
        self.grab_set()
        self.transient(master)
        self.geometry("300x500")
        self.title('Make a Choice')
        self._master = master
        if searchby == 'movie':
            self.movie_options(master)

        elif searchby == 'genre':
            self.genre_options(master, genres)
        else:
            raise ValueError("The searchby value is incorrect")

    def movie_options(self, master):
        '''
        This function triggers when the user selects the search by movie button
        It will populate the movies as radio buttons that the user can choose the movies
        '''
        self.movies_options_frame = tk.Frame(self)
        self.movies_options_frame.grid(
            row=16, column=0, sticky='nsew', padx=10, pady=20)

        self.movie_choice = tk.StringVar()

        capture_movie_titles = cur.execute(
            "SELECT (name) FROM movies_table ORDER BY name").fetchall()

        self.movie_choice.set(capture_movie_titles[0][0])
        for val in capture_movie_titles:
            tk.Radiobutton(self.movies_options_frame,
                           text=val[0], padx=20, variable=self.movie_choice, value=val[0]).pack(anchor=tk.W)

        self.saveButton = tk.Button(self, text='SAVE',
                                    command=self.get_choice_movie).grid()

        self.grab_set()
        self.focus_set()
        self.protocol("WM_DELETE_WINDOW", self._close_movie)
        self.transient(master)

    def _close_movie(self):
        '''
        This function will reset the user choice and close the window
        if the user clicks the X
        '''
        self.movie_choice.set("")
        self.destroy()

    def get_choice_movie(self):
        ''' 
        This function is called when the user clicks the SAVE button
        it will close the window and return the choice
        '''
        self.destroy()
        return self.movie_choice.get()

    def genre_options(self, master, genres):
        '''
        This function triggers when the user selects the search by genre button
        It will populate the genres as radio buttons, that the user can choose the genre
        '''
        self.genre_options_frame = tk.Frame(self)
        self.genre_options_frame.grid(
            row=16, column=0, sticky='nsew', padx=10, pady=20)

        self.genre_choice = tk.StringVar()

        self.genre_choice.set(genres[0][0])
        # print(genres)
        for val in genres:
            tk.Radiobutton(self.genre_options_frame,
                           text=val[0], padx=20, variable=self.genre_choice, value=val[0]).pack(anchor=tk.W)

        self.saveButton = tk.Button(self, text='SAVE',
                                    command=self.get_choice_genre).grid()

        self.grab_set()
        self.focus_set()
        self.protocol("WM_DELETE_WINDOW", self._close_genre)
        self.transient(master)

    def get_choice_genre(self):
        ''' 
        This function is called when the user clicks the SAVE button
        it will close the window and return the choice
        '''
        self.destroy()
        return self.genre_choice.get()

    def _close_genre(self):
        '''
        This function will reset the user choice and close the window
        if the user clicks the X
        '''
        self.genre_choice.set("")
        self.destroy()


app = MainWin()
app.mainloop()
