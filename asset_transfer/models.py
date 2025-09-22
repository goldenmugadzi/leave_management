from django.db import models

class AssetTransfer(models.Model):
    date = models.DateField()
    serial_number = models.CharField(max_length=100)
    asset_description = models.TextField()
    asset_number = models.CharField(max_length=100)
    transfer_from = models.CharField(max_length=255)
    transfer_to = models.CharField(max_length=255)
    reason_for_transfer = models.TextField()
    signature_sender = models.CharField(max_length=255)
    signature_recipient = models.CharField(max_length=255)

    def __str__(self):
        return f"Transfer {self.serial_number} from {self.transfer_from} to {self.transfer_to}"