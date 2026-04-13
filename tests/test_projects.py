"""
tests/test_projects.py — Project model, progress tracking, stage updates
"""
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from projects.models import Project, ProjectStage
from tests.helpers import (
    make_client_user, make_staff_user, make_service,
    make_client, make_project, make_stage,
    ClientLoginMixin, StaffLoginMixin,
)


# ── PROJECT MODEL ─────────────────────────────────────────────────────────────

class ProjectModelTest(TestCase):

    def setUp(self):
        self.user = make_client_user()
        self.service = make_service()
        self.client_obj = make_client(self.user)
        self.project = make_project(self.client_obj, self.service)

    def test_str_contains_title(self):
        self.assertIn(self.project.title, str(self.project))

    def test_default_status_is_not_started(self):
        self.assertEqual(self.project.status, Project.STATUS_NOT_STARTED)

    def test_default_progress_is_zero(self):
        self.assertEqual(self.project.progress_percentage, 0)

    def test_status_badge_mapping(self):
        self.project.status = 'in_progress'
        self.assertEqual(self.project.status_badge, 'primary')
        self.project.status = 'completed'
        self.assertEqual(self.project.status_badge, 'success')
        self.project.status = 'on_hold'
        self.assertEqual(self.project.status_badge, 'warning')
        self.project.status = 'cancelled'
        self.assertEqual(self.project.status_badge, 'danger')

    def test_current_stage_returns_in_progress_stage(self):
        s1 = make_stage(self.project, order=1, status='completed')
        s2 = make_stage(self.project, order=2, status='in_progress')
        make_stage(self.project, order=3, status='pending')
        self.assertEqual(self.project.current_stage, s2)

    def test_current_stage_returns_first_pending_if_none_in_progress(self):
        make_stage(self.project, order=1, status='completed')
        s2 = make_stage(self.project, order=2, status='pending')
        self.assertEqual(self.project.current_stage, s2)

    def test_current_stage_none_when_no_stages(self):
        self.assertIsNone(self.project.current_stage)


# ── PROJECT STAGE MODEL ───────────────────────────────────────────────────────

class ProjectStageModelTest(TestCase):

    def setUp(self):
        self.user = make_client_user()
        self.client_obj = make_client(self.user)
        self.project = make_project(self.client_obj)

    def test_str_contains_project_title_and_stage_name(self):
        stage = make_stage(self.project, name='Site Visit')
        self.assertIn('Site Visit', str(stage))
        self.assertIn(self.project.title, str(stage))

    def test_status_badge_mapping(self):
        stage = make_stage(self.project, status='pending')
        self.assertEqual(stage.status_badge, 'secondary')
        stage.status = 'in_progress'
        self.assertEqual(stage.status_badge, 'primary')
        stage.status = 'completed'
        self.assertEqual(stage.status_badge, 'success')

    def test_status_icon_mapping(self):
        stage = make_stage(self.project, status='completed')
        self.assertIn('check', stage.status_icon)
        stage.status = 'in_progress'
        self.assertIn('arrow', stage.status_icon)

    def test_ordering_by_order_field(self):
        make_stage(self.project, order=3, name='Last')
        make_stage(self.project, order=1, name='First')
        make_stage(self.project, order=2, name='Middle')
        stages = list(self.project.stages.all())
        self.assertEqual(stages[0].name, 'First')
        self.assertEqual(stages[2].name, 'Last')


# ── CLIENT: PROJECT VIEWS ─────────────────────────────────────────────────────

class ClientProjectViewTest(ClientLoginMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.client_obj = make_client(self.client_user)
        self.project = make_project(self.client_obj)
        make_stage(self.project, order=1, name='Site Visit', status='completed')
        make_stage(self.project, order=2, name='Data Collection', status='in_progress')
        make_stage(self.project, order=3, name='Report', status='pending')

    def test_project_list_loads(self):
        response = self.client.get(reverse('project_list'))
        self.assertEqual(response.status_code, 200)

    def test_project_list_shows_own_projects(self):
        response = self.client.get(reverse('project_list'))
        self.assertContains(response, self.project.title)

    def test_project_list_hides_other_users_projects(self):
        other = make_client_user(email='other@example.com')
        other_client = make_client(other)
        other_project = make_project(other_client)
        response = self.client.get(reverse('project_list'))
        self.assertNotContains(response, other_project.title)

    def test_project_detail_loads(self):
        response = self.client.get(reverse('project_detail', args=[self.project.pk]))
        self.assertEqual(response.status_code, 200)

    def test_project_detail_shows_all_stages(self):
        response = self.client.get(reverse('project_detail', args=[self.project.pk]))
        self.assertContains(response, 'Site Visit')
        self.assertContains(response, 'Data Collection')
        self.assertContains(response, 'Report')

    def test_project_detail_shows_progress_percentage(self):
        self.project.progress_percentage = 33
        self.project.save()
        response = self.client.get(reverse('project_detail', args=[self.project.pk]))
        self.assertContains(response, '33')

    def test_project_detail_of_other_user_returns_404(self):
        other = make_client_user(email='other2@example.com')
        other_client = make_client(other)
        other_project = make_project(other_client)
        response = self.client.get(reverse('project_detail', args=[other_project.pk]))
        self.assertEqual(response.status_code, 404)

    def test_project_list_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('project_list'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('project_list')}")


# ── STAFF: STAGE UPDATES ──────────────────────────────────────────────────────

class StaffProjectStageUpdateTest(StaffLoginMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.client_user = make_client_user()
        self.client_obj = make_client(self.client_user, assigned_staff=self.staff_user)
        self.project = make_project(self.client_obj, staff=self.staff_user)
        self.stage = make_stage(self.project, order=1, name='Site Visit', status='pending')

    def test_staff_project_detail_loads(self):
        response = self.client.get(reverse('staff_project_detail', args=[self.project.pk]))
        self.assertEqual(response.status_code, 200)

    def test_staff_can_update_stage_status(self):
        self.client.post(reverse('update_project_stage', args=[self.project.pk]), {
            'stage_id': self.stage.pk,
            'name': self.stage.name,
            'status': 'in_progress',
            'notes': 'Team dispatched to site.',
        })
        self.stage.refresh_from_db()
        self.assertEqual(self.stage.status, 'in_progress')

    def test_staff_can_add_notes_to_stage(self):
        self.client.post(reverse('update_project_stage', args=[self.project.pk]), {
            'stage_id': self.stage.pk,
            'name': self.stage.name,
            'status': 'in_progress',
            'notes': 'Measurements completed, 3 beacons placed.',
        })
        self.stage.refresh_from_db()
        self.assertEqual(self.stage.notes, 'Measurements completed, 3 beacons placed.')

    def test_completing_stage_sets_completed_at(self):
        self.client.post(reverse('update_project_stage', args=[self.project.pk]), {
            'stage_id': self.stage.pk,
            'name': self.stage.name,
            'status': 'completed',
            'notes': 'Done.',
        })
        self.stage.refresh_from_db()
        self.assertIsNotNone(self.stage.completed_at)

    def test_progress_percentage_updates_on_stage_completion(self):
        # 1 of 1 stage completed = 100%
        self.client.post(reverse('update_project_stage', args=[self.project.pk]), {
            'stage_id': self.stage.pk,
            'name': self.stage.name,
            'status': 'completed',
            'notes': '',
        })
        self.project.refresh_from_db()
        self.assertEqual(self.project.progress_percentage, 100)

    def test_progress_percentage_partial(self):
        stage2 = make_stage(self.project, order=2, name='Report', status='pending')
        # Complete only first of 2 stages = 50%
        self.client.post(reverse('update_project_stage', args=[self.project.pk]), {
            'stage_id': self.stage.pk,
            'name': self.stage.name,
            'status': 'completed',
            'notes': '',
        })
        self.project.refresh_from_db()
        self.assertEqual(self.project.progress_percentage, 50)

    def test_all_stages_complete_marks_project_completed(self):
        self.client.post(reverse('update_project_stage', args=[self.project.pk]), {
            'stage_id': self.stage.pk,
            'name': self.stage.name,
            'status': 'completed',
            'notes': '',
        })
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.STATUS_COMPLETED)

    def test_staff_can_add_new_stage(self):
        self.client.post(reverse('update_project_stage', args=[self.project.pk]), {
            'stage_id': '',
            'name': 'New Stage',
            'description': 'A new stage added.',
            'status': 'pending',
            'notes': '',
        })
        self.assertTrue(ProjectStage.objects.filter(
            project=self.project, name='New Stage'
        ).exists())

    def test_stage_update_sets_updated_by(self):
        self.client.post(reverse('update_project_stage', args=[self.project.pk]), {
            'stage_id': self.stage.pk,
            'name': self.stage.name,
            'status': 'in_progress',
            'notes': '',
        })
        self.stage.refresh_from_db()
        self.assertEqual(self.stage.updated_by, self.staff_user)
