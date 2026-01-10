import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from .models import ChatRoom, ChatMessage, ChatAttachment

User = get_user_model()
logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.room_id}'

        user = self.scope["user"]
        if user is None or isinstance(user, AnonymousUser):
            logger.warning(f"Anonymous user attempted to connect to chat room {self.room_id}")
            await self.close()
            return

        is_allowed = await self.is_participant(user.id, self.room_id)
        if not is_allowed:
            logger.warning(f"User {user.id} not allowed in chat room {self.room_id}")
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        logger.info(f"User {user.id} ({user.username}) connected to chat room {self.room_id}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get("action", "send")
            
            if action == "typing":
                # Broadcast typing status to room
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "user_typing",
                        "user_id": self.scope["user"].id,
                        "is_typing": True
                    }
                )
                return
            elif action == "stop_typing":
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "user_typing",
                        "user_id": self.scope["user"].id,
                        "is_typing": False
                    }
                )
                return

            # Default action: send message
            message_text = data.get("content", "")
            msg_type = data.get("type", "text")
            attachments = data.get("attachments", []) # List of dicts {file_path, name, size, etc}
            user = self.scope["user"]

            logger.info(f"User {user.id} sending message in room {self.room_id}: {message_text[:50]}")

            # Save to DB
            message = await self.create_message(user.id, self.room_id, message_text, msg_type, attachments)
            
            logger.info(f"Message {message.id} saved to database")

            # Broadcast
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": {
                        "id": message.id,
                        "sender_id": user.id,
                        "sender": user.first_name or user.username, # Use full name preference
                        "content": message.content,
                        "created_at": message.created_at.isoformat(),
                        "attachments": attachments 
                    }
                }
            )
            
            logger.info(f"Message {message.id} broadcasted to room {self.room_group_name}")
            
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}", exc_info=True)
            await self.send(text_data=json.dumps({
                "action": "error",
                "message": "Failed to send message"
            }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "action": "receive",
            "message": event["message"]
        }))

    async def user_typing(self, event):
        await self.send(text_data=json.dumps({
            "action": "typing",
            "user_id": event["user_id"],
            "is_typing": event["is_typing"]
        }))

    # =====================
    # DATABASE METHODS
    # =====================

    @database_sync_to_async
    def is_participant(self, user_id, room_id):
        try:
            room = ChatRoom.objects.get(id=room_id)
            return room.employer_id == user_id or room.seeker_id == user_id
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def create_message(self, user_id, room_id, content, msg_type, attachment_data):
        user = User.objects.get(id=user_id)
        room = ChatRoom.objects.get(id=room_id)
        
        msg = ChatMessage.objects.create(
            room=room,
            sender=user,
            content=content,
            message_type=msg_type
        )
        
        # Link attachments if any
        # The frontend uploaded the file and got a path back. 
        # We need to create ChatAttachment records.
        # Note: In a real app, we might want to validate the file path exists or ownership.
        for att in attachment_data:
            # We assume 'file_path' is relative to MEDIA_ROOT as returned by backend
            ChatAttachment.objects.create(
                message=msg,
                file=att.get('file_path'), 
                content_type=att.get('content_type', 'application/octet-stream'),
                size=att.get('size', 0)
            )
            
        return msg
