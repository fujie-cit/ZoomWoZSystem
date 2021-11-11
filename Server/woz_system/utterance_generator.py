from typing import Text
from .natural_language_generator_command import NaturalLanguageGeneratorCommand
from .dialog_context_manager import DialogContextManager
from .query_generator import QueryGenerator
from .dialog_manager import DialogManager
from .natural_language_generator import NaturalLanguageGenerator
from .text_to_speech import TextToSpeech

from .woz_command import parse_wizard_command

class UtteranceCandidate:
    def __init__(self, 
        nlg_command: NaturalLanguageGeneratorCommand,
        text: str,
        speech_data: bytes
    ):
        self._nlg_command = nlg_command
        self._text = text
        self._speech_data = speech_data
    
    @property
    def nlg_command(self):
        return self._nlg_command

    @property
    def text(self):
        return self._text

    @property
    def speech_data(self):
        return self._speech_data


class UtteranceCandidateGeneratorError(Exception):
    pass


class UtteranceCandidateGenerator:
    def __init__(self,
        context_manager: DialogContextManager,
        query_generator: QueryGenerator,
        dialog_manager: DialogManager,
        natural_language_generator: NaturalLanguageGenerator,
        text_to_speech: TextToSpeech,
    ):
        self._context_manager = context_manager
        self._query_generator = query_generator
        self._dialog_manager = dialog_manager
        self._natural_language_generator = natural_language_generator
        self._text_to_speech = text_to_speech

    def generate(self, message, target):
        command, command_arg, command_type, target = \
            parse_wizard_command(message, target)

        if command == "repeat":
            nlg_command = \
                self._context_manager.get_latest_executed_nlg_command()
            if nlg_command is None:
                raise UtteranceCandidateGeneratorError(
                    "cannot repeat utterance since no NLG command executed."
                )
            # TODO cloneして，command_type, target を更新する
            # nlg_command.query.command_type = command_type
            # nlg_command.query.target = target
            text = self._natural_language_generator.generate(nlg_command)
            speech_data = self._text_to_speech.generate(text)
            utterance_candidate = UtteranceCandidate(
                nlg_command, text, speech_data
            )
            return utterance_candidate
        
        query = self._query_generator.generate_query(
            command, command_arg, command_type, target
        )
        nlg_command = self._dialog_manager.generate(query)
        text = self._natural_language_generator.generate(nlg_command)
        speech_data = self._text_to_speech.generate(text)

        return UtteranceCandidate(nlg_command, text, speech_data)

        
