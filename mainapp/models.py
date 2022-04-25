from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser, User
from django.urls import reverse
from django.utils.translation import gettext as _
from django.db import models
from datetime import datetime


class Country(models.Model):
    abbreviation = models.CharField(max_length=2)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Countries'


class Language(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class LanguageLevel(models.Model):

    LEVEL_CHOICES = (('A1', _('Beginner')),
                     ('A2', _('Pre-Intermediate')),
                     ('B1', _('Intermediate')),
                     ('B2', _('Upper-Intermediate')),
                     ('C1', _('Advanced')),
                     ('C2', _('Proficiency')),
                     ('NV', _('NATIVE')))

    level = models.CharField(max_length=2, choices=LEVEL_CHOICES)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE)

    def __str__(self):
        return '{}: {}-{}'.format(str(self.profile), str(self.language), str(self.level))

    def get_absolute_url(self):
        return reverse('profile-language-level', kwargs={'id': self.pk})


class TagsArea(models.Model):
    area = models.CharField(max_length=100, null=False)

    def __str__(self):
        return self.area


class Tag(models.Model):
    tag = models.CharField(max_length=100)
    tag_area = models.ForeignKey(TagsArea, on_delete=models.CASCADE)

    def __str__(self):
        return self.tag


class Profile(models.Model):
    GENDER_CHOICES = (('m', _('male')),
                      ('f', _('female')),
                      ('n', _('prefer not to respond')))

    phoneNumberRegex = RegexValidator(regex=r"^\+?1?\d{8,15}$")

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField(blank=True, null=True)
    avatar = models.ImageField(upload_to='users/%Y/%m/%d', blank=True)
    phone = models.CharField(validators=[phoneNumberRegex], max_length=16, unique=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='n', blank=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True)
    native_in = models.ManyToManyField(Language, related_name='native', blank=True)
    study = models.ManyToManyField(Language, blank=True, through=LanguageLevel)

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name

    def get_absolute_url(self):
        return reverse('profile', kwargs={'profile_id': self.id})

    @property
    def age(self):
        if self.date_of_birth:
            return int((datetime.now().date() - self.date_of_birth).days / 365.25)

    class Meta:
        ordering = ['-user__last_login']


class Partner(models.Model):
    followed = models.ForeignKey('Profile', on_delete=models.DO_NOTHING, related_name="followed")
    follower = models.ForeignKey('Profile', on_delete=models.DO_NOTHING, related_name="follower")
    request_date = models.DateField(auto_now=True)
    response_date = models.DateField(null=True)

    class Meta:
        unique_together = [['followed', 'follower']]

    def __str__(self):
        return self.follower.user.first_name
