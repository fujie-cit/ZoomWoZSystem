(function () {
    let user_name = 'unknown';
    let at_least_one_word_recognized = false;

    function showMessage(message) {
        // $('#messages').append('<li>' + message)
        $('#messages').html('<li>' + message)
    }

    /* WebSocketが使えるかどうかのチェック */
    if (!window.WebSocket) {
        if (window.MozWebSocket) {
            window.WebSocket = window.MozWebSocket;
        } else {
            showMessage("Your browser doesn't support WebSockets")
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
        showMessage('Connected.')
    }

    /* WebSocketがメッセージを受け取ったときのコールバック */
    ws.onmessage = function (evt) {
        showMessage(evt.data)
    }

    /* WebSocketが閉じたときのコールバック */
    ws.onclose = function (evt) {
        $('#messages').append('<li>WebSocket connection closed.</li>');
    }

    let error = false; // webkitSpeechRecognition が使えない
    let recognizing = false; // 音声入力中か
    let recognitionValue = ''; // 文字起こしされたテキスト
    try {
        recognition = new webkitSpeechRecognition();
        recognition.lang = 'ja'; // 日本語
        recognition.continuous = false; // 継続しない
        // recognition.continuous = true; // 継続する
        recognition.interimResults = true;
        // recognition.maxAlternatives = 3;
        recognition.maxAlternatives = 1;

        // エラー時
        recognition.onerror = function (e) {
            // writeLog('onerror');
            // writeLog(e.error);
            recognizing = false;
        };
        // 音声結果取得時
        /* https://developer.mozilla.org/ja/docs/Web/API/Web_Speech_API */
        recognition.onresult = function (e) {
            // e.reuslts が SpeechRecognitionResultList オブジェクト
            // e.resultIndex に，実際に変更された最初の e.reulsts の要素のインデクス
            // e.results[i] は i 番目の結果の SpeechRecognitionAlternative のリスト
            // e.results[i][j].transcript が，i番目の結果のj番目の候補の認識結果
            // e.results[i][j].confidence が，i番目の結果のj番目の候補の信頼度

            // ひとつも結果が無ければ終了
            if (e.resultIndex >= e.results.length ||
                e.results[e.resultIndex].length < 1) {
                return; 
            }

            // 1度は結果が来たことを記録
            at_least_one_word_recognized = true;

            // message_type: SendSpeechRecognitionResult
            // datetime: 日時
            // user_name: ユーザ名
            // speech_recognition_state: Start / Partial / End
            // speech_recognition_result: 音声認識結果（文字列，Startの場合も考慮して空文字もあり）
            
            speech_recognition_state = "Partial";
            if(e.results[e.resultIndex].isFinal) {
                speech_recognition_state = "End"
            }
            speech_recognition_result = e.results[e.resultIndex][0].transcript;

            datetime_now = new Date();
            message = JSON.stringify({
                message_type: "SendSpeechRecognitionResult",
                datetime: datetime_now.toISOString(),
                user_name: user_name,
                speech_recognition_state: speech_recognition_state,
                speech_recognition_result: speech_recognition_result
            });
            ws.send(message)

            // writeLog('onresult');
            // for (var i = e.resultIndex; i < e.results.length; ++i) {
            //     if (e.results[i].isFinal) {
            //         recognitionValue += e.results[i][0].transcript;
            //     }
            // }
            // showMessage(recognitionValue)
            // //　最初の結果のみ使う.
            // for (var i = e.resultIndex; i < e.results.length; ++i) {
            //     // for (var i = 0; i < e.results.length; ++i) {
            //     for (var j = 0; j < e.results[i].length; ++j) {
            //         // recognitionValue += "[" + j + "] "
            //         recognitionValue += e.results[i][j].transcript;
            //         if (e.results[i].isFinal) {
            //             recognitionValue += "。";
            //         }
            //         recognitionValue += "(" + e.results[i][j].confidence + ") ";
            //     }
            // }
            // // showMessage(recognitionValue);
            // // ws.send(recognitionValue);

            // recognitionValue = "";
        };

        // 音声入力終了時 (エラー終了時含む)
        recognition.onend = function () {
            // writeLog('onend');

            if (recognizing) {
                recognizing = false;
                // writeResult(recognitionValue);
                showMessage(recognitionValue);
                recognitionValue = '';
            }

            // document.getElementById('start').disabled = false;
            recognition.start();
        };
        // recognition.onsoundstart = function() { writeLog('onsoundstart'); }; // 音声認識開始時
        // recognition.onsoundend = function() { writeLog('onsoundend'); }; // 音声認識終了時 (onresult より前に発生)
        // recognition.onnomatch = function() { writeLog('onnomatch'); }; // 認識なし

        recognition.onspeechstart = function () {
            // ws.send("音声認識開始");
            // message_type: SendSpeechRecognitionResult
            // datetime: 日時
            // user_name: ユーザ名
            // speech_recognition_state: Start / Partial / End
            // speech_recognition_result: 音声認識結果（文字列，Startの場合も考慮して空文字もあり）
            datetime_now = new Date();
            message = JSON.stringify({
                message_type: 'SendSpeechRecognitionResult',
                datetime: datetime_now.toISOString(),
                user_name: user_name,
                speech_recognition_state: 'Start',
                speech_recognition_result: ''
            })
            ws.send(message)
            at_least_one_word_recognized = false;
        }

        recognition.onspeechend = function () {
            // ws.send("音声認識終了")
            if (!at_least_one_word_recognized) {
                datetime_now = new Date();
                message = JSON.stringify({
                    message_type: 'SendSpeechRecognitionResult',
                    datetime: datetime_now.toISOString(),
                    user_name: user_name,
                    speech_recognition_state: 'End',
                    speech_recognition_result: ''
                })
                ws.send(message)
            }
        }
    }
    catch (e) {
        error = true;
    }

    // ボタン
    document.addEventListener('click', function (e) {
        if (e.target.id == 'start') {
            if (error) {
                alert('今閲覧中のブラウザではでは動作しません。');
                return;
            }

            e.target.disabled = true;

            recognizing = true;
            recognition.start();
            // writeLog('start');
        } else if (e.target.id == 'login_button') {
            user_name = $("#login_user_name").val()
            // message_type: RequestLogin
            // datetime: 日時
            // user_name: ユーザ名
            // password: パスワード
            datetime_now = new Date();
            ws.send(JSON.stringify({
                message_type: 'RequestLogin',
                datetime: datetime_now.toISOString(),
                user_name: user_name,
                password: '123456789'
            }));
        }
    });


}());
