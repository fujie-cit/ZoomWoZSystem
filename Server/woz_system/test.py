import configparser
import traceback

from .woz_command import parse_wizard_command
from .dialog_context_manager import DialogContextManager
from .query import Query
from .query_generator import QueryGenerator
from .db_api import DB_API
from .dialog_manager import DialogManager
from .natural_language_generator import NaturalLanguageGenerator


def test(config_file_path='config/config.ini'):
    config = configparser.ConfigParser()

    config.read(config_file_path, encoding='utf-8')
    db = DB_API(config)

    context_manager = DialogContextManager(db)
    query_generator = QueryGenerator(context_manager)
    dialog_manager = DialogManager(context_manager, db, config)
    nlg_generator = NaturalLanguageGenerator()

    # genre_id 18はドラマ
    context_manager.append_genre_id(18) 

    woz_command_list = [
        # システム動作系(command_type: action)
        ("look-action", "A"),
        ("nod-action", "A"),
        ("cancel-action", "A"),
        # メタコマンド系（command_type: meta)
        ("change_topic-meta", "えいが・かけグルイ"),
        ("change_person-meta", "はまべみなみ"),
        ("change_genre-meta", "18"), # ドラマ"),
        # 発話系(command_type: active, passive, correction)
        ("start-active", "A"),
        ("summarize-active", "A"),
        ("end-active", "A"),
        ("recommendation-active", "A"),
        ("detail-active", "A"),
        ("question", "A"),
        ("response-passive", "A"),
        ("yes-correction", "A"),
        ("no-correction", "A"),
        ("unknown-correction", "A"),
        ("repeat-correction", "A"),
        ("title-correction", "A"),
        ("genre-correction", "A"),
        ("recommendation-correction", "A"),
        ("cast_detail-correction", "A"),
        ("director_detail-correction", "A"),
        ("tips-story-correction", "A"),
        ("tips-info-correction", "A"),
        ("review-correction", "A"),
        ("evaluation-correction", "A"),
        ("cast-correction", "A"),
        ("director-correction", "A"),
    ]

    def check_command(message, target):
        print("Wizard Command: {} {}".format(message, target))

        command, command_arg, command_type, target = \
            parse_wizard_command(message, target)

        print("Parsed Wizard Command:")
        print("  command: {}".format(command))
        print("  command_arg: {}".format(command_arg))
        print("  command_type: {}".format(command_type))
        print("  target: {}".format(target))

        ct = Query.CommandType
        if command_type in [ct.Action, ct.Meta]:
            return

        if command == "repeat":
            execute_repeat_command(command_type, target)
            return

        query = query_generator.generate_query(
            command, command_arg, command_type, target)
        print("Query")
        print("  {}".format(query))

        nlg_command = dialog_manager.generate(query)
        print("NLG Command")
        print("  {}".format(nlg_command))

        utterance = nlg_generator.generate(nlg_command)

        print("Utterance: {}".format(utterance))
        return nlg_command

    def execute_meta_command(command, target):
        qc = Query.CommandName
        if command == qc.ChangeTopic:
            context_manager.append_title(target)
        elif command == qc.ChangePerson:
            context_manager.append_person(target)
        elif command == qc.ChangeGenre:
            context_manager.append_genre_id(int(target))

    def execute_repeat_command(command_type, target):
        nlg_command = context_manager.get_latest_executed_nlg_command()
        if nlg_command is None:
            print("no command found")
            return
        print("NLG Command (Repeat)")
        nlg_command.query.command_type = command_type
        nlg_command.query.target = target
        print("  {}".format(nlg_command))
        utterance = nlg_generator.generate(nlg_command)
        print("Utterance: {}".format(utterance))
        return nlg_command

    def check_commands_in_list(l):
        for i, (message, target) in enumerate(woz_command_list):
            try:
                print("* {}/{} ----------------------------".format(
                    i + 1, len(woz_command_list)))
                check_command(message, target)
            except Exception as e:
                print(traceback.format_exc())

    # 1st check
    print("1st check")
    check_commands_in_list(woz_command_list)

    # 1st context update
    print("update context")
    message, target = "recommendation-correction", "A"
    nlg_command = check_command(message, target)
    context_manager.append_executed_nlg_command(nlg_command)

    # 2nd check
    print("2nd check")
    check_commands_in_list(woz_command_list)

    # 3rd context update
    print("3rd context update")
    message, target = "director-correction", "A"
    nlg_command = check_command(message, target)
    context_manager.append_executed_nlg_command(nlg_command)

    # 3rd check
    print("3rd check")
    check_commands_in_list(woz_command_list)

    # 4th context update
    print("4th context update")
    message, target = "change_topic", "ボヘミアン・ラプソディ"
    command, command_arg, command_type, target = parse_wizard_command(message, target)
    execute_meta_command(command, target)

    # 4th check
    print("4th check")
    check_commands_in_list(woz_command_list)

    # 5th context update
    print("5th context update")
    message, target = "change_person", "はなえなつき"
    command, command_arg, command_type, target = parse_wizard_command(message, target)
    execute_meta_command(command, target)

    # 5th check
    print("5th check")
    check_commands_in_list(woz_command_list)

    # 6th context update
    print("6th context update")
    message, target = "change_genre", "16" # アニメ
    command, command_arg, command_type, target = parse_wizard_command(message, target)
    execute_meta_command(command, target)

    # 6th check
    print("6th check")
    check_commands_in_list(woz_command_list)
