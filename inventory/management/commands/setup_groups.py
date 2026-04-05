"""
Management command to set up user groups and permissions.
Usage: python manage.py setup_groups
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from inventory.models import ModelIndent, GPR, ConsumableRegister


class Command(BaseCommand):
    help = 'Creates the Instructors and StoreKeepers groups with appropriate permissions'

    def handle(self, *args, **options):
        # ── Instructors Group ─────────────────────────────
        instructors_group, created = Group.objects.get_or_create(name='Instructors')
        if created:
            self.stdout.write(self.style.SUCCESS('Created group: Instructors'))
        else:
            self.stdout.write('Group "Instructors" already exists.')

        # Instructors can create/view indents
        indent_ct = ContentType.objects.get_for_model(ModelIndent)
        indent_perms = Permission.objects.filter(
            content_type=indent_ct,
            codename__in=['add_modelindent', 'view_modelindent']
        )
        instructors_group.permissions.set(indent_perms)
        self.stdout.write(f'  → Assigned {indent_perms.count()} permission(s) to Instructors')

        # ── StoreKeepers Group ────────────────────────────
        storekeepers_group, created = Group.objects.get_or_create(name='StoreKeepers')
        if created:
            self.stdout.write(self.style.SUCCESS('Created group: StoreKeepers'))
        else:
            self.stdout.write('Group "StoreKeepers" already exists.')

        # StoreKeepers can manage GPR, CR, and view/change indents
        store_perms = []

        # GPR permissions
        gpr_ct = ContentType.objects.get_for_model(GPR)
        store_perms.extend(Permission.objects.filter(content_type=gpr_ct))

        # CR permissions
        cr_ct = ContentType.objects.get_for_model(ConsumableRegister)
        store_perms.extend(Permission.objects.filter(content_type=cr_ct))

        # Indent view + change (for merging)
        indent_manage_perms = Permission.objects.filter(
            content_type=indent_ct,
            codename__in=['view_modelindent', 'change_modelindent']
        )
        store_perms.extend(indent_manage_perms)

        storekeepers_group.permissions.set(store_perms)
        self.stdout.write(f'  → Assigned {len(store_perms)} permission(s) to StoreKeepers')

        self.stdout.write(self.style.SUCCESS('\n✓ Groups setup complete!'))
