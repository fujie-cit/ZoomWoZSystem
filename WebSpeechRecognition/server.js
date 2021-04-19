// const PORT = 4000;
const PORT = process.env.PORT || 9000;
const PORT2 = 9001;
const INDEX = '/index.html';

const express = require('express');
const os = require('os')
const socketIO = require('socket.io');

const app = express();
app.use(express.static(__dirname));
const server = require('http').createServer(app).listen(PORT);
const io = socketIO(server);

const io2 = require('socket.io')(PORT2);
var io2_flg = true;

io2.on('connection', function ( socket2 ) {
  console.log('接続完了');
  socket2.emit('on_server_to_client', {word: '接続完了'});
  io2_flg = true;
});

io2.on('disconnect',() => {
  console.log( 'disconnect' );
  io2_flg = false;
} );

io.sockets.on('connection', function(socket) {
  socket.on('get_word', function (data) {
    if(data === undefined || data === "" || data === null) return;
    console.log(data);
    if (io2_flg == true) io2.sockets.emit('on_server_to_client', {usr: data.user, word: data.word});
  });
});
