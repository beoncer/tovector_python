from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from core.models import Vectorization
import os

class Command(BaseCommand):
    help = 'Cleans up expired vectorization files'

    def handle(self, *args, **kwargs):
        # Get all expired vectorizations
        expired = Vectorization.objects.filter(
            expires_at__lt=timezone.now(),
            status='COMPLETED'
        )
        
        count = 0
        for vec in expired:
            try:
                # Delete the file if it exists
                if vec.storage_path:
                    full_path = os.path.join(settings.MEDIA_ROOT, vec.storage_path)
                    if os.path.exists(full_path):
                        os.remove(full_path)
                        count += 1
                
                # Update status to expired
                vec.status = 'EXPIRED'
                vec.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully cleaned up: {vec.filename}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error cleaning up {vec.filename}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully cleaned up {count} expired files')
        ) 