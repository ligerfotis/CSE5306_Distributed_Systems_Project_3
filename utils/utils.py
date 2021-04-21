"""
@author: Fotios Lygerakis
@UTA ID: 1001774373
"""
import os
import socket

from config import IP, PORT


def set_up_username(ip, port, my_username, header_length):
    """
    Sets up connection with the server and establishes a username on it.
    If the username is taken, it returns None.
    :param my_username: username to
    :param header_length:
    :return:
    """
    client_socket = connect_client(ip, port)

    send_msg(socket=client_socket, message=my_username, header_length=header_length)
    username = False
    while not username:
        username = receive_file(client_socket, header_length=header_length)
        if username:
            if username["data"].decode() == "None":
                return None
            else:
                username = username["data"].decode()
                print("My username is {}".format(username))
                return [username, client_socket]


def send_msg(socket, message, header_length):
    """
    Encode message to bytes, prepare header and convert to bytes, like for username above, then send
    :param socket: socket to send through
    :param message: message to send
    :param header_length: header length
    """
    msg = message.encode('utf-8')
    msg_header = f"{len(msg):<{header_length}}".encode('utf-8')
    socket.send(msg_header + msg)


def receive_file(client_socket, header_length):
    """
    Handles message receiving
    :param client_socket: socket to receive from
    :param header_length: header length
    :return: a dictionary with message header and message
    """
    try:
        # Receive our "header" containing message length, it's size is defined and constant
        message_header = client_socket.recv(header_length)
        # If we received no data, client gracefully closed a connection, for example using socket.close() or
        if not len(message_header):
            return False

        # Convert header to int value
        message_length = int(message_header.decode('utf-8').strip())
        # print("msg length: {}".format(message_length))

        # Return an object of message header and message data
        return {'header': message_header, 'data': client_socket.recv(message_length)}

    except:

        # If we are here, client closed connection violently, for example by pressing ctrl+c on his script or just
        # lost his connection socket.close() also invokes socket.shutdown(socket.SHUT_RDWR) what sends information
        # about closing the socket (shutdown read/write) and that's also a cause when we receive an empty message
        return False


def check_username(username, clients):
    """
    Checks if username is taken
    :param username: username to be checked
    :param clients: the online clients
    :return: True if not used, False otherwise
    """
    for socket in clients:
        if clients[socket]["data"].decode() == username:
            return False
    return True


def connect_client(ip, port):
    """
    Connects client through a socket
    :param ip: ip address
    :param port: port
    :return: the socket established
    """
    # Create a socket socket.AF_INET - address family, IPv4, some otehr possible are AF_INET6, AF_BLUETOOTH,
    # AF_UNIX socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams,
    # socket.SOCK_RAW - raw IP packets
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to a given ip and port
    client_socket.connect((ip, port))

    # Set connection to non-blocking state, so .recv() call won;t block, just return some exception we'll handle
    client_socket.setblocking(False)
    return client_socket


def save_file(text, path, client_file):
    """
    Saves the text to a file
    :param text:
    :param path:
    :param client_file:
    :return:
    """
    # create dir to store received texts from clients
    if not os.path.exists(path):
        os.mkdir(path)
    # check if file exists already and erase it if so
    if os.path.exists(path + client_file):
        os.remove(path + client_file)

    with open(path + client_file, "wt") as file:
        file.write(text)
