from typing import Tuple

def parse_wizard_command(message: str, target: str) -> Tuple[str, str, str, str]:
    """Wizardのボタン操作に対応する文字列をパースして，コマンド，タイプ，ターゲットに
    分解する．

    Args:
        message (str): メッセージ（e.g. recommendation-passive）
        target (str): ターゲット（e.g. A）

    Raises:
        ValueError: 与えられたタイプやターゲットが適切な形でない場合

    Returns:
        Tuple[str, str, str, str]: command, command_arg, command_type, target
    """
    
    # メッセージは '{command}(-{command_arg})-{type}' の形で与えられる．
    # {command_arg}は無いときがある．
    msg_split = message.split('-')
    assert 1 <= len(msg_split) <= 3

    command = msg_split[0]
    command_arg = None
    command_type = None
    if len(msg_split) == 2:
        command_type = msg_split[1]
    elif len(msg_split) == 3:
        command_arg = msg_split[1]
        command_type = msg_split[2]

    # command_typeのチェック
    if command_type is not None and \
        command_type not in ['action', 'meta', 'active', 'passive', 'correction']:
        raise ValueError('invalid command type {}'.format(command_type))

    # # targetのチェック
    # if target is not None and \
    #     target not in ['A', 'B']:
    #     raise ValueError('ivalid target {}'.format(target))

    return command, command_arg, command_type, target

if __name__ == "__main__":
    message, target = "recommendation-active", "A"
    message, target = "tips-info-active", "A"
    print(parse_wizard_command(message, target))
