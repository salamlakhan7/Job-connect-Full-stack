import tempfile

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TransactionTestCase, override_settings
from django.urls import reverse

from .models import Application, ChatMessage, ChatRoom, Job, UserProfile
from .routing import websocket_urlpatterns


websocket_application = URLRouter(websocket_urlpatterns)


class ChatAuthorizationTests(TransactionTestCase):
    allowed_statuses = ('shortlisted', 'interview', 'hired')
    blocked_statuses = ('pending', 'reviewed', 'rejected')

    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        self.settings_override = override_settings(
            MEDIA_ROOT=self.media_dir.name,
            CHANNEL_LAYERS={
                'default': {
                    'BACKEND': 'channels.layers.InMemoryChannelLayer',
                },
            },
        )
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)

        self.employer = User.objects.create_user('employer', password='test-pass')
        self.employer_profile = UserProfile.objects.create(
            user=self.employer,
            role='employer',
        )
        self.seeker = User.objects.create_user('seeker', password='test-pass')
        self.seeker_profile = UserProfile.objects.create(
            user=self.seeker,
            role='seeker',
        )
        self.job = Job.objects.create(
            employer=self.employer,
            employer_profile=self.employer_profile,
            company_name='Test Company',
            title='Test Role',
            description='Test role description',
            location='Remote',
        )
        self.application = Application.objects.create(
            job=self.job,
            applicant=self.seeker_profile,
        )
        self.room = ChatRoom.objects.create(
            employer=self.employer,
            seeker=self.seeker,
        )
        self.message = ChatMessage.objects.create(
            room=self.room,
            sender=self.employer,
            content='Existing history',
        )
        self.client = Client()
        self.client.force_login(self.seeker)

    def set_status(self, status):
        self.application.status = status
        self.application.save(update_fields=['status'])

    def test_http_chat_access_for_every_application_status(self):
        for status in self.blocked_statuses + self.allowed_statuses:
            with self.subTest(status=status):
                self.set_status(status)
                is_allowed = status in self.allowed_statuses

                start_response = self.client.get(
                    reverse('chat_start', args=[self.application.id])
                )
                expected_start = (
                    reverse('chat_room', args=[self.room.id])
                    if is_allowed else reverse('chat_list')
                )
                self.assertRedirects(
                    start_response,
                    expected_start,
                    fetch_redirect_response=False,
                )

                room_response = self.client.get(
                    reverse('chat_room', args=[self.room.id])
                )
                self.assertEqual(room_response.status_code, 200 if is_allowed else 302)
                if is_allowed:
                    self.assertContains(room_response, 'Existing history')

                list_response = self.client.get(reverse('chat_list'))
                self.assertEqual(list_response.status_code, 302 if is_allowed else 200)

                job_response = self.client.get(
                    reverse('start_chat_from_job', args=[self.job.id])
                )
                expected_job = (
                    reverse('chat_room', args=[self.room.id])
                    if is_allowed else reverse('job_detail', args=[self.job.id])
                )
                self.assertRedirects(
                    job_response,
                    expected_job,
                    fetch_redirect_response=False,
                )

                upload_response = self.client.post(
                    reverse('chat_upload'),
                    {
                        'conversation_id': self.room.id,
                        'file': SimpleUploadedFile('test.txt', b'test'),
                    },
                )
                self.assertEqual(upload_response.status_code, 200 if is_allowed else 403)

                application_page = self.client.get(reverse('my_applications'))
                self.assertEqual(
                    b'>Chat</a>' in application_page.content,
                    is_allowed,
                )

                job_page = self.client.get(reverse('job_detail', args=[self.job.id]))
                self.assertEqual(
                    b'Message Employer' in job_page.content,
                    is_allowed,
                )

        self.assertTrue(
            ChatMessage.objects.filter(id=self.message.id, content='Existing history').exists()
        )

    def test_job_chat_requires_eligible_application_for_that_job(self):
        self.set_status('shortlisted')
        other_job = Job.objects.create(
            employer=self.employer,
            employer_profile=self.employer_profile,
            company_name='Test Company',
            title='Other Role',
            description='Another role',
            location='Remote',
        )

        response = self.client.get(reverse('start_chat_from_job', args=[other_job.id]))

        self.assertRedirects(
            response,
            reverse('job_detail', args=[other_job.id]),
            fetch_redirect_response=False,
        )

    def test_websocket_connect_follows_status_allowlist(self):
        async def connect():
            communicator = WebsocketCommunicator(
                websocket_application,
                f'/ws/chat/{self.room.id}/',
            )
            communicator.scope['user'] = self.seeker
            connected, _ = await communicator.connect()
            if connected:
                await communicator.disconnect()
            return connected

        for status in self.blocked_statuses + self.allowed_statuses:
            with self.subTest(status=status):
                self.set_status(status)
                self.assertEqual(
                    async_to_sync(connect)(),
                    status in self.allowed_statuses,
                )

    def test_websocket_receive_rechecks_status(self):
        self.set_status('shortlisted')

        async def connect_then_reject():
            communicator = WebsocketCommunicator(
                websocket_application,
                f'/ws/chat/{self.room.id}/',
            )
            communicator.scope['user'] = self.seeker
            connected, _ = await communicator.connect()
            self.assertTrue(connected)

            await database_sync_to_async(
                Application.objects.filter(id=self.application.id).update
            )(status='rejected')
            await communicator.send_json_to({'action': 'send', 'content': 'Blocked'})
            response = await communicator.receive_json_from()
            self.assertEqual(response['action'], 'error')
            await communicator.wait()

        async_to_sync(connect_then_reject)()
        self.assertFalse(
            ChatMessage.objects.filter(room=self.room, content='Blocked').exists()
        )
