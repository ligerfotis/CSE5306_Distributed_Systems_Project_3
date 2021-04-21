"""
@author: Fotios Lygerakis
@UTA ID: 1001774373
"""
import socket
import threading
import PySimpleGUI as sg

from back_up_server import BackUpServer
from client import Client
from config import IP, PORT
from utils.utils_gui import server_layout, client_layout, backup_layout
from server import Server

"""
Code based on https://pysimplegui.readthedocs.io/en/latest/cookbook/
"""


class GUI:
    def __init__(self, name):
        """
        Init method
        :param name: the name of the user (server or client)
        """
        self.server, self.client, self.backup = None, None, None
        # helper variables
        if name == "Client":
            self.is_client = True
            self.is_server = False
            self.is_backup = False
        elif name == "Server":
            self.is_client = False
            self.is_server = True
            self.is_backup = False
        # backup server
        else:
            self.is_client = False
            self.is_server = False
            self.is_backup = True

        # chose the appropriate layout for the server and the client
        if self.is_server:
            self.layout = server_layout
            self.server = Server()
        elif self.is_client:
            self.layout = client_layout
            self.client = Client()
        elif self.is_backup:
            self.layout = backup_layout
            self.backup = BackUpServer()
        self.logged_in = False

        # create a window
        self.window = sg.Window(name, self.layout)

    def run(self):
        """
        Function for handling the GUI
        """
        while True:
            # read the events on the gui and their values
            event, values = self.window.read()
            # exit gui when window is closed or Exit button is pressed
            if event == sg.WIN_CLOSED or event == 'Exit':
                # close up sockets
                if self.is_server:
                    try:
                        self.server.socket.shutdown(socket.SHUT_RD)
                        self.server.socket.close()
                    except:
                        print("server shut down")
                        break
                elif self.is_backup:
                    try:
                        self.backup.socket.shutdown(socket.SHUT_RD)
                        self.backup.socket.close()
                    except:
                        print("server shut down")
                        break
                else:
                    self.client.socket.shutdown(socket.SHUT_RD)
                break

            # Client's gui
            if self.is_client:
                # on submit button take the username that has been entered
                if event == 'Login' and not self.logged_in:
                    # try to log in with the given username
                    print("Trying to log in: {}".format(values[0]))
                    self.logged_in = self.client.set_up_connection(IP, PORT, values[0])
                    # not logged in
                    if not self.logged_in:
                        print("Could not login")
                        print("Username already taken.\nPlease use another one.")
                    else:
                        print('You are logged in!')
                        # start the main thread of the client as a thread
                        thread = threading.Thread(target=self.client.main)
                        thread.start()
                # if logged in
                if self.logged_in:
                    # "Send Text" is pressed
                    if event == "Send Text":
                        # changes the clients variable, so that to turn on the file exchange with the server
                        self.client.send_file_to_server = True
                        # pass on the filename given by the gui to the client thread
                        self.client.filename = values[1]
                    # "Add" button is pressed
                    elif event == "Add":
                        # add entry from gui to the client's thread queue
                        self.client.add_to_queue(values[2])
            # Server's gui
            elif self.is_server or self.is_backup:
                # start a thread for the server when the Go button is pressed
                if event == 'Go':
                    # deactivate Go button
                    self.window.FindElement('Go').Update(disabled=True)
                    main = self.server.main if self.is_server else self.backup.main
                    thread = threading.Thread(target=main)
                    thread.start()
                # when "Client List" button is pressed the online usernames are being printed on the gui
                elif event == 'Client List':
                    if self.is_server:
                        print("Client List Online: {}".format(self.server.get_live_usernames()))
                    elif self.is_backup:
                        print("Client List Online: {}".format(self.backup.get_live_usernames()))
                # otherwise print the values in the gui
                else:
                    print(values)
        self.window.close()
