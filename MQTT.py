import asyncio

class MQTTServer:
    def __init__(self, on_connect=None, on_disconnect=None, on_message=None):
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_message = on_message
        self.clients = {}  # {client_id: (reader, writer)}
        self.subscriptions = {}  # {topic: set(client_id)}

    async def start(self, host='0.0.0.0', port=1883):
        server = await asyncio.start_server(
            self._handle_client,
            host,
            port
        )
        async with server:
            await server.serve_forever()

    async def publish(self, topic, message):
        """外部调用的发布方法，向所有订阅了指定主题的客户端发送消息"""
        if topic in self.subscriptions:
            # 创建订阅者集合的副本
            subscribers = self.subscriptions[topic].copy()
            for subscriber_id in subscribers:
                await self._send_publish(subscriber_id, topic, message)

    async def _handle_client(self, reader, writer):
        client_id = None
        try:
            while True:
                # 读取固定头的第一个字节
                first_byte = await reader.read(1)
                if not first_byte:
                    break

                # 解析剩余长度
                remaining_length = 0
                multiplier = 1
                while True:
                    byte = await reader.read(1)
                    if not byte:
                        return
                    digit = byte[0]
                    remaining_length += (digit & 127) * multiplier
                    if (digit & 128) == 0:
                        break
                    multiplier *= 128

                # 读取剩余的数据
                payload = await reader.read(remaining_length)
                if not payload:
                    break

                packet_type = first_byte[0] >> 4
                
                if packet_type == 1:  # CONNECT
                    client_id = await self._handle_connect(payload, writer)
                    if client_id:
                        self.clients[client_id] = (reader, writer)
                        if self.on_connect:
                            self.on_connect(client_id)
                elif packet_type == 3:  # PUBLISH
                    if client_id:
                        await self._handle_publish(client_id, payload)
                elif packet_type == 8:  # SUBSCRIBE
                    if client_id:
                        await self._handle_subscribe(client_id, payload, writer)
                elif packet_type == 12:  # PINGREQ
                    await self._handle_pingreq(writer)
                elif packet_type == 14:  # DISCONNECT
                    break

        except Exception:
            pass
        finally:
            if client_id:
                await self._cleanup_client(client_id)

    async def _handle_connect(self, payload, writer):
        protocol_name_length = int.from_bytes(payload[0:2], byteorder='big')
        protocol_level = payload[2+protocol_name_length]
        client_id_length = int.from_bytes(payload[6+protocol_name_length:8+protocol_name_length], byteorder='big')
        client_id = payload[8+protocol_name_length:8+protocol_name_length+client_id_length].decode('utf-8')

        if protocol_level != 0x04:
            writer.write(bytes([0x20, 0x02, 0x00, 0x01]))  # 协议版本不支持
            await writer.drain()
            await writer.close()
            return None

        writer.write(bytes([0x20, 0x02, 0x00, 0x00]))  # CONNACK: Success
        await writer.drain()
        return client_id

    async def _handle_publish(self, client_id, payload):
        current_index = 0
        topic_length = int.from_bytes(payload[current_index:current_index+2], byteorder='big')
        current_index += 2
        topic = payload[current_index:current_index+topic_length].decode('utf-8')
        current_index += topic_length
        message = payload[current_index:].decode('utf-8')

        if self.on_message:
            self.on_message(client_id, topic, message)

        # 广播到订阅者
        if topic in self.subscriptions:
            for subscriber_id in self.subscriptions[topic]:
                if subscriber_id in self.clients and subscriber_id != client_id:
                    await self._send_publish(subscriber_id, topic, message)

    async def _handle_subscribe(self, client_id, payload, writer):
        packet_id = int.from_bytes(payload[0:2], byteorder='big')
        topics = []
        idx = 2
        while idx < len(payload):
            topic_length = int.from_bytes(payload[idx:idx+2], byteorder='big')
            idx += 2
            topic = payload[idx:idx+topic_length].decode('utf-8')
            idx += topic_length
            qos = payload[idx]
            idx += 1
            topics.append((topic, qos))
            print(f"Client {client_id} subscribed to {topic} with QoS {qos}")

        for topic, _ in topics:
            if topic not in self.subscriptions:
                self.subscriptions[topic] = set()
            self.subscriptions[topic].add(client_id)

        suback = bytes([0x90, 2 + len(topics)]) + payload[0:2] + bytes([0x00] * len(topics))
        writer.write(suback)
        await writer.drain()

    async def _handle_pingreq(self, writer):
        writer.write(bytes([0xD0, 0x00]))  # PINGRESP
        await writer.drain()

    async def _cleanup_client(self, client_id):
        if client_id in self.clients:
            reader, writer = self.clients[client_id]
            del self.clients[client_id]
            
            for subscribers in self.subscriptions.values():
                subscribers.discard(client_id)
            
            if not writer.is_closing():
                writer.close()
                await writer.wait_closed()
            
            if self.on_disconnect:
                self.on_disconnect(client_id)

    async def _send_publish(self, client_id, topic, message):
        if client_id not in self.clients:
            return
            
        _, writer = self.clients[client_id]
        try:
            packet_type = 3 << 4
            topic_encoded = topic.encode('utf-8')
            topic_length = len(topic_encoded)
            variable_header = topic_length.to_bytes(2, byteorder='big') + topic_encoded
            payload = message.encode('utf-8')
            remaining_length = len(variable_header) + len(payload)
            
            # 编码剩余长度
            remaining_length_encoded = b''
            while True:
                byte = remaining_length % 128
                remaining_length = remaining_length // 128
                if remaining_length > 0:
                    byte = byte | 0x80
                remaining_length_encoded += bytes([byte])
                if remaining_length == 0:
                    break
                    
            packet = bytes([packet_type]) + remaining_length_encoded + variable_header + payload
            writer.write(packet)
            await writer.drain()
        except Exception as e:
            print(f"Failed to send PUBLISH to {client_id}: {e}")
            await self._cleanup_client(client_id)