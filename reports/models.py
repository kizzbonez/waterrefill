from django.db import models

class Reports(models.Model):
    class Meta:
        
        verbose_name_plural = "Reports"
        managed = False  # Don't create a DB table
