from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from .models import User, LeaveRequest

# Create your tests here.

class LeaveWorkflowTest(TestCase):
    def setUp(self):
        self.hr = User.objects.create_user(username='hr', password='hrpass', role='hr')
        self.manager = User.objects.create_user(username='manager', password='managerpass', role='manager')
        self.employee = User.objects.create_user(username='employee', password='employeepass', role='employee', manager=self.manager)
        self.client = APIClient()
        self.client.force_authenticate(user=self.employee)

    def test_leave_request_flow(self):
        # Employee creates leave
        response = self.client.post(reverse('leave-list'), {
            'start_date': '2025-07-10',
            'end_date': '2025-07-12',
            'leave_type': 'CL',
            'reason': 'Vacation',
        })
        self.assertEqual(response.status_code, 201)
        leave_id = response.data['id']

        # Employee submits leave
        response = self.client.post(reverse('leave-submit', args=[leave_id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'submitted')

        # Manager approves
        self.client.force_authenticate(user=self.manager)
        response = self.client.post(reverse('leave-approve', args=[leave_id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'approved_manager')

        # HR approves
        self.client.force_authenticate(user=self.hr)
        response = self.client.post(reverse('leave-approve', args=[leave_id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'approved_hr')

        # Employee tries to cancel (should fail)
        self.client.force_authenticate(user=self.employee)
        response = self.client.post(reverse('leave-cancel', args=[leave_id]))
        self.assertEqual(response.status_code, 400)
