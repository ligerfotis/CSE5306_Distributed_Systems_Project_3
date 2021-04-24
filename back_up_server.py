"""
@author: Fotios Lygerakis
@UTA ID: 1001774373
"""
import queue
import socket
import select
import time

from config import IP, PORT_BackUp, polling_timeout, HEADER_LENGTH, back_up_lexicon_file
from utils.utils import send_msg, receive_file, check_username, save_file
from utils.utils_server import update_lexicon, spelling_check, receive_msg

"""
Code based on https://pythonprogramming.net/server-chatroom-sockets-tutorial-python-3/
"""


class BackUpServer:
    def __init__(self):

        # Create a socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((IP, PORT_BackUp))

        # Listen to new connections
        self.socket.listen()

        # List of sockets for select.select()
        self.sockets_list = [self.socket]

        # List of connected clients - socket as a key, user header and name as data
        self.clients = {}

        self.lexicon_list = []
        self.shutdown = False

    def main(self):
        """
        Main functionality of the server
        """
        print("Listening for connections on {}:{}...".format(IP, PORT_BackUp))
        # load up the lexicon entries
        with open("back_up_server_files/" + back_up_lexicon_file, "r") as file:
            self.lexicon_list = file.readlines()[0].split(" ")

        start_time = time.time()
        while True:
            # times out every 'polling_timeout' minutes to poll from clients
            # did this trick to take into consideration the time spent on exchanging files with clients
            timeout = polling_timeout - (time.time() - start_time)
            """
            Polling is based on https://pymotw.com/2/select/
            """
            if "server" in self.get_live_usernames():
                read_sockets, _, exception_sockets = select.select(self.sockets_list, [], self.sockets_list)
            else:
                if timeout < 0:
                    timeout = 0
                read_sockets, _, exception_sockets = select.select(self.sockets_list, [], self.sockets_list, timeout)
            # if timeout has happened
            if not (read_sockets or exception_sockets) and "server" not in self.get_live_usernames():
                # polling
                q_dict = self.q_polling()
                # update lexicon
                for q in q_dict.values():
                    self.lexicon_list, _ = update_lexicon(q, self.lexicon_list)
                # update lexicon file
                with open("back_up_server_files/lexicon.txt", "w") as file:
                    file.write(" ".join(self.lexicon_list))
                start_time = time.time()

            # Iterate over notified sockets
            for notified_socket in read_sockets:

                # If notified socket is a server socket - new connection, accept it
                if notified_socket == self.socket:

                    # Accept new connection
                    # That gives us new socket - client socket, connected to this given client only, it's unique for that client
                    # The other returned object is ip/port set
                    try:
                        client_socket, client_address = self.socket.accept()
                    except:
                        print("server shut down")
                        self.shutdown = True
                        break
                    # Client should send his name right away, receive it
                    user = receive_file(client_socket, header_length=HEADER_LENGTH)

                    # If False - client disconnected before he sent his name
                    if user is False:
                        continue

                    username = user['data'].decode()
                    # username is not taken
                    if check_username(username, self.clients):
                        # Add accepted socket to select.select() list
                        self.sockets_list.append(client_socket)
                        # Also save username and username header
                        self.clients[client_socket] = user
                        send_msg(socket=client_socket, message=username, header_length=HEADER_LENGTH)
                        print('Accepted new connection from {}:{}, username: {}'.format(*client_address,
                                                                                        user['data'].decode('utf-8')))
                    # the username is taken
                    else:
                        # notify the client of used username and close the socket
                        send_msg(socket=client_socket, message="None", header_length=HEADER_LENGTH)
                        print(
                            'Rejected new connection from {}:{}. username: {} is already in use by another client'.format(
                                *client_address,
                                user['data'].decode('utf-8')))
                        client_socket.close()

                # Else existing socket is sending a message
                else:
                    q = queue.Queue()
                    if "server" in self.get_live_usernames():
                        # if server is till on
                        print("server is talking")
                        try:
                            while 1:
                                # receive word from the client
                                poll_msg = receive_file(notified_socket, HEADER_LENGTH)
                                if poll_msg is False:
                                    print(
                                        'Closed connection from: {}'.format(
                                            self.clients[notified_socket]['data'].decode('utf-8')))
                                    # Remove from list for socket.socket()
                                    self.sockets_list.remove(notified_socket)
                                    # Remove from our list of users
                                    del self.clients[notified_socket]
                                    break

                                elif poll_msg['data'].decode() == 'poll_end':
                                    break
                                else:
                                    # put the polling word in the queue
                                    q.put(poll_msg['data'].decode())
                                    print("Word \'{}\' was polled from the main server.".format(poll_msg['data'].decode()))
                        except select.error:
                            start_time = time.time()
                            print('Closed connection from server')
                            self.sockets_list.remove(notified_socket)
                            # Remove from our list of users
                            del self.clients[notified_socket]
                            continue
                        # update lexicon
                        self.lexicon_list, _ = update_lexicon(q, self.lexicon_list)
                        # update lexicon file
                        with open("back_up_server_files/lexicon.txt", "w") as file:
                            file.write(" ".join(self.lexicon_list))
                    else:
                        # Receive username
                        message = receive_file(notified_socket, header_length=HEADER_LENGTH)

                        # If False, client disconnected, cleanup
                        if message is False:
                            print(
                                'Closed connection from: {}'.format(self.clients[notified_socket]['data'].decode('utf-8')))
                            # Remove from list for socket.socket()
                            self.sockets_list.remove(notified_socket)
                            # Remove from our list of users
                            del self.clients[notified_socket]
                            continue

                        # filter out the text from the message
                        username = self.clients[notified_socket]["data"].decode()

                        path = "server_files/"
                        client_file = "file_{}.txt".format(username)
                        msg = message["data"].decode("utf-8")
                        # save the text to a file
                        save_file(msg, path, client_file)

                        # Get user by notified socket, so we will know who sent the message
                        user = self.clients[notified_socket]
                        print('Received text from user:{}'.format(username))

                        # annotate misspelled words
                        annotated_text = spelling_check(path + client_file, self.lexicon_list)

                        # print("sending {}".format(annotated_text))
                        send_msg(notified_socket, annotated_text, HEADER_LENGTH)
                        print("Sent annotated text back to user:{}".format(username))

            if self.shutdown:
                break
            self.handle_socket_exceptions(exception_sockets)

    def handle_socket_exceptions(self, exception_sockets):
        # It's not really necessary to have this, but will handle some socket exceptions just in case
        for notified_socket in exception_sockets:
            # Remove from list for socket.socket()
            self.sockets_list.remove(notified_socket)
            # Remove from our list of users
            del self.clients[notified_socket]

    def get_live_usernames(self):
        """
        Returns a list of live usernames
        :return: list of live usernames
        """
        username_list = []
        for client_socket in self.clients:
            username = self.clients[client_socket]["data"].decode()
            username_list.append(username)
        return username_list

    def q_polling(self):
        """
        Put the words from the polling to a queue for each client
        :return: a dictionary with a queue for each client
        """
        polls = {}
        print("Polling from clients...")
        clients = self.clients.copy()
        # iterate over clients
        for client_socket in clients:
            try:
                # poll each client
                send_msg(client_socket, "poll", HEADER_LENGTH)
                q = queue.Queue()
                while 1:
                    # receive word from the client
                    poll_msg = receive_msg(client_socket, HEADER_LENGTH)
                    if poll_msg == 'poll_end':
                        # the polling from this q has ended and store the queue in the dictionary
                        polls[client_socket] = q
                        break
                    else:
                        # put the polling word in the queue
                        q.put(poll_msg)
                        print("Word \'{}\' was polled from user: {}".format(poll_msg, clients[client_socket]["data"].decode()))
            except select.error:
                print(
                    'Closed connection from: {}'.format(self.clients[client_socket]['data'].decode('utf-8')))
                self.sockets_list.remove(client_socket)
                # Remove from our list of users
                del self.clients[client_socket]
                continue
        return polls

