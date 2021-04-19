# from socketIO_client_nexus import SocketIO, LoggingNamespace
#
#
# def on_connect():
#     print('connect')
#
#
# def on_disconnect():
#     print('disconnect')
#
#
# def on_reconnect():
#     print('reconnect')
#
#
# def on_date_response(*args):
#     print('on_date', args)
#
#
# socketIO = SocketIO('http://34.82.235.69', 8081, LoggingNamespace)
# socketIO.on('connect', on_connect)
# socketIO.on('disconnect', on_disconnect)
# socketIO.on('reconnect', on_reconnect)
#
# # Listen
# socketIO.on('date', on_date_response)
# socketIO.emit('test', {'value': 'test3'})
# socketIO.wait(seconds=10)


import socketio

# standard Python
sio = socketio.Client()


@sio.event
def connect():
    print("connected!")


@sio.on('on_server_to_client')
def on_server_to_client(data):
    usr = data['user']
    text = data['word']
    print('{}: {}'.format(usr, text))


sio.connect('http://34.82.235.69:9001')
