const socket = io.connect();                  // ソケットio
const speech = new webkitSpeechRecognition(); // 音声認識APIの使用
speech.lang = "ja";
// speech.interimResults = true                      // 言語を日本語に設定
let keep_standby = false;
let usr = "";

function update_prosess(text) { $("#prosess").text(text); } // 音声認識 スタンバイ/停止 表示
function update_status(text)  { $("#status").html(text); }  // 音声認識 イベント 表示
function update_usr(text)  { $("#usr").html(text); }  // 音声認識 イベント 表示

// 音声認識した文字表示
function update_result_text(text)  {
    update_prosess('[結果表示]');
    $("#content").text(text);
    console.log(text);
}

// 音声認識の結果取得時の処理
speech.onresult = result => {
    const text = result.results[0][0].transcript;
    update_result_text(text);
    socket.emit('get_word', {user: usr, word: text}); // 認識文字を socket.io 経由でサーバに送信する
};

// 音声認識の継続継続処理
speech.onend = () => {
    if (keep_standby) speech.start();
    else speech.stop();
};

speech.onspeechstart = () => update_prosess('[音声取得開始]');
speech.onspeechend   = () => update_prosess('[解析開始]');

$(function () {
    $("#start_btn").on('click', () => {
        update_status('<span class="text-success">『音声認識中』</span>');
        keep_standby = true;
        speech.start();
    });
    $("#end_btn").on('click', () => {
        update_status('<span class="text-danger">『音声認識停止中』</span>');
        update_prosess('[音声認識停止中]');
        keep_standby = false;
        speech.stop();
    });
    $("#usr_A_btn").on('click', () => {
        update_usr('<span class="text-success">ユーザAを選択しています</span>');
        usr = "A";

    });
    $("#usr_B_btn").on('click', () => {
        update_usr('<span class="text-success">ユーザBを選択しています</span>');
        usr = "B";

    });

    $("#end_btn").trigger('click'); // 初期
    //$("#start_btn").trigger('click'); // 自動スタート
});
