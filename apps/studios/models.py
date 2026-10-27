from datetime import datetime, timedelta

from django.db import models

from .validators import validate_iana_timezone


class Studio(models.Model):
    name = models.CharField(max_length=200)
    timezone = models.CharField(
        max_length=64,
        validators=[validate_iana_timezone],
    )
    cancellation_cutoff_hours = models.PositiveIntegerField(default=4)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class ClassSession(models.Model):
    studio = models.ForeignKey(
        Studio,
        on_delete=models.CASCADE,
        related_name="classes",
    )
    title = models.CharField(max_length=200)
    starts_at = models.DateTimeField(db_index=True)
    duration_minutes = models.PositiveIntegerField()
    capacity = models.PositiveIntegerField()
    credit_cost = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(capacity__gt=0),
                name="class_capacity_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(duration_minutes__gt=0),
                name="class_duration_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(credit_cost__gt=0),
                name="class_cost_positive",
            ),
        ]

    @property
    def ends_at(self) -> datetime:
        return self.starts_at + timedelta(minutes=self.duration_minutes)

    def __str__(self) -> str:
        return f"{self.title} @ {self.starts_at:%Y-%m-%d %H:%M}"