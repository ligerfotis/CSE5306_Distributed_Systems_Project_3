"""
@author: Fotios Lygerakis
@UTA ID: 1001774373
"""
import os
import queue
import select

from config import HEADER_LENGTH, IP, PORT_BackUp
from utils.utils import send_msg, receive_file, save_file, set_up_username



"""
Code based on https://pythonprogramming.net/client-chatroom-sockets-tutorial-python-3/
"""


class Client:
    def __init__(self):
        self.send_file_to_server = False

        # the username and connection socket
        self.username, self.socket = [None, None]

        # the name of the file to send to the server for checking
        self.filename = None

        # the text retrieved from the file in string format
        self.text_string = None

        # the queue to store the lexicon additions
        self.q = queue.Queue()

    def set_up_connection(self, ip, port, username):
        """
        Sets up connection and username
        :param username: username for this client
        :return: True if connection succeeded and username has been established, False otherwise
        """
        try:
            # set up the connection and establish a username to the server
            response = set_up_username(ip, port, username, HEADER_LENGTH)
            if response is not None:
                self.username, self.socket = response
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False

    def main(self):
        """
        Main functionality of the client
        """
        while True:
            # check for polling demand

            read_sockets, _, exception_sockets = select.select([self.socket], [], [self.socket], 0.5)
            # Iterate over notified sockets
            for notified_socket in read_sockets:
                # If notified socket is a server socket - new connection, accept it
                if notified_socket == self.socket:
                    # Receive message
                    message = receive_file(notified_socket, header_length=HEADER_LENGTH)
                    # If False, client disconnected, cleanup
                    if message is False:
                        print("Server Crashed!")
                        self.connect_to_backup()
                        break
                    message = message["data"].decode()
                    if message == "poll":
                        print("A poll is received from the server...")
                        while not self.q.empty():
                            word = self.q.get()
                            send_msg(self.socket, word, HEADER_LENGTH)
                            print("The word \'{}\' was retrieved by the server.".format(word))
                        send_msg(self.socket, "poll_end", HEADER_LENGTH)

            if self.send_file_to_server:
                response = self.send_file()
                # in case file requested does not exist
                if not response:
                    self.send_file_to_server = False
                    continue
                print("Successfully uploaded file to the server.")
                read_sockets, _, exception_sockets = select.select([self.socket], [], [self.socket])
                # Iterate over notified sockets
                for notified_socket in read_sockets:
                    # If notified socket is a server socket - new connection, accept it
                    if notified_socket == self.socket:
                        # Receive message
                        message = receive_file(notified_socket, header_length=HEADER_LENGTH)

                        # If False, client disconnected, cleanup
                        if message is False:
                            if message is False:
                                print("Server Crashed!")
                                self.connect_to_backup()
                                break
                        message = message["data"].decode()
                        path = "client_files/"
                        filename = "annotated_{}_{}.txt".format(self.filename, self.username)
                        save_file(message, path, filename)
                        print("The spell check sequence has been completed.")
                        self.send_file_to_server = False

    def send_file(self):
        """
        Read the text from the 'self.filename' file
        :return: True if file exists, False otherwise
        """
        if os.path.isfile("client_files/" + self.filename):
            with open("client_files/" + self.filename, "r") as file:
                text_list = file.readlines()
                self.text_string = ''.join(text_list)
            send_msg(self.socket, self.text_string, HEADER_LENGTH)
            return True
        else:
            print("\'{}\' does not exist.\nPlease provide a valid file name.".format(self.filename))
            return False

    def add_to_queue(self, word):
        """
        Add a word into the clients queue
        :param word: word to add in the queue
        """
        self.q.put(word)
        print("word \'{}\' added in clients queue".format(word))

    def connect_to_backup(self):
        print("Trying to connect to backup server.")
        ready = False
        while not ready:
            ready = self.set_up_connection(IP, PORT_BackUp, self.username)
        print("Connected to backup server at IP:{}, Port:{}".format(IP, PORT_BackUp))
