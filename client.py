import socket
import select
import errno
import sys
from PyQt4 import QtGui, QtCore
import time
from threading import Thread

HEADER_LENGTH = 10

IP = "46.117.245.207"
PORT = 49153

app = QtGui.QApplication(sys.argv)
widget = QtGui.QWidget()
widget.resize(400, 300)
widget.setWindowTitle('Chat Room!!!')

window = QtGui.QGridLayout(widget)
text = QtGui.QTextBrowser()
lmessage = QtGui.QLabel("Message:")
message = QtGui.QLineEdit()
lname = QtGui.QLabel("Name:")
name = QtGui.QLineEdit()
name.setText("user")
send = QtGui.QPushButton("Send")
conn = QtGui.QPushButton("Conn")
send.setDisabled(True)

window.addWidget(text,0,0,6,6)
window.addWidget(lname,6,0)
window.addWidget(name,6,1,1,2)
window.addWidget(send,6,5,1,1)
window.addWidget(conn,6,4,1,1)
window.addWidget(lmessage,7,0,1,1)
window.addWidget(message,7,1,1,5)

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
my_name = ''

def conn_func(sender):
    global my_name
    if send.isEnabled() == False:
        try:
            client_socket.connect((IP, PORT))

            # Set connection to non-blocking state, so .recv() call won;t block, just return some exception we'll handle
            client_socket.setblocking(False)

            # Prepare username and header and send them
            # We need to encode username to bytes, then count number of bytes and prepare header of fixed size, that we encode to bytes as well
            username = name.text()
            my_name = username
            username = username.encode('utf-8')

            username_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')

            client_socket.send(username_header + username)
            send.setDisabled(False)
            text.append("%s connected!" % name.text())
            conn.setText("Exit")
        except Exception as e:
            text.append("network error!")
            text.append(e)
    else:
        send.setDisabled(True)
        client_socket.close()
        text.append("Connect close,Good-bye!")
        conn.setText("Conn")

def send_func(sender=None):
    if not message.text() or send.isEnabled() == False:
        print("error message")
        return

    # Encode message to bytes, prepare header and convert to bytes, like for username above, then send
    message_text = message.text().encode('utf-8')
    message_header = f"{len(message_text):<{HEADER_LENGTH}}".encode('utf-8')
    client_socket.send(message_header + message_text)
    text.append("%s> %s" % (my_name, message.text()))
    message.setText('')

conn.mousePressEvent = conn_func
send.mousePressEvent = send_func

window.connect(QtGui.QShortcut(QtGui.QKeySequence("Return"), widget), QtCore.SIGNAL('activated()'), send_func)


def recv(sender):
    while True:
        if send.isEnabled() == False:
            time.sleep(1)
            continue
        try:
            # Now we want to loop over received messages (there might be more than one) and print them
            while True:

                # Receive our "header" containing username length, it's size is defined and constant
                username_header = client_socket.recv(HEADER_LENGTH)

                # If we received no data, server gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
                if not len(username_header):
                    print('Connection closed by the server')
                    text.append("Connection closed by the server")
                    sys.exit()

                # Convert header to int value
                username_length = int(username_header.decode('utf-8').strip())

                # Receive and decode username
                username = client_socket.recv(username_length).decode('utf-8')

                # Now do the same for message (as we received username, we received whole message, there's no need to check if it has any length)
                message_header = client_socket.recv(HEADER_LENGTH)
                message_length = int(message_header.decode('utf-8').strip())
                message = client_socket.recv(message_length).decode('utf-8')

                # Print message
                text.append(f'{username}> {message}')

        except IOError as e:
            # This is normal on non blocking connections - when there are no incoming data error is going to be raised
            # Some operating systems will indicate that using AGAIN, and some using WOULDBLOCK error code
            # We are going to check for both - if one of them - that's expected, means no incoming data, continue as normal
            # If we got different error code - something happened
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                text.append('Reading error: {}'.format(str(e)))
                sys.exit()

            # We just did not receive anything
            time.sleep(1)
            continue

        except Exception as e:
            # Any other exception - something happened, exit
            text.append('Reading error: {}'.format(str(e)))
            sys.exit()


widget.show()
thread = Thread(target=recv, args=(1,))
thread.daemon = True
thread.start()
app.exec_()
sys.exit(client_socket.close())
