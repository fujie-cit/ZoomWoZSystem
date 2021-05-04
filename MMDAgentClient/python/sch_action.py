# coding: utf-8
import csv
import os
import glob

# 目や首の最大，最小値を得るため
from mmdagent_schema_client import MMDAgentSchemaClient as msc

# Action Pattern Type
AP_ABS = 1 # ABSOLUTE
AP_REL = 2 # RELATIVE

# Action Type
AT_NORMAL = 1 # NORMAL
AT_PERIODIC = 2 # PERIODIC

# Default Action Directory
DEFAULT_ACTION_DIRECTORY = 'action'
DEFAULT_NORMAL_ACTION_DIRECTORY = 'normal'
DEFAULT_PERIODIC_ACTION_DIRECTORY = 'periodic'

class ActionPattern (object):
    u"""アクションパターン
    CSVファイル1つに対応
    """

    def __init__ (self):
        self._type = AP_ABS
        self._pat  = []
        self._final_tick = 0

    def read (self, filename):
        u"""filenameで与えられたCSVファイルを読み込む"""

        with open (filename, 'r') as f:
            reader = csv.reader(f)
            line = next(reader)

            # タイプを読み込む
            if line[0] == 'ABS':
                self._type = AP_ABS
            elif line[0] == 'REL':
                self._type = AP_REL
            else:
                raise Exception ('Unkonwn Type')

            # パターンを読み込む
            for pat in reader:
                if all ([x == '' for x in pat]):
                    continue
                # 自由度名
                dof  = pat[0]
                # 時刻
                t    = float(pat[1])
                # 目標角度
                deg  = float(pat[2])
                # 速度，加速度，減速度など
                # （必須でないので空があったら0にしておく）
                rest = []
                for s in pat[3:]:
                    try:
                        rest.append(float(s))
                    except ValueError:
                        rest.append(0.0)
                self._pat.append([dof, t, deg] + rest)

        # 最終tickを確認しておく
        self._update_final_tick ()

    def _update_final_tick (self):
        u"""最終tickを更新する"""
        self._final_tick = 0
        for p in self._pat:
            if p[1] > self._final_tick:
                self._final_tick = p[1]

    @property
    def type (self):
        u"""タイプ．絶対的か相対的か．"""
        return self._type

    @type.setter
    def type (self, value):
        self._type = value

    @property
    def pattern (self):
        u"""パターンのリスト"""
        return self._pat

    @pattern.setter
    def pattern (self, value):
        self._pat = value
        self._update_final_tick ()

    @property
    def final_tick (self):
        u"""パターン全体の最終tick"""
        return self._final_tick

class Action (object):
    u"""1つのアクション"""
    def __init__ (self):
        self._name = None
        self._type = AT_NORMAL
        self._pattern_list = []
        self._cancel_pattern = None

    def read (self, dirname, action_type):
        u"""ディレクトリから読み込む．
        アクション名はディレクトリ名から自動的に判断する．
        アクションタイプは action_type で与える．
        """
        self._name = os.path.basename(dirname)
        self._type = action_type
        filelist = sorted (glob.glob(os.path.join(dirname, '*.csv')))
        self._pattern_list = []
        self._cancel_pattern = None
        for f in filelist:
            ap = ActionPattern()
            ap.read (f)
            if os.path.basename(f) != "cancel.csv":
                self._pattern_list.append(ap)
            else:
                self._cancel_pattern = ap

    @property
    def name (self):
        u"""アクション名"""
        return self._name

    @property
    def type (self):
        u"""アクションタイプ．周期的かどうか"""
        return self._type

    @property
    def pattern_list (self):
        u"""アクションパターンのリスト．キャンセルパターン以外"""
        return self._pattern_list

    @property
    def cancel_pattern (self):
        u"""キャンセルパターン"""
        return self._cancel_pattern


class ActionLookWithEye (Action):
    def __init__ (self, yaw=0.0, pitch=0.0, last_target_info=None):
        Action.__init__ (self)
        self._name = 'le'
        self._type = AT_NORMAL
        self._pattern_list = []
        self._cancel_pattern = None

        # 現状の neck_yaw, neck_pitch, turret_yaw を取得する
        current_neck_yaw = 0.0
        current_neck_pitch = 0.0
        current_turret_yaw = 0.0
        if last_target_info != None:
            if 'NEC_X_Y' in last_target_info.keys():
                if last_target_info['NEC_X_Y'][0] != None:
                    current_neck_yaw = last_target_info['NEC_X_Y'][0]
            if 'NEC_X_P' in last_target_info.keys():
                if last_target_info['NEC_X_P'][0] != None:
                    current_neck_pitch = last_target_info['NEC_X_P'][0]
            if 'TURRET' in last_target_info.keys():
                if last_target_info['TURRET'][0] != None:
                    current_turret_yaw = last_target_info['TURRET'][0]

        eye_yaw  = yaw - current_neck_yaw - current_turret_yaw
        neck_yaw = current_neck_yaw
        turret_yaw = current_turret_yaw
        if eye_yaw < msc.get_min_pos('EYE_R_Y'):
            neck_yaw += eye_yaw - msc.get_min_pos('EYE_R_Y')
            eye_yaw  = msc.get_min_pos('EYE_R_Y')
        elif eye_yaw > msc.get_max_pos('EYE_R_Y'):
            neck_yaw += eye_yaw - msc.get_max_pos('EYE_R_Y')
            eye_yaw  = msc.get_max_pos('EYE_R_Y')
        if neck_yaw < msc.get_min_pos('NEC_X_Y'):
            turret_yaw += neck_yaw - msc.get_min_pos('NEC_X_Y')
            neck_yaw = msc.get_min_pos('NEC_X_Y')
        elif neck_yaw > msc.get_max_pos('NEC_X_Y'):
            turret_yaw += neck_yaw - msc.get_max_pos('NEC_X_Y')
            neck_yaw = msc.get_max_pos('NEC_X_Y')
        if turret_yaw < msc.get_min_pos('TURRET'):
            turret_yaw =  msc.get_min_pos('TURRET')
        elif turret_yaw > msc.get_max_pos('TURRET'):
            turret_yaw = msc.get_max_pos('TURRET')

        eye_pitch = pitch - current_neck_pitch
        neck_pitch = current_neck_pitch
        if eye_pitch < msc.get_min_pos('EYE_R_P'):
            neck_pitch += eye_pitch - msc.get_min_pos('EYE_R_P')
            eye_pitch = msc.get_min_pos('EYE_R_P')
        elif eye_pitch > msc.get_max_pos('EYE_R_P'):
            neck_pitch += eye_pitch - msc.get_max_pos('EYE_R_P')
            eye_pitch = msc.get_max_pos('EYE_R_P')
        if neck_pitch < msc.get_min_pos('NEC_X_Y'):
            neck_pitch =  msc.get_min_pos('NEC_X_Y')
        elif neck_pitch > msc.get_max_pos('NEC_X_Y'):
            neck_pitch = msc.get_max_pos('NEC_X_Y')

        pat = ActionPattern ()
        pat.type = AP_ABS
        pat.pattern = [['EYE_R_P', 10, eye_pitch],
                       ['EYE_L_P', 10, eye_pitch],
                       ['EYE_R_Y', 10, eye_yaw],
                       ['EYE_L_Y', 10, eye_yaw],
                       ['NEC_X_P', 10, neck_pitch],
                       ['NEC_X_Y', 10, neck_yaw],
                       ['TURRET', 10, turret_yaw]]
        self._pattern_list.append (pat)

class ActionLookWithNeck (Action):
    def __init__ (self, yaw=0.0, pitch=0.0, last_target_info=None):
        Action.__init__ (self)
        self._name = 'ln'
        self._type = AT_NORMAL
        self._pattern_list = []
        self._cancel_pattern = None

        # 現状の turret_yaw を取得する
        current_turret_yaw = 0.0
        if last_target_info != None:
            if 'TURRET' in last_target_info.keys():
                if last_target_info['TURRET'][0] != None:
                    current_turret_yaw = last_target_info['TURRET'][0]

        eye_yaw  = 0.0
        neck_yaw = yaw - current_turret_yaw
        turret_yaw = current_turret_yaw
        if neck_yaw < msc.get_min_pos('NEC_X_Y'):
            turret_yaw += neck_yaw - msc.get_min_pos('NEC_X_Y')
            neck_yaw = msc.get_min_pos('NEC_X_Y')
        elif neck_yaw > msc.get_max_pos('NEC_X_Y'):
            turret_yaw += neck_yaw - msc.get_max_pos('NEC_X_Y')
            neck_yaw = msc.get_max_pos('NEC_X_Y')
        if turret_yaw < msc.get_min_pos('TURRET'):
            turret_yaw =  msc.get_min_pos('TURRET')
        elif turret_yaw > msc.get_max_pos('TURRET'):
            turret_yaw = msc.get_max_pos('TURRET')

        eye_pitch = 0.0
        neck_pitch = pitch
        if neck_pitch < msc.get_min_pos('NEC_X_Y'):
            neck_pitch =  msc.get_min_pos('NEC_X_Y')
        elif neck_pitch > msc.get_max_pos('NEC_X_Y'):
            neck_pitch = msc.get_max_pos('NEC_X_Y')

        pat = ActionPattern ()
        pat.type = AP_ABS
        pat.pattern = [['EYE_R_P', 10, eye_pitch],
                       ['EYE_L_P', 10, eye_pitch],
                       ['EYE_R_Y', 10, eye_yaw],
                       ['EYE_L_Y', 10, eye_yaw],
                       ['NEC_X_P', 10, neck_pitch],
                       ['NEC_X_Y', 10, neck_yaw],
                       ['TURRET', 10, turret_yaw]]
        self._pattern_list.append (pat)

class ActionLookWithTurret (Action):
    def __init__ (self, yaw=0.0, pitch=0.0, last_target_info=None):
        Action.__init__ (self)
        self._name = 'lt'
        self._type = AT_NORMAL
        self._pattern_list = []
        self._cancel_pattern = None

        eye_yaw  = 0.0
        neck_yaw = 0.0
        turret_yaw = yaw
        if turret_yaw < msc.get_min_pos('TURRET'):
            turret_yaw =  msc.get_min_pos('TURRET')
        elif turret_yaw > msc.get_max_pos('TURRET'):
            turret_yaw = msc.get_max_pos('TURRET')

        eye_pitch = 0.0
        neck_pitch = pitch
        if neck_pitch < msc.get_min_pos('NEC_X_Y'):
            neck_pitch =  msc.get_min_pos('NEC_X_Y')
        elif neck_pitch > msc.get_max_pos('NEC_X_Y'):
            neck_pitch = msc.get_max_pos('NEC_X_Y')

        pat = ActionPattern ()
        pat.type = AP_ABS
        pat.pattern = [['EYE_R_P', 10, eye_pitch],
                       ['EYE_L_P', 10, eye_pitch],
                       ['EYE_R_Y', 10, eye_yaw],
                       ['EYE_L_Y', 10, eye_yaw],
                       ['NEC_X_P', 10, neck_pitch],
                       ['NEC_X_Y', 10, neck_yaw],
                       ['TURRET',  10, turret_yaw]]
        self._pattern_list.append (pat)

class ActionDictionary (dict):
    u"""アクション名をキーにした，アクションのディクショナリ"""
    def __init__ (self):
        pass

    def read (self, topdir):
        u"""topdir以下にあるアクション情報を読み込む"""
        self.clear()
        for typ_dir, typ in (('normal', AT_NORMAL),
                             ('periodic', AT_PERIODIC)):
            dir_pattern = os.path.join (topdir, typ_dir, '*')
            for act_dir in glob.glob (dir_pattern):
                if os.path.isdir (act_dir):
                    action = Action ()
                    action.read (act_dir, typ)
                    self[action.name] = action

class ActionContext (object):
    u"""アクションの実行時のコンテキスト情報を保持する"""
    def __init__ (self, action):
        # もととなるアクション
        self._action = action

        # 現在のパターンのインデクス
        # -1 はキャンセルパターンという意味
        self._current_pattern_index = 0

        # 現在のパターン
        self._current_pattern = self._action.pattern_list[
            self._current_pattern_index]

        # 現時刻のtick（アクション全体）
        self._current_tick = 0

        # 現在のパターンが始まった時のtick
        self._current_pattern_tick = 0

        # キャンセルされているかどうか
        self._is_cancelled = False

        # 終了してたら True
        self._finished = False

    def get_current_target (self):
        u"""現在のtickに応じた目標角度を取り出す．
        戻り値として，自由度名をキーとして目標角度を返す．
        """

        # 戻り値
        rv = {}

        # 現在のパターンでの tick
        tick = self._current_tick - self._current_pattern_tick

        for pat in self._current_pattern.pattern:
            # 自由度名
            dof_name = pat[0]
            # 名前が既にあったら何もしない
            if dof_name in rv.keys():
                continue
            # 目標時刻[tick]
            target_tick = pat[1]
            # 目標時刻が現在のtick以下だったら何もしない
            if target_tick <= tick:
                continue
            # 目標角度[deg]
            target_deg = pat[2]
            # 設定する
            rv[dof_name] = target_deg

        return rv

    def update (self, target):
        u"""目標角度情報を更新する.

        target は 自由度名 をキーとして， [ ABS分の目標値, REL分の目標値 ] を
        を値としてもつディクショナリ．

        目標値は deg 単位の float
        """
        # 現在のパターンのタイプ
        pat_type = self._current_pattern.type
        # 現在のパターンの目標角を取得
        pat_target = self.get_current_target ()

        for dof, target_deg in pat_target.items():
            # そもそも設定が無ければそのまま更新
            if not dof in target.keys():
                if pat_type == AP_ABS:
                    target[dof] = [target_deg, None]
                else:
                    target[dof] = [None, target_deg]
                continue

            # 設定されるタイプと角度
            abs_target, rel_target = target[dof]

            if pat_type == AP_ABS:
                if abs_target != None:
                    print("conflict dof (%s) for action '%s'" % (
                        dof, self._action.name))
                else:
                    target[dof][0] = target_deg
            else:
                if rel_target != None:
                    target[dof][1] = target_deg + rel_target
                else:
                    target[dof][1] = target_deg

    def step (self):
        u"""1 tick 進める."""

        # 全体が終了していたら何もしない
        if self._finished == True:
            return

        # 1 tick 進める
        self._current_tick += 1

        # 現在のパターンの開始に対する相対 tick に直す
        tick = self._current_tick - self._current_pattern_tick

        # 現在のパターンの終了tickに到達しているかチェックし，
        # 到達して無ければこれ以上は何もせずに終了
        if tick < self._current_pattern.final_tick:
            return

        # 到達していた場合は各種パターンの変更等が必要

        # まず，キャンセルパターンを実行していて終了した場合は
        # 終了
        if self._current_pattern_index < 0:
            self._finished = True
            return

        # キャンセルがリクエストされていて，
        # キャンセルパターンがある場合はキャンセルパターンを実行開始，
        # 無い場合は終了する
        if self._is_cancelled == True:
            if self._action.cancel_pattern != None:
                self._current_pattern_index = -1
                self._current_pattern = self._action.cancel_pattern
                self._current_pattern_tick = self._current_tick
            else:
                self._finished = True
            return

        # 次のパターンを見つける．
        # 最後まで到達してなければ単純に次に進む．
        # 到達していた場合は，非周期動作であれば終了，
        # 周期動作であれば同じパターンを繰り返す
        self._current_pattern_index += 1 # 一旦進めてみて…
        if self._current_pattern_index < len(self._action.pattern_list):
            # 最終に到達してなければそのまま採用
            pass
        elif self._action.type == AT_NORMAL:
            # 最終に到達していて非周期動作だった場合は終了
            self._finished = True
            return
        else:
            # 最終に到達していて周期動作だった場合は同じパターンを繰り返す
            self._current_pattern_index -= 1 # 元に戻す

        # print self._current_pattern_index
        # print self._current_tick

        self._current_pattern = self._action.pattern_list[
            self._current_pattern_index]
        self._current_pattern_tick = self._current_tick

    def cancel (self):
        u"""キャンセルをリクエストする"""
        self._is_cancelled = True

    @property
    def is_finished (self):
        u"""終了しているかどうか"""
        return self._finished

class ActionMasterContext (object):
    def __init__ (self, action_dictionary):
        self._act_dict = action_dictionary
        self._context_dict = {}
        self._name_list = []
        self._target = {}
        self._actual_target = {}
        self._target_info = {}
        self._last_target_info = {}

        self._tick = 0

    def put (self, action_name):
        u"""新しいアクションを投入する"""
        if not action_name in self._act_dict.keys():
            print("action %s not found" % action_name)

        if action_name in self._context_dict.keys():
            print("action %s is alread started" % action_name)
            return

        new_context = ActionContext(self._act_dict[action_name])
        self._context_dict[action_name] = new_context
        self._name_list.append (action_name)

    def put_action_direct (self, action):
        u"""新しいアクションを直に投入する"""
        if action.name in self._context_dict.keys():
            print("action %s is alread started" % action.name)
            return

        new_context = ActionContext(action)
        self._context_dict[action.name] = new_context
        self._name_list.append (action.name)

    def cancel (self, action_name):
        u"""アクションをキャンセルする"""

        # 既に終了済み
        if not action_name in self._context_dict.keys():
            return

        self._context_dict[action_name].cancel()

    def step (self):
        self._tick += 1

        # コンテクストを進めつつ．終了したコンテクストは削除する
        del_list = []
        for name, context in self._context_dict.items():
            context.step()
            # iterationしながら消すのはよくないかも…
            if context.is_finished:
                del_list.append(name)
                self._name_list.remove (name)

        for name in del_list:
            del self._context_dict[name]

        # 新たなターゲットを作成
        target_info = {}
        for name in self._name_list:
            self._context_dict[name].update (target_info)

        # 角度情報だけに直す
        target_deg_only = {}
        for dof, info in target_info.items():
            # print target_info
            # print self._last_target_info
            tgt = 0.0
            if info[0] != None:
                tgt = info[0]
            elif dof in self._last_target_info.keys() and self._last_target_info[dof][0] != None:
                tgt = self._last_target_info[dof][0]
            if info[1] != None:
                tgt += info[1]
            target_deg_only[dof] = tgt

        # 過去の目標値と比較して，実際出力するべきターゲットに絞り込む
        actual_target = {}
        for dof, target_deg in target_deg_only.items():
            if not dof in self._target.keys() or self._target[dof] != target_deg:
                actual_target[dof] = target_deg

        # メンバ変数更新
        self._actual_target.clear()
        self._actual_target.update(actual_target)

        self._target.clear()
        self._target.update(target_deg_only)

        self._target_info.clear()
        self._target_info.update(target_info)

        for dof, info in target_info.items():
            if not dof in self._last_target_info.keys():
                self._last_target_info[dof] = info

            if info[0] != None:
                self._last_target_info[dof][0] = info[0]
            if info[1] != None:
                self._last_target_info[dof][1] = info[1]

    @property
    def target (self):
        u"""目標角のディクショナリ"""
        return self._target

    @property
    def actual_target (self):
        u"""何度も同じ命令を送らないために前 tick から変わったところだけ"""
        return self._actual_target

    @property
    def target_info (self):
        u"""自由度名をキー，[ABS目標値，REL目標値]を値にしたディクショナリ"""
        return self._target_info

    @property
    def last_target_info (self):
        u"""自由度名をキー，[ABS目標値，REL目標値]を値にしたディクショナリ．
        アクションが終了しても最後の情報が残っている．
        （SCHEMAはそのポーズをしていることが期待される）
        """
        return self._last_target_info

    @property
    def tick (self):
        return self._tick

if __name__ == '__main__':
    action_dictionary = ActionDictionary ()
    action_dictionary.read ('action')

    context = ActionMasterContext (action_dictionary)

    for i in range(100):
        context.step()

    # context.put ('nod')
    le = ActionLookWithEye (30.0, 30.0)
    print(le.pattern_list[0].pattern)
    print(le.pattern_list[0].final_tick)
    context.put_action_direct (le)
    for i in range(100):
        context.step()
        if len(context.target) != 0:
            print(context.tick, context.actual_target)

    # context.put ('byebye')
    # for i in range(1000):
    #     context.step()
    #     if len(context.actual_target) != 0:
    #         print context.tick, context.actual_target

    # context.cancel ('nod')
    # context.cancel ('byebye')

    # for i in range(10000):
    #     context.step()
    #     if len(context.actual_target) != 0:
    #         print context.tick, context.actual_target
