from django.db import models
from django.contrib.auth.models import User

class Timetable(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="timetables")
    slot = models.AutoField(primary_key=True)
    time = models.TimeField()
    monday = models.CharField(max_length=20, blank=True, null=True)
    tuesday = models.CharField(max_length=20, blank=True, null=True)
    wednesday = models.CharField(max_length=20, blank=True, null=True)
    thursday = models.CharField(max_length=20, blank=True, null=True)
    friday = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = "timetable"

class AcademicCalendar(models.Model):
    acdid = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="AcademicCalendars")
    date = models.DateField()
    context = models.CharField(max_length=50)

    class Meta:
        db_table = "AcademicCalendar"