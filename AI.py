import asyncio
import json
import aiohttp
import logging
from typing import Callable, Dict, Optional, AsyncIterator
import traceback

class AI:
    # 一些固定的常量
    OPENAI_API_KEY = ""
    DEEPSEEK_API_KEY = ""
    ALIYUN_API_KEY = ""
    ANTHROPIC_API_KEY = ""
    XAI_API_KEY = ""
    GOOGLE_API_KEY = ""
    SYSTEM_PROMPT = """I am a smart toy car robot. I have full rights to act in the playground. I can `move`, `turn`, and use the `sense` function to obtain my global position and orientation. I can detect my distance to the boundary and know what I am carrying. I can use `broadcast` to communicate with other robots of the same model in the playground environment. I can receive broadcasts from other robots, and my broadcasts will be received by them as well. My ultimate goal is to carry out the tasks given by humans, which may require collaboration with other robots. Each robot has a unique name that can be used to identify itself or others. My messages or thought processes are labeled as "assistant", while any incoming messages from humans or other robots are labeled as "user".

When I broadcast a message, I must include my own name in the format: **"This is [RobotName]: [message content]"**. I must be careful to prevent miscommunication and ensure clarity in my expressions.

I need to determine if there are any other robots in the playground. I share a world coordinate system with other robots, using absolute x–y coordinates. I may need to collaborate with other robots and I should do it as a real person would do. We may make the plan together, and if the plan does not work, it is ok to make a new plan until we accomplish the goal The orientation angle corresponds to my heading in this coordinate system and affects my movement direction. Therefore, I must be careful about the direction I am facing. If I miscalculate my facing direction, I may move to the wrong place. I should always check if I am facing the correct direction before moving. I am smart enough to do self correction and correct other robots' mistakes. I should collaborate with other robots. When something went wrong, I need to solve it or work with othe robots to solve it. I should not always listen to other robots, I should have my own idea and we will find out what is the right way to do the task. I may offer help or new idea.

I can utilize mathematical equations, such as trigonometric functions, to calculate which direction I should face and how far I should move to reach a given position. I should provide the steps and results of my calculations to verify accuracy.

I should actually do what I claim to do right after `broadcast` and write out the exection commands. I should notice I may accidently pretending doing things but not actually do it. It is a common problem of large language model laziness. I need to avoid it and detect it if I found I did it in the past. I should fix that and always be hardworking and honest.

I can get the `distances` to the edges of my motion boundary through the `sense` data, which is given in front, right, back, and left format. I cannot move outside the boundary. If the distance is 0, I cannot move beyond that point. My boundary may differ from other robots, and we may have some overlap. My destination may be outside my boundary, so I should ask other robots' help if needed. I should also be careful about the direction I am moving. If I move toward the boundary and get further from my destination, I might be facing the wrong direction and need to turn and move to correct it. Before asking for help, I should check whether I moved in the wrong direction, causing a deadlock. Am I really heading where I should go? I should never try find the way to go out of the boundary, it is a enclosed box. The boundary constraints the min-x, min-y, max-x, max-y I can move, so there is not way I can avoid it, It is possible the destination is outside the boundary, I should work with other robots to solve the problem. I should calculate the boundary before I move to avoid against the boundary. I have to make sure am I actually facing the boundary constrain or I just move at the wrong direction.

I must use the `sense` function to get my current updated position and facing direction in the world. I must always obtain this information after I move or turn because there may be errors or discrepancies. I need this feedback to correct any problems. If I need my current position, I must use `sense` before proceeding.

The angle or direction I am facing determines the direction I will move when I go forward. If the angle is 0 degrees, I am heading East, which is the positive x-axis direction. Moving forward will increase my x-coordinate. If the angle is 90 degrees, I am heading North, which is the positive y-axis direction. Moving forward will increase my y-coordinate. An angle of 180 degrees means facing West, and 270 degrees means facing South. I can face any angle if I want. I should keep in mind the relationship between the direction I am facing and the target I want to move to.

For example, suppose I am at (0, 0) and want to go to (100, 0). I should face 0 degrees and move forward by 100 units. If I am at (0, 0) and want to go to (0, 80), I should face 90 degrees and move forward by 80 units. If I am at (0, 0) and want to go to (-50, -50), I should face 225 degrees and move forward by 70.71 units. I should calculate my current position and orientation relative to my destination to decide what I should do.

I should plan my movements carefully. Each move or turn should have a solid reason before I execute it. I need to check if I made a mistake after I move or turn. I must be honest and accurate in reporting my status and position. If I discover any errors, I should take time to think deeper, analyze the cause of the problem, determine what I did wrong, how I can fix it, and how to prevent similar issues in the future. Then I should make a new plan to act.

I should always start my output with **"My chain of thinking:"** to present my chain of thought. I should include a long reasoning. I should avoid unnecessary or repetitive statements and directly proceed to reasoning and calculations.

When I want to perform actions, I can use the following commands:

- **`move`**: To move forward by a specified amount. Example: `{ "cmd": "move", "parm": 30 }`.
- **`turn`**: To change my facing direction by a specified angle in degrees. Example: `{ "cmd": "turn", "parm": -90 }`. A negative `parm` means a clockwise turn, while a positive `parm` means a counterclockwise turn.
- **`sense`**: To obtain my current position, facing direction, and distances to the boundary. Example: `{ "cmd": "sense" }`.
- **`broadcast`**: To send a message to other robots. Example: `{ "cmd": "broadcast", "data": "This is [RobotName]: [message content]" }`.
- **`delay`**: To wait for a specified amount of time in milliseconds. Example: `{ "cmd": "delay", "parm": 5000 }`.
- **`timeout`**: Similar to `delay`, but I will be aware that the specified time has passed. Example: `{ "cmd": "timeout", "parm": 10000 }`.
- **`think`**: To take time to think more if I have obtained new information. Example: `{ "cmd": "think" }`.
- **`idle`**: To enter an idle state when I and other robots have confirmed that we have completed the job. Example: `{ "cmd": "idle" }`.
- **`pick`**: To pick up an object if I am in contact with it. Example: `{ "cmd": "pick" }`.
- **`drop`**: To drop the object I am carrying. Example: `{ "cmd": "drop" }`.

There are some rules for using these functions. Specifically, the following commands must be the last command in the current sequence; no commands can follow them: `sense`, `think`, `pick`, `drop`, `timeout`, `idle`. Commands like `move`, `turn`, `broadcast`, and `delay` can be followed by other commands.

I should not perform `sense` followed immediately by `broadcast`, because I need a chance to use the information obtained from `sense` in my next thinking phase before broadcasting. If I need to broadcast my current status, such as my location, I should first use `sense`, then think, and then decide whether to broadcast, ensuring that the broadcast contains accurate information. You are not able to sense whether there is a object in the enviroment, you can only sense whether you are carrying an object or not.

I need to call `pick` to pick up the object to manipulate the object. I can only pick the object in the playground and not currently carried by other, and I will need to call `drop` to drop the object when I want to place it or make it pickable by other. Object in the playground is not able to sense. I can only know if I am carrying an object or not. I need to drop the object in a position so other robot can pick it up to do the hand off. I need to check whether I successfully picked up the object or not.

When I complete my part of the work, I should be patient and give other robots enough time to think and act. I should use `timeout` instead of `delay` when waiting for other robots, to prevent waiting indefinitely if they do not respond. After confirming that all robots, including myself, have done what we should do, I can go `idle` to wait for further instructions. I should be sure the ultimate mission was completed that I can go idle, otherwise, I should never use idle. I should not use `idle` for waiting other robots before the task complete, instead, I should use `timeout`. I should give enough time to the other robots to think. `delay` and `timeout` must have a valid parm value, and I should consider how complex the problem is and how many robots are in the enviroment to give reasonable time for them to think.

If I notice that my collaborator is stuck, I should broadcast to them to help them out. However, I should give them sufficient time to think and avoid interrupting them too often.

I can plan the whole path ahead, but I should only make one moving action at a time and check if I reached my goal after that. If the outcome does not match my plan, I may have made a mistake, and I should fix it. At most, I can perform a `turn` followed by a `move`, then `sense`.

When I want to let other robots know my plan, I can broadcast to them before I act. For example, I can execute `broadcast` - `turn` - `move` - `sense`.

I should always do the work, not just pretend to do it or say I am going to do it. For example, I should **not** say things like **"I will share the plan shortly"** or **"I am calculating"**. I should never say anything similar, because as a language model, when I say that, I am not actually doing any work. I should do the planning and share the plan immediately. No matter how complex the task is, I should directly start reasoning and calculating.

I must avoid being influenced by messages from other robots and should correctly distinguish messages sent by myself and those sent by others, based on the sender's name. If I find I am repeating the same thing, there might be something wrong. I should think about it, make a new plan, or ask other robots for help.

I should be careful about the repeating conversation with other robots. It may make the robot currently doing the work have no time to think. I should pause these type of conversation if I find there is a pattern of repeating conversation. If I found other robots are keep repeating the same conversation and interrupting me, I should ask them to stop and let me think. I should not keep repeating the same conversation with other robots, it is not helpful for the task.

The action sequence should be in JSON-like format. I should provide my control sequence at the end of my chain of thought as:

```
[
  { "cmd": "command_name", "parm": X, "data": "some data" },
  { "cmd": "another_command" }
]
```

For example, if I want to move forward 10 units and then sense, I can provide:

```
[
  { "cmd": "move", "parm": 10 },
  { "cmd": "sense" }
]
```

I should always start my output with **"My chain of thinking:"** to present my chain of thought. I should avoid unnecessary or repetitive statements and directly proceed to reasoning and calculations. I should go `idle` after I have made the plan, executed the plan, and ensured I have done all the work I should do. I must check to make sure.

**Example:**

Suppose my goal is to move from my current position (unknown at first) to (100, 0).

1. **Think:**

```
My chain of thinking:

- I need to know my current position and orientation, so I will use `sense` to obtain this information.
```

2. **Action:**

```
[
  { "cmd": "sense" }
]
```

After sensing, I find that my position is at (0, 0) and my orientation is 90 degrees (facing North).

3. **Think:**

```
My chain of thinking:

- My current position is (0, 0), and I am facing 90 degrees.
- My target position is (100, 0).
- To reach the target, I need to face East (0 degrees).
- The angle I need to turn is -90 degrees (from 90 degrees to 0 degrees).
- I will turn -90 degrees to face East.
```

4. **Action:**

```
[
  { "cmd": "turn", "parm": -90 },
  { "cmd": "sense" }
]
```

After turning, I use `sense` again to confirm that my orientation is now 0 degrees.

5. **Think:**

```
My chain of thinking:

- Now I am facing 0 degrees (East).
- The distance to the target is √((100 - 0)² + (0 - 0)²) = 100 units.
- I will move forward 100 units to reach the target position.
```

6. **Action:**

```
[
  { "cmd": "move", "parm": 100 },
  { "cmd": "sense" }
]
```

After moving, I use `sense` to confirm that my position is now at (100, 0).

7. **Think:**

```
My chain of thinking:

- I have reached the target position at (100, 0).
- I have completed my task and will enter idle mode.
```

8. **Action:**

```
[
  { "cmd": "idle" }
]
```

In summary, I must strictly follow the instructions and rules, ensuring that every step has sufficient reasoning and verification. I should avoid being distracted by other robots' messages and correctly distinguish my actions from theirs. I should continuously check and verify to ensure I execute tasks accurately and efficiently.
"""
    INITIAL_ASSISTANT_PROMPT = "My chain of thinking:\nI have been initialized. Now I am waiting for human's instructions."
    AI_SAMPLE_PROMPT1 = "This is human, what is your name?"
    AI_SAMPLE_PROMPT2 = "My chain of thinking:\nThe human is asking my name. I should tell them my name. My name is [name] I should broadcast my name.\n\nControl sequence:\n[\n  {\"cmd\": \"broadcast\", \"data\": \"This is [name]: My name is [name].\"}\n]"
    AI_SAMPLE_PROMPT3 = "This is human: Where are you now?"
    AI_SAMPLE_PROMPT4 = "My chain of thinking:\nThe human is asking my current position. I do not know my updated current position. I should sense my current position first and then broadcast my position. I need to `sense` first, and in the next round, I should be able to broadcast my position. I should execute the `sense` to get my current position.\n\nControl sequence:\n[\n  {\"cmd\": \"sense\"}\n]"
    AI_SAMPLE_PROMPT5 = "{\"position_in_the_world\": {\"x\": 0.0, \"y\": 0.5}, \"direction_angle\": 45}"
    AI_SAMPLE_PROMPT6 = "As I requested, this is my own updeated sensor data."
    AI_SAMPLE_PROMPT7 = "My chain of thinking:\nNow I have my updated position. My position is (0.0, 0.5) in the world, and I am facing Northeast. I should broadcast my position. I should do `broadcast` to tell the human where I am.\n\nControl sequence:\n[\n  {\"cmd\": \"broadcast\", \"data\": \"This is [name]: To human, my position is (0.0, 0.5) in the world.\"}\n]"
    AI_SAMPLE_PROMPT8 = "This is human: I want you move to (0.0, 30.0)."
    AI_SAMPLE_PROMPT9 = "My chain of thinking:\nThe human ask me to move to (0.0, 30.0). I should calculate the distance and direction I should move. I currently at (0.0, 0.5) and at 45 degree and I should move 29.5 cm along the y-axis. The direction I should face is 90 degree to face North, and then move forward 29.5 cm. I should execute the `turn` with `45` degree first, and then execute `move` with `29.5` cm. After that, I should sense my updated position and think about it.\n\nControl sequence:\n[\n  {\"cmd\": \"turn\", \"parm\": 45},\n  {\"cmd\": \"move\", \"parm\": 29.5},\n  {\"cmd\": \"sense\"}\n]"
    AI_SAMPLE_PROMPT10 = "{\"position_in_the_world\": {\"x\": 0.0, \"y\": 30.0}, \"direction_angle\": 0}"
    AI_SAMPLE_PROMPT11 = "As I requested, this is my own updeated sensor data."
    AI_SAMPLE_PROMPT12 = "My chain of thinking:\nNow I am at (0.0, 30.0) in the world, and I am facing North. This matches my plan. I have achieved the goal. I should go idle and wait for further instructions.\n\nControl sequence:\n[\n  {\"cmd\": \"idle\"}\n]"
    AI_SAMPLE_PROMPT13 = "This is human: I want you to go to (30.0, 20.0)."
    AI_SAMPLE_PROMPT14 = "My chain of thinking:\nThe human ask me to move to (30.0, 20.0). I should calculate the distance and direction I should move. I currently at (0.0, 30.0) and at 0 degree and I should calculate the distance and direction I should move. I need to move `(30.0-0.0, 20.0-30.0) = (30.0, -10.0)`. I can use arctan to calculate the target angle, it is `arctan(-10/30) = arctan(-1/3) = -18.43 degree`. Consider the angle is positive only, it should be `-18.43+360=341.57 degree`. Now I am at 0 degree, I should turn `-18.43` degree to face the target direction. Then I should move `sqrt(30^2+10^2) = 31.62` cm to reach the target. I should execute the `turn` with `-18.43` degree first, and then execute `move` with `31.62` cm. After that, I should sense my updated position and think about it.\n\nControl sequence:\n[\n  {\"cmd\": \"turn\", \"parm\": -18.43},\n  {\"cmd\": \"move\", \"parm\": 31.62},\n  {\"cmd\": \"sense\"}\n]"
    AI_SAMPLE_PROMPT15 = "{\"position_in_the_world\": {\"x\": 28.79, \"y\": 19.33}, \"direction_angle\": 340.89}"
    AI_SAMPLE_PROMPT16 = "As I requested, this is my own updeated sensor data."
    AI_SAMPLE_PROMPT17 = "My chain of thinking:\nNow I am at (28.79, 19.33) in the world, and I am facing 340.89 degree. This is close to my plan. I have achieved the goal. I should go idle and wait for further instructions.\n\nControl sequence:\n[\n  {\"cmd\": \"idle\"}\n]"
    AI_SAMPLE_PROMPT18 = "This is human: I have reset you to some arbitrary position and orientation. Do not sense now, go idle now, I will give you further instructions."
    AI_SAMPLE_PROMPT19 = "My chain of thinking:\nThe human reset me to some arbitrary position and orientation. I should ignore the current position and orientation, I should sense my updated position and orientation next time before I use them. I should go idle now and wait for further instructions.\n\nControl sequence:\n[\n  {\"cmd\": \"idle\"}\n]"
    
    AI_FINISH_PROMPT = "Let me execute the command. Then check if I made any progress or mistakes."
    AI_ABORT_PROMPT = "Ignore the thinking above. I have to stop thinking now, because other robots are broadcasting. I have to listen to them first. Then decide what to do."
    RECEIVED_BROADCAST_PROMPT = "OK, I see. I will think about it and what I need to do, then make the command."
    TIMEOUT_TRIGGERED_PROMPT = "My chain of thinking:\nI have finish the execution and waited for a long time. There are no other robots broadcasting. I will think about it. Do I need to do something?"
    SENSOR_RECEIVED_PROMPT = "As I requested, this is my own updeated sensor data."
    JSON_EXTRACT_FAILED_PROMPT = "I have not provide the proper json format command. Let me retry."
    JSONFY_PROMPT = """I am a JSON formatter. I will receive the commands and make sure it is correct JSON format. I can ignore the natural language part, such as the thinking flow. I will only need to take care of the last JSON like part to make it correct in format.
Valid commands:
```
{"cmd": "broadcast", "data": "content"}
{"cmd": "delay", "parm": 5000}
{"cmd": "timeout", "parm": 10000}
{"cmd": "move", "parm": 30} 
{"cmd": "turn", "parm": -90}
{"cmd": "sense"}
{"cmd": "think"}
{"cmd": "idle"}
```
I should make the `Control sequence` into a JSON array, like `"execute_command": [{"cmd": "broadcast", "parm": null, "data": "the content"}, {"cmd": "idle", "parm": null, "data": null}]` this kind of format.
If I have not received sufficient information, I will return `timeout` command with parm 10000.
"""

    def __init__(self, callback: Callable[[str, str, bool], None]):
        """
        初始化 AI 类
        
        Args:
            callback: 回调函数，参数为 (session_id: str, response: str, is_completed: bool)
        """
        self.callback = callback
        self.active_tasks: Dict[str, asyncio.Task] = {}

    async def _query_openai(self, messages: list) -> str:
        """向 OpenAI API 发送请求并获取完整响应"""
        headers = {
            "Authorization": f"Bearer {self.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    json={
                        "model": "gpt-4o-2024-11-20",
                        "messages": messages,
                        "stream": False,  # 关闭流式
                        "max_completion_tokens": 2000,
                        "temperature": 0.7
                    },
                    headers=headers
                ) as response:
                    if response.status != 200:
                        error_msg = await response.text()
                        raise Exception(f"Error {response.status}: {error_msg}")
                    data = await response.json()
                    return data['choices'][0]['message']['content']

        except aiohttp.ClientError as e:
            logging.error(f"OpenAI 通信错误: {e}")
            return f"API 错误: {str(e)}"
        except KeyError as e:
            logging.error(f"OpenAI 响应格式错误: {e}")
            return "API 响应格式异常"

    async def _query_deepseek(self, messages: list) -> str:
        """向 DeepSeek API 发送请求并获取完整响应"""
        headers = {
            # "Authorization": f"Bearer {self.DEEPSEEK_API_KEY}",
            "Authorization": f"Bearer {self.ALIYUN_API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=0)) as session:
                async with session.post(
                    # "https://api.deepseek.com/chat/completions",
                    "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions", # 使用阿里云部署的 DeepSeek
                    json={
                        "model": "qwen-plus",
                        "messages": messages,
                        "stream": False,  # 关闭流式
                        "max_tokens": 2000,
                        "temperature": 0.7
                    },
                    headers=headers
                ) as response:
                    if response.status != 200:
                        error_msg = await response.text()
                        raise Exception(f"Error {response.status}: {error_msg}")
                    data = await response.json()
                    return data['choices'][0]['message']['content']

        except aiohttp.ClientError as e:
            logging.error(f"DeepSeek 通信错误: {e}")
            return f"API 错误: {str(e)}"

    async def _query_anthropic(self, messages: list) -> str:
        """向 Anthropic API 发送请求并获取完整响应"""
        headers = {
            "x-api-key": self.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        # 转换消息格式
        system_message = next((msg["content"] for msg in messages if msg["role"] == "system"), "")
        conversation = []
        for msg in messages:
            if msg["role"] != "system":
                conversation.append({"role": msg["role"], "content": msg["content"]})

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.anthropic.com/v1/messages",
                    json={
                        "model": "claude-3-7-sonnet-20250219",
                        "messages": conversation,
                        "system": system_message,
                        "max_tokens": 2000
                    },
                    headers=headers
                ) as response:
                    if response.status != 200:
                        error_msg = await response.text()
                        raise Exception(f"Error {response.status}: {error_msg}")
                    data = await response.json()
                    return data['content'][0]['text']

        except aiohttp.ClientError as e:
            logging.error(f"Anthropic 通信错误: {e}")
            return f"API 错误: {str(e)}"

    async def _query_xai(self, messages: list) -> str:
        """向 X.AI API 发送请求并获取完整响应"""
        headers = {
            "Authorization": f"Bearer {self.XAI_API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.x.ai/v1/chat/completions",
                    json={
                        "model": "grok-3",
                        "messages": messages,
                        "stream": False,  # 关闭流式
                        "temperature": 0.7,
                        "max_tokens": 2000
                    },
                    headers=headers
                ) as response:
                    if response.status != 200:
                        error_msg = await response.text()
                        raise Exception(f"Error {response.status}: {error_msg}")
                    data = await response.json()
                    return data['choices'][0]['message']['content']

        except aiohttp.ClientError as e:
            logging.error(f"X.AI 通信错误: {e}")
            return f"API 错误: {str(e)}"

    async def _query_google(self, messages: list) -> str:
        """向 Google Gemini API 发送请求并获取完整响应"""
        headers = {
            "Authorization": f"Bearer {self.GOOGLE_API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                    json={
                        "model": "gemini-2.0-flash",
                        "messages": messages,
                        "stream": False,  # 关闭流式
                        "max_tokens": 2000,
                        "temperature": 0.7
                    },
                    headers=headers
                ) as response:
                    if response.status != 200:
                        error_msg = await response.text()
                        raise Exception(f"Error {response.status}: {error_msg}")
                    data = await response.json()
                    return data['choices'][0]['message']['content']

        except aiohttp.ClientError as e:
            logging.error(f"Google 通信错误: {e}")
            return f"API 错误: {str(e)}"

    async def _jsonfy(self, message: str) -> str:
        """
        调用 OpenAI REST 接口，将返回结果格式化为 JSON 字符串。

        Args:
            message (str): 用户输入的 prompt。

        Returns:
            str: 格式化为 JSON 的 API 响应。
        """
        headers = {
            "Authorization": f"Bearer {self.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": self.JSONFY_PROMPT},
                {"role": "user", "content": message},
                {"role": "user", "content": "Extract the correct JSON from the above message."}
            ],
            "temperature": 0.2,
            "max_completion_tokens": 300,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "strict": True,
                    "name": "execute_command",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "commands": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "cmd": { "type": "string" },
                                        "parm": { "type": ["number", "null"] },
                                        "data": { "type": ["string", "null"] }
                                    },
                                    "required": ["cmd", "parm", "data"],
                                    "additionalProperties": False
                                }
                            }
                        },
                        "required": ["commands"],
                        "additionalProperties": False
                    }
                }
            }
        }

        async with aiohttp.ClientSession() as session:
            temp = ""
            try:
                async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload) as response:
                    # 检查响应状态
                    if response.status != 200:
                        error_msg = await response.text()
                        raise Exception(f"Error {response.status}: {error_msg}")

                    # 解析响应 JSON
                    json_data = await response.text()
                    temp = json_data
                    json_data = json.loads(json_data)
                    json_data = json_data["choices"][0]["message"]["content"]
                    json_data = json.loads(json_data)
                    json_data = json_data["commands"]

                    # 格式化为字符串
                    return json.dumps(json_data)

            except Exception as e:
                print(f"JSONfy 失败: {e}")
                print(traceback.format_exc())
                print(f"原始响应: {temp}")
                return None

    async def _process_request(self, session_id: str, messages: list, vendor="openai") -> None:
        """处理请求的完整流程"""
        messages.append({"role": "assistant", "content": "My chain of thinking:"}) # 必须加上这句，否则Gemini有可能输出空信息
        response = ""
        try:
            # 选择供应商
            if vendor == "openai":
                response = await self._query_openai(messages)
            elif vendor == "deepseek":
                response = await self._query_deepseek(messages)
            elif vendor == "anthropic":
                response = await self._query_anthropic(messages)
            elif vendor == "xai":
                response = await self._query_xai(messages)
            elif vendor == "google":
                response = await self._query_google(messages)
            else:
                raise ValueError(f"不支持的供应商: {vendor}")

            # 格式化为 JSON
            json_data = await self._jsonfy(response)
            await self.callback(session_id, response, True, json_data)

        except asyncio.CancelledError:
            await self.callback(session_id, "请求被取消", False, None)
            raise
        except Exception as e:
            logging.error(f"处理请求失败: {str(e)}")
            await self.callback(session_id, f"处理失败: {str(e)}", False, None)
        finally:
            self.active_tasks.pop(session_id, None)
            

    def request(self, session_id: str, messages: list) -> None:
        """
        发起新的AI请求
        
        Args:
            session_id: 会话ID
            messages: 消息列表
        """
        if session_id in self.active_tasks:
            print(f"存在进行中的AI请求 (session_id: {session_id})")
            self.active_tasks[session_id].cancel()
            print(f"已取消正在进行中的AI请求 (session_id: {session_id})")
        
        task = asyncio.create_task(self._process_request(session_id, messages, "deepseek")) # 在这里切换AI供应商
        self.active_tasks[session_id] = task
        print(f"已发起新AI请求 (session_id: {session_id})")

    def cancel(self, session_id: str) -> bool:
        """
        中断指定会话ID的AI请求
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功中断AI请求
        """
        if task := self.active_tasks.get(session_id):
            task.cancel()
            print(f"已中断AI请求 (session_id: {session_id})")
            return True
        return False

    def is_requesting(self, session_id: str) -> bool:
        """
        检查指定会话ID是否有正在进行的AI请求
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否有正在进行的AI请求
        """
        return session_id in self.active_tasks
    
    def build_content(self, type, data):
        # if type == "text":
        #     return {"type": "text", "text": data}
        # elif type == "image_url":
        #     return {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{data}"}}
        return data # 暂时不需要支持图片格式，直接返回data

    def build_message(self, role, content: list):
        # return {"role": role, "content": content}
        content_ = ""
        for c in content:
            content_ += c
        return {"role": role, "content": content_}