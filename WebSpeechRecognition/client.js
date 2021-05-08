const io = require('socket.io-client');

// 1秒ごとに現在の時間をプリントするコマンド
var socket = io.connect('http://34.82.235.69:9001');//接続先のサーバを指定

//console.log(command);

socket.on('connect' ,function (data) {//コネクションの接続
  console.log("connected");

  socket.on('response',function(msg){//サーバからのレスポンスを受け取る
    msg = msg['data'];
    console.log(msg);
  });

  socket.on('exit',function(msg){//終了を受け取ったらSocket通信を終了する
    console.log(msg);
    socket.disconnect()
  });
});
