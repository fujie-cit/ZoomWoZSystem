from aiohttp import web
import aiohttp
import asyncio
import json
from robot_controller import RobotController

app = web.Application()
loop = asyncio.get_event_loop()
rc = RobotController('action1')

async def get_action_info(request):
    conv_num = request.match_info.get('conv_num', None)
    topic = request.match_info.get('topic', None)
    action = request.match_info.get('action', None)
    target = request.match_info.get('target', None)
    detail = request.match_info.get('detail', None)
    print (conv_num)
    print (topic)
    print (action)
    print (target)
    print (detail)
    """
    if action == 'look':
        rc.look_target(target):    
    else:
        rc.utter(topic, action, target, detail)
    """
    res = "successful"
    return web.json_response(res,headers={"Access-Control-Allow-Origin": "*"})

def main():
    app.router.add_get('/woz/{conv_num}/{topic}/{action}/{target}/{detail}', get_action_info)
    handler = app.make_handler()
    f = loop.create_server(handler, '0.0.0.0', 8080)
    srv = loop.run_until_complete(f)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.close()

if __name__=="__main__":
    main()
