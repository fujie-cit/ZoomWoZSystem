# coding: utf-8
import monea
import readline

MODULE_XML_FILENAME="action_player_client_test.xml"
context = monea.ModuleContextFactory_newContext (MODULE_XML_FILENAME)
remote = context.getRemoteModule ("action_player")
remote_ss = context.getRemoteModule ("speech_synthesizer")

def play (remote, name, x=0.0, y=0.0):
    builder = remote.newProcessingRequestBuilder ('play')
    builder.characters ('actionName', name)
    builder.float32 ('x', x)
    builder.float32 ('y', y)
    builder.sendMessage ()

def cancel (remote, name):
    builder = remote.newProcessingRequestBuilder ('cancel')
    builder.characters ('actionName', name)
    builder.sendMessage ()
    
def speak (remote, content):
    print "speak " + content
    builder = remote.newProcessingRequestBuilder ('speak')
    builder.characters ('content', content)
    builder.sendMessage ()

def stop_speaking (remote):
    builder = remote.newProcessingRequestBuilder ('stop')
    builder.sendMessage ()
    
while True:
    try:
        line = raw_input('> ')
        cmds = line.split(' ')
        if cmds[0] == 's':
            speak (remote_ss, cmds[1])
        elif cmds[0] == 'ss':
            stop_speaking (remote_ss)
        elif cmds[0] == 'c':
            cancel(remote, cmds[1])
        else:
            args = []
            for c in cmds[1:]:
                try:
                    v = float(c)
                    args.append(v)
                except ValueError:
                    v = 0.0
            args = args[:2]
            play (remote, cmds[0], *args)
    except KeyboardInterrupt:
        break
