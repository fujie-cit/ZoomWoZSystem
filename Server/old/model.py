from torch import nn


class BertClassifier(nn.Module):

    def __init__(self, model):
        super(BertClassifier, self).__init__()

        # BERTモジュール
        self.bert = model  # 日本語学習済みのBERTモデル

        # headにクラス予測を追加
        # 入力はBERTの出力特徴量の次元768、出力は10クラス
        self.cls = nn.Linear(in_features=768, out_features=10)

        # 重み初期化処理
        nn.init.normal_(self.cls.weight, std=0.02)
        nn.init.normal_(self.cls.bias, 0)

    def forward(self, input_ids):
        '''
        input_ids： [batch_size, sequence_length]の文章の単語IDの羅列
        '''
        # BERTの基本モデル部分の順伝搬
        # 順伝搬させる
        result = self.bert(input_ids)
        vec = result[0]
        attentions = result[-1]
        vec = vec[:, 0, :]
        vec_0 = vec.view(-1, 768)
        output = self.cls(vec_0)

        return output, attentions
