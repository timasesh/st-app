from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.db.models.signals import post_save


class User(AbstractUser):
    is_student = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_user_permissions_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username


class Lesson(models.Model):
    title = models.CharField(max_length=100)
    video = models.FileField(upload_to='videos/')
    pdf = models.FileField(upload_to='pdfs/', blank=True, null=True)

    def __str__(self):
        return self.title


class Quiz(models.Model):
    title = models.CharField(max_length=255)
    stars = models.IntegerField(default=1, verbose_name='Звездочки за квиз')

    def __str__(self):
        return self.title

    def questions(self):
        return self.question_set.all()


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text


class Answer(models.Model):
    text = models.CharField(max_length=255)  # Текст ответа
    question = models.ForeignKey(Question, related_name='answers', on_delete=models.CASCADE)
    is_correct = models.BooleanField(default=False)  # Правильный ли ответ

    def __str__(self):
        return f'{self.text} ({"Правильный" if self.is_correct else "Неправильный"})'


class Module(models.Model):
    title = models.CharField(max_length=100)
    lessons = models.ManyToManyField(Lesson)
    description = models.TextField(null=True, blank=True, default="")
    quizzes = models.ManyToManyField(Quiz, blank=True)  # Связь с квизами

    def __str__(self):
        return self.title


import random
import string


class Course(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    modules = models.ManyToManyField('Module', blank=True)
    course_code = models.CharField(max_length=5, blank=True, unique=True)
    students = models.ManyToManyField('Student', related_name='enrolled_courses', blank=True)
    image = models.ImageField(upload_to='image/', null=True, blank=True)  # Новое поле для изображения

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.course_code:
            self.course_code = self.generate_course_code()
        super().save(*args, **kwargs)

    def generate_course_code(self, length=5):
        """Генерация случайного кода для курса."""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


# class StudentProgress(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     course = models.ForeignKey(Course, on_delete=models.CASCADE)
#     completed_lessons = models.ManyToManyField(Lesson, blank=True)
#     progress = models.IntegerField(default=0)
class StudentProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    completed_lessons = models.ManyToManyField(Lesson, blank=True)
    progress = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        self.progress = max(0, min(self.progress, 100))  # Ограничиваем значение от 0 до 100
        super().save(*args, **kwargs)


class QuizResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.IntegerField()
    date_taken = models.DateTimeField(auto_now_add=True)
    total_questions = models.IntegerField(default=0)
    stars_given = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'quiz')

    def __str__(self):
        return f"{self.user} - {self.quiz}"


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    courses = models.ManyToManyField('Course', related_name='students_set')
    stars = models.IntegerField(default=0)
    profile_edited_once = models.BooleanField(default=False)

    @property
    def username(self):
        return self.user.username


class ProfileEditRequest(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[('pending', 'В ожидании'), ('approved', 'Подтверждено'), ('rejected', 'Отклонено')], default='pending')
    admin_response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)


class CourseAddRequest(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    comment = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('pending', 'В ожидании'), ('approved', 'Подтверждено'), ('rejected', 'Отклонено')], default='pending')
    admin_response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)


class Notification(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=30, choices=[
        ('course_approved', 'Курс добавлен'),
        ('course_rejected', 'Курс отклонён'),
        ('stars_awarded', 'Получены звёзды'),
        ('profile_edit', 'Редактирование профиля'),
    ])
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']


class Group(models.Model):
    name = models.CharField(max_length=100, unique=True)
    students = models.ManyToManyField('Student', related_name='groups')

    def __str__(self):
        return self.name




