(function () {
    function clearMessage() {
        $('#messages').html(
            '<li>ここにデバッグメッセージが表示されます.</li>'
        );
    }
    
    function showMessage(message) {
        $('#messages').append(
            '<li>' + message + '</li>'
        );
    }

    /* WebSocketが使えるかどうかのチェック */
    if (!window.WebSocket) {
        if (window.MozWebSocket) {
            window.WebSocket = window.MozWebSocket;
        } else {
            // showMessage("Your browser doesn't support WebSockets")
            alert("Your browser doesn't support WebSockets")
        }
    }

    /* WebSocketのURL */
    let scheme = window.location.protocol === "https:" ? 'wss://' : 'ws://';
    let webSocketUri = scheme
        + window.location.hostname
        + (location.port ? ':' + location.port : '')
        + $SCRIPT_ROOT + '/websocket';
    let ws = new WebSocket(webSocketUri);

    /* WebSocketが開いたときのコールバック */
    ws.onopen = function (evt) {
        showMessage('サーバ（websocket）に接続しました.')
    }

    /* WebSocketがメッセージを受け取ったときのコールバック */
    ws.onmessage = function (evt) {
        data = JSON.parse(evt.data)
        if(data.message_type == 'Ping') {
            datetime_now = new Date();
            data = {
                message_type: 'Pong',
                datetime: datetime_now.toISOString(),
                user_name: user_name,
                source_datetime: data.source_datetime,
                source_id: data.source_id
            }
            ws.send(JSON.stringify(data))
        }
    }

    /* WebSocketが閉じたときのコールバック */
    ws.onclose = function (evt) {
        showMessage('サーバエラー（リロードしてください）')
    }

    let mediaRecorder = null;

    var handleSuccess = function (stream) {
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = function (e) {
            // showMessage('data size: ' + e.data.size + ": " + data_string);
            // blobToBase64(e.data).then(function (res) {
            //     showMessage('data size: ' + e.data.size + ': ' + res);
            // });
            e.data.arrayBuffer().then(function(buffer){
                // showMessage(buffer[0]);
                base64String = btoa(String.fromCharCode.apply(null, new Uint8Array(buffer)));
                message = {
                    message_type: 'sound_data',
                    type: e.data.type,
                    data: base64String,
                }
                // showMessage(JSON.stringify(message))
                ws.send(JSON.stringify(message))
            });
        };

        mediaRecorder.onstop = function () {
            message = {
                message_type: 'sound_stop',
            }
            ws.send(JSON.stringify(message))
            showMessage("録音停止しました.");
        }

        message = {
            message_type: 'sound_start',
        }
        ws.send(JSON.stringify(message))

        var slice = 10 // sliceミリ秒毎に送信
        mediaRecorder.start(slice);
        
        showMessage("録音開始しました.");
    };

    /* -- ボタン --*/
    document.addEventListener('click', function (e) {
        if (e.target.id == 'start') {
            // 録音開始
            navigator.mediaDevices.getUserMedia({
                audio: true, video: false
            }).then(handleSuccess);
        } else if (e.target.id == 'stop' && mediaRecorder != null) {
            // 録音終了
            mediaRecorder.stop();
            mediaRecorder = null;
        }
    });


}());
