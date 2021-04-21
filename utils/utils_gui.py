"""
@author: Fotios Lygerakis
@UTA ID: 1001774373
"""
import PySimpleGUI as sg

"""
The layout for server and client guis
"""
server_layout = [[sg.Output(size=(60, 20))],
                 [sg.Button('Go'), sg.Button('Client List'), sg.Button('Exit')]]

backup_layout = [[sg.Output(size=(60, 20))],
                 [sg.Button('Go'), sg.Button('Client List'), sg.Button('Exit')]]

client_layout = [[sg.Text('Please enter username')],
                 [sg.Text("Username", size=(15, 1)), sg.InputText(), sg.Button("Login")],
                 [sg.Text("File Name", size=(15, 1)), sg.InputText("mytext.txt"), sg.Button("Send Text")],
                 [sg.Output(size=(60, 20))],
                 [sg.Text("Lexicon Addition", size=(15, 1)), sg.InputText(do_not_clear=False), sg.Button("Add")],
                 [sg.Button('Exit')]]

