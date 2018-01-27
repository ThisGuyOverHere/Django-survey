from datetime import datetime, timedelta
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin
)
from .validators import validate_file_extension

#####


class CustomUserManager(BaseUserManager):

    def _create_user(self, id_card, password, **extra_fields):
        """
        Creates and saves a User with the given id card and password.
        """
        if not id_card:
            raise ValueError('Users must have an identity card')
        user = self.model(
            id_card=id_card,
            **extra_fields      #TODO: normalize_id_card
        )
        # user = self.model(id_card=id_card, email=email, TODO aggiungere i campi necessari in fase di creazione
        #                   date_joined=now)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, id_card, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(id_card, password, **extra_fields)

    # def create_staffuser(self, id_card, password):
    #     """
    #     Creates and saves a staff user with the given id card and password.
    #     """
    #     user = self.create_user(
    #         id_card,
    #         password=password,
    #     )
    #     user.is_staff = True
    #     user.save(using=self._db)
    #     return user

    def create_superuser(self, id_card, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(id_card, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):

    # --- Fields ---
    # Primary Key
    id_card = models.CharField(
        verbose_name='identity card',
        max_length=9,
        unique=True,
    )
    # Mandatory for real identification
    id_card_scan = models.FileField(verbose_name="Scansione ID Card", upload_to="documents/", validators=[validate_file_extension], blank=True)
    email = models.EmailField(verbose_name=('email address'), max_length=254, unique=True, blank=True)
    first_name = models.CharField('first name', max_length=30, blank=True)
    last_name = models.CharField('last name', max_length=30, blank=True)
    # Extra Fields
    # avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    comune = models.CharField('comune', max_length=30, blank=True)
    provincia = models.CharField('provincia', max_length=30, blank=True)
    indirizzo = models.CharField('indirizzo', max_length=120, blank=True)
    date_joined = models.DateTimeField('date joined', default=timezone.now)
    # -- Mandatory for implementation
    is_active = models.BooleanField(default=True)
    # Can login in admin panel
    is_staff = models.BooleanField(default=False)

    # Hook
    objects = CustomUserManager()

    # --- STRINGS ---
    # -- Mandatory for implementation
    # - Unique identifier
    USERNAME_FIELD = 'id_card'
    # - Value returned by get_email_field_name()
    EMAIL_FIELD = 'email'
    # - Field prompted when creating user via createsuperuser
    # REQUIRED_FIELDS = ['date_of_birth', ...]

    # --- METHODS ---
    # - Mandatory for implementation
    def get_full_name(self):
        # The user is identified by their email address
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()
        # return self.id_card

    def get_short_name(self):
        # The user is identified by their email address
        return self.first_name

    def get_absolute_url(self):
        #return reverse('user-detail', args=[str(self.id_card)])
        return reverse('profile')

    def __str__(self):              # __unicode__ on Python 2
        return self.id_card

    # def has_perm(self, perm, obj=None):
    #     "Does the user have a specific permission?"
    #     # Simplest possible answer: Yes, always
    #     return True
    #
    # def has_module_perms(self, app_label):
    #     "Does the user have permissions to view the app `app_label`?"
    #     # Simplest possible answer: Yes, always
    #     return True
    #
    # @property
    # def is_staff(self):
    #     "Is the user a member of staff?"
    #     return self.staff
    #
    # @property
    # def is_admin(self):
    #     "Is the user a admin member?"
    #     return self.admin
    #
    # @property
    # def is_active(self):
    #     "Is the user active?"
    #     return self.active


class Survey(models.Model):
    survey_title = models.CharField(max_length=120)
    survey_description = models.CharField(max_length=255)

    class Meta:
        permissions = (("can_vote", "Vote questions in the survey"),
                       ("can_report", "Can see the results of the survey"),)

    def __str__(self):
        return self.survey_title


class Topic(models.Model):
    topic_title = models.CharField(max_length=120)
    topic_description = models.CharField(max_length=255)
    survey_id = models.ForeignKey(Survey, on_delete=models.CASCADE)

    def __str__(self):
        return self.topic_title

class Question(models.Model):

    question_text = models.CharField(max_length=255)
    # Valutare inserimento ChoiceField
    answer_1 = models.CharField(max_length=255)
    answer_2 = models.CharField(max_length=255)
    answer_3 = models.CharField(max_length=255)
    # Voti ottenuti dalle risposte (abbozzato, si cercherà una soluzione migliore in futuro)
    votes_1 = models.IntegerField(default = 0)
    votes_2 = models.IntegerField(default = 0)
    votes_3 = models.IntegerField(default = 0)
    pub_date = models.DateTimeField('date published')
    topic_id = models.ForeignKey(Topic, on_delete=models.CASCADE)

    __original = None

    def __init__(self, *args, **kwargs):
        super(Question, self).__init__(*args, **kwargs)
        self.__original = [self.answer_1,self.answer_2,self.answer_3,self.question_text]

    def __str__(self):
        return self.question_text

    def save(self, *args, **kwargs):
        if (self.answer_1 != self.__original[0] or self.answer_2 != self.__original[1] or self.answer_3 != self.__original[2] or self.__original[3] != self.question_text):
            self.votes_1 = 0
            self.votes_2 = 0
            self.votes_3 = 0
            Completed.objects.filter(surveyId = self.topic_id.survey_id.id).delete()
            SubscribedSurveyQuestion.objects.filter(questionId = self.pk).delete()

        super(Question, self).save(*args, **kwargs) # Call the "real" save() method.

class Completed(models.Model):
    surveyId = models.ForeignKey(Survey, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

class SubscribedSurveyQuestion(models.Model):
    username = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    surveyId = models.ForeignKey(Survey, on_delete=models.CASCADE)
    questionId = models.ForeignKey(Question, on_delete=models.CASCADE)
    # 0 = false, 1 = true
    completed = models.IntegerField(default=0)
    # Va collegata con le possibili risposte delle relativa Question?
    choice = models.CharField(max_length=255)
    # Chiama datetime.now solo quando aggiunge il record
    # Utility per il futuro:
    # date= models.DateTimeField(default=datetime.now()+timedelta(days=30))
    subscription_date = models.DateTimeField(default=datetime.now, blank=True)

    class Meta:
        unique_together = (("username", "surveyId", "questionId"),)

    def __str__(self):
        return self.choice

