import asyncio
import json
import time
import re
from MQTT import MQTTServer
from LogManager import LogManager
from SessionManager import SessionManager
from AI import AI

# 创建日志管理器
logger = LogManager("D:\Dartmouth\Lab\Smart Car\Proxy\logs.csv")
# 创建会话管理器
session_manager = SessionManager("D:\Dartmouth\Lab\Smart Car\Proxy")
# server
server = None

async def on_ai_complete(session_id, response, success, json_data):
    print(f"--------------------\nsession_id: {session_id},\nresponse: {response},\nsuccess: {success}\n--------------------\n\n")
    if success:
        session_manager.add_record_session(session_id, ai.build_message("assistant", [
            ai.build_content("text", response),
            # ai.build_content("text", ai.AI_FINISH_PROMPT)
            ]))
        logger.insert(session_id, session_manager.get_client_id(session_id), "FINISH", response)
        
        if json_data:
            client_id = session_manager.get_client_id(session_id)
            print(f"Sending JSON data to {client_id}: {json_data}\n\n")
            # 随便找个机会把session_id发回给小车
            await server.publish(client_id, json.dumps({"session_id": session_id}))
            await server.publish(client_id, json_data)
        else:
            print("Extracted JSON data failed")
        #     session_manager.add_record_session(session_id, ai.build_message("assistant", [ai.build_content("text", ai.JSON_EXTRACT_FAILED_PROMPT)]))
        #     ai.request(session_id, session_manager.get_records(session_id))
    else:
        # session_manager.add_record_session(session_id, ai.build_message("assistant", [
        #     ai.build_content("text", response),
        #     ai.build_content("text", ai.AI_ABORT_PROMPT)
        #     ]))
        logger.insert(session_id, session_manager.get_client_id(session_id), "ABORT", response)

# 创建AI实例
ai = AI(on_ai_complete)

def on_connect(client_id):
    session_id = session_manager.create_session(client_id)
    logger.insert(session_id, client_id, "CONNECT", "")
    print(f"Client connected: {client_id}")
    session_manager.add_record(client_id, ai.build_message("system", [
        ai.build_content("text", f"My name is `{client_id}`."),
        ai.build_content("text", ai.SYSTEM_PROMPT),
        ai.build_content("text", f"My name is `{client_id}`."),
        ai.build_content("text", ai.SYSTEM_PROMPT),
        ai.build_content("text", f"My name is `{client_id}`."),
        ai.build_content("text", ai.SYSTEM_PROMPT),
        ]))
    session_manager.add_record(client_id, ai.build_message("assistant", [ai.build_content("text", ai.INITIAL_ASSISTANT_PROMPT)]))

    # session_manager.add_record(client_id, ai.build_message("user", [ai.build_content("text", ai.AI_SAMPLE_PROMPT1)]))
    # session_manager.add_record(client_id, ai.build_message("assistant", [ai.build_content("text", ai.AI_SAMPLE_PROMPT2.replace("[name]", client_id))]))
    # session_manager.add_record(client_id, ai.build_message("user", [ai.build_content("text", ai.AI_SAMPLE_PROMPT3)]))
    # session_manager.add_record(client_id, ai.build_message("assistant", [ai.build_content("text", ai.AI_SAMPLE_PROMPT4)]))
    # session_manager.add_record(client_id, ai.build_message("assistant", [ai.build_content("text", ai.AI_SAMPLE_PROMPT5)]))
    # session_manager.add_record(client_id, ai.build_message("assistant", [ai.build_content("text", ai.AI_SAMPLE_PROMPT6)]))
    # session_manager.add_record(client_id, ai.build_message("assistant", [ai.build_content("text", ai.AI_SAMPLE_PROMPT7.replace("[name]", client_id))]))
    # session_manager.add_record(client_id, ai.build_message("user", [ai.build_content("text", ai.AI_SAMPLE_PROMPT8)]))
    # session_manager.add_record(client_id, ai.build_message("assistant", [ai.build_content("text", ai.AI_SAMPLE_PROMPT9)]))
    # session_manager.add_record(client_id, ai.build_message("assistant", [ai.build_content("text", ai.AI_SAMPLE_PROMPT10)]))
    # session_manager.add_record(client_id, ai.build_message("assistant", [ai.build_content("text", ai.AI_SAMPLE_PROMPT11)]))
    # session_manager.add_record(client_id, ai.build_message("assistant", [ai.build_content("text", ai.AI_SAMPLE_PROMPT12)]))
    # session_manager.add_record(client_id, ai.build_message("user", [ai.build_content("text", ai.AI_SAMPLE_PROMPT13)]))
    # session_manager.add_record(client_id, ai.build_message("assistant", [ai.build_content("text", ai.AI_SAMPLE_PROMPT14)]))
    # session_manager.add_record(client_id, ai.build_message("assistant", [ai.build_content("text", ai.AI_SAMPLE_PROMPT15)]))
    # session_manager.add_record(client_id, ai.build_message("assistant", [ai.build_content("text", ai.AI_SAMPLE_PROMPT16)]))
    # session_manager.add_record(client_id, ai.build_message("assistant", [ai.build_content("text", ai.AI_SAMPLE_PROMPT17)]))
    # session_manager.add_record(client_id, ai.build_message("user", [ai.build_content("text", ai.AI_SAMPLE_PROMPT18)]))
    # session_manager.add_record(client_id, ai.build_message("assistant", [ai.build_content("text", ai.AI_SAMPLE_PROMPT19)]))
    
def on_disconnect(client_id):
    session_id = session_manager.get_session_id(client_id)
    has_requesting = ai.cancel(session_id)
    if has_requesting:
        logger.insert(session_id, client_id, "CANCEL_AI_REQUEST", "on_disconnect")
        time.sleep(0.5) # 等待AI请求取消
    session_manager.close_session(client_id)
    logger.insert(session_id, client_id, "DISCONNECT", "")
    print(f"Client disconnected: {client_id}")
    
def on_message(client_id, topic, message):
    print(f"Message from {client_id} on {topic}: {message}")
    session_id = session_manager.get_session_id(client_id)
    json_message = json.loads(message)
    if (json_message["type"] == "abort_thinking"): # 小车开始收到广播
        ai.cancel(session_id) # 如果有当前正在进行的AI请求，取消
    elif (json_message["type"] == "received_broadcast"): # 小车收到完整广播
        session_manager.add_record(client_id, ai.build_message("user", [ai.build_content("text", "Received Broadcast: " + json_message["content"])]))
        # session_manager.add_record(client_id, ai.build_message("assistant", [ai.build_content("text", ai.RECEIVED_BROADCAST_PROMPT)]))
        # ai.request(session_id, session_manager.get_records(session_id)) # 发起AI请求，不需要，因为收到广播后小车会请求think
    elif (json_message["type"] == "timeout_triggered"): # 超时触发
        ai.cancel(session_id)
        session_manager.add_record(client_id, ai.build_message("assistant", [ai.build_content("text", ai.TIMEOUT_TRIGGERED_PROMPT)]))
        ai.request(session_id, session_manager.get_records(session_id))
    elif (json_message["type"] == "object_manipulation"): # 小车拾取物体
        session_manager.add_record(client_id, ai.build_message("assistant", [ai.build_content("text", json_message["content"])]))
        ai.cancel(session_id)
        ai.request(session_id, session_manager.get_records(session_id))
    elif (json_message["type"] == "sensor"): # 小车回传传感器数据
        session_manager.add_record(client_id, ai.build_message("assistant", [
            ai.build_content("text", ai.SENSOR_RECEIVED_PROMPT),
            ai.build_content("text", json_message["content"])
            ]))
        ai.cancel(session_id)
        ai.request(session_id, session_manager.get_records(session_id))
    elif (json_message["type"] == "think"): # 小车请求AI思考
        ai.cancel(session_id)
        ai.request(session_id, session_manager.get_records(session_id))
    else:
        print(f"Unknown message type: {json_message['type']}, message: {message}")

async def main():
    global server
    server = MQTTServer(
        on_connect=on_connect,
        on_disconnect=on_disconnect,
        on_message=on_message
    )
    
    # 创建一个任务来启动服务器
    server_task = asyncio.create_task(server.start())
    print("Server started")
    
    # 等待服务器运行
    await server_task

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Terminating...")