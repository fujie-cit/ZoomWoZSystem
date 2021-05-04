# coding: utf-8
import mmdagent_schema_client as msc
import sch_action as sa
import threading as th
import time
import readline
# import sch_ss_speaker as ss
# import monea

class ActionPlayer (th.Thread):
    def __init__(self,
                 mmdagent_schema_client,
                 action_master_context):
        th.Thread.__init__(self)
        self._client  = mmdagent_schema_client
        self._context = action_master_context
        self._cond = th.Condition()
        self._time_started = None
        self._running = True
        self.daemon = True

    def run(self):
        self._time_started = time.time()

        while self._running == True:
            with self._cond:
                targets = self._context.actual_target
            for dof, target_deg in targets.items():
                self._client.send (dof, target_deg)

            with self._cond:
                time_to_wait = self._context.tick * 0.01 + self._time_started - time.time()

            # 余った時間だけ寝る
            if time_to_wait > 0.0:
                time.sleep (time_to_wait)
            else:
                if time_to_wait > 0.1:
                    print("delay %f" % (-time_to_wait))
                else:
                    pass

            with self._cond:
                self._context.step()

    def put (self, action_name):
        with self._cond:
            self._context.put (action_name)

    def put_le (self, yaw, pitch):
        with self._cond:
            action = sa.ActionLookWithEye (yaw, pitch, self._context.last_target_info)
            self._context.put_action_direct (action)

    def put_ln (self, yaw, pitch):
        with self._cond:
            action = sa.ActionLookWithNeck (yaw, pitch, self._context.last_target_info)
            self._context.put_action_direct (action)

    def put_lt (self, yaw, pitch):
        with self._cond:
            action = sa.ActionLookWithTurret (yaw, pitch, self._context.last_target_info)
            self._context.put_action_direct (action)

    def cancel (self, action_name):
        with self._cond:
            self._context.cancel (action_name)

"""
class ActionPlayerPlayHandler (monea.ProcessingRequestHandler):
    def __init__ (self, action_player):
        monea.ProcessingRequestHandler.__init__ (self)
        self._player = action_player

    def handleRequest (self, req):
        try:
            name = req.findFirstParam ('actionName').getAsString()
            if name in ('le', 'ln', 'lt'):
                x = req.findFirstParam ('x').toFloat32()
                y = req.findFirstParam ('y').toFloat32()
                if name == 'le':
                    self._player.put_le (x, y)
                elif name == 'ln':
                    self._player.put_ln (x, y)
                else:
                    self._player.put_lt (x, y)
            else:
                self._player.put (name)
        except Exception as e:
            print e

class ActionPlayerCancelHandler (monea.ProcessingRequestHandler):
    def __init__ (self, action_player):
        monea.ProcessingRequestHandler.__init__ (self)
        self._player = action_player

    def handleRequest (self, req):
        try:
            name = req.findFirstParam ('actionName').getAsString ()
            self._player.cancel (name)
        except Exception as e:
            print e

class ActionPlayerMoneaThread (th.Thread):
    DEFAULT_MODULE_XML_FILENAME="sch_action_player.xml"

    def __init__ (self, action_player,
                  module_xml_filename=DEFAULT_MODULE_XML_FILENAME):
        th.Thread.__init__ (self)
        self.__player = action_player
        self.__context = monea.ModuleContextFactory_newContext (module_xml_filename)
        self.__local = self.__context.getLocalModule ()

        self.__play_handler   = ActionPlayerPlayHandler(self.__player)
        self.__cancel_handler = ActionPlayerCancelHandler(self.__player)
        self.daemon = True

    def start (self):
        self.__local.getProcessingRequestQueue ('play').setHandler (
            self.__play_handler)
        self.__local.getProcessingRequestQueue ('cancel').setHandler (
            self.__cancel_handler)
        th.Thread.start (self)

    def run (self):
        time.sleep(1.0)
"""

if __name__ == '__main__':
    client = msc.MMDAgentSchemaClient("192.168.1.14")

    action_dictionary = sa.ActionDictionary ()
    action_dictionary.read ('../action')
    context = sa.ActionMasterContext (action_dictionary)

    # speaker = ss.SchemaSpeaker (client)
    action_player = ActionPlayer(client, context)
    # action_player_monea_thread = ActionPlayerMoneaThread (action_player)

    # speaker.start ()
    action_player.start()
    # action_player_monea_thread.start()

    while True:
        try:
            line = input('> ')
            cmds = line.split(' ')
            if cmds[0] == 'c':
                action_player.cancel(cmds[1])
            elif cmds[0] == 'le':
                yaw, pitch = float(cmds[1]), float(cmds[2])
                action_player.put_le (yaw, pitch)
            elif cmds[0] == 'ln':
                yaw, pitch = float(cmds[1]), float(cmds[2])
                action_player.put_ln (yaw, pitch)
            elif cmds[0] == 'lt':
                yaw, pitch = float(cmds[1]), float(cmds[2])
                action_player.put_lt (yaw, pitch)
            else:
                action_player.put (cmds[0])
        except KeyboardInterrupt:
            break
