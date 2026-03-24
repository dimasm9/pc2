from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Создаёт учетную запись admin/admin при первом запуске.'

    def handle(self, *args, **options):
        User = get_user_model()
        admin_group, _ = Group.objects.get_or_create(name='admin')

        user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'email': 'admin@example.local',
            },
        )

        if created:
            user.set_password('admin')
            user.save(update_fields=['password'])
            self.stdout.write(self.style.SUCCESS('Создан пользователь admin с паролем admin.'))
        else:
            if not user.is_staff or not user.is_superuser:
                user.is_staff = True
                user.is_superuser = True
                user.save(update_fields=['is_staff', 'is_superuser'])
            self.stdout.write('Пользователь admin уже существует.')

        user.groups.add(admin_group)
