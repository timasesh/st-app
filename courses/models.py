from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.db.models.signals import post_save
from .validators import validate_video_url
import os
from django.conf import settings


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
    video = models.FileField(upload_to='videos/', blank=True, null=True)
    video_url = models.URLField(
        max_length=500, 
        blank=True, 
        null=True, 
        help_text='URL видео (YouTube, Vimeo, Google Drive, Dropbox, OneDrive)',
        validators=[validate_video_url]
    )
    pdf = models.FileField(upload_to='pdfs/', blank=True, null=True)
    convert_pdf_to_slides = models.BooleanField(
        default=False, 
        help_text='Конвертировать PDF/PPTX в слайды для просмотра на странице'
    )
    converted_slides_status = models.CharField(
        max_length=20, 
        choices=[('pending', 'В ожидании'), ('completed', 'Завершено'), ('failed', 'Ошибка'), ('not_applicable', 'Неприменимо')], 
        default='not_applicable',
        help_text='Статус конвертации PDF/PPTX в слайды'
    )
    slide_count = models.IntegerField(default=0, help_text='Количество сгенерированных слайдов')

    def __str__(self):
        return self.title

    def clean(self):
        if not self.video and not self.video_url and not self.pdf:
            raise ValidationError('Необходимо указать либо видеофайл, либо URL видео, либо PDF/PPTX файл')
        if self.video and self.video_url:
            raise ValidationError('Нельзя указать одновременно видеофайл и URL видео')
        
        if self.convert_pdf_to_slides and not self.pdf:
            raise ValidationError('Для конвертации в слайды необходимо прикрепить PDF/PPTX файл.')


class LessonSlide(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='slides')
    image = models.ImageField(upload_to='slides/')
    order = models.IntegerField()

    class Meta:
        ordering = ['order']
        unique_together = ('lesson', 'order')

    def __str__(self):
        return f'{self.lesson.title} - Slide {self.order}'


@receiver(post_save, sender=Lesson)
def convert_pdf_to_slides_on_save(sender, instance, created, **kwargs):
    # Проверяем флаг, чтобы избежать рекурсии
    if hasattr(instance, '_skip_conversion_signal') and instance._skip_conversion_signal:
        return
    if kwargs.get('raw'): # If model is loading from fixtures, skip conversion
        return

    from .services import handle_lesson_file_conversion
    from .models import LessonSlide # Import here to avoid circular dependency

    if instance.convert_pdf_to_slides and instance.pdf:
        # Устанавливаем временный флаг, чтобы избежать рекурсии при вызове save()
        instance._skip_conversion_signal = True

        # Удаляем существующие слайды, если они есть и урок обновляется
        if not created: 
            instance.slides.all().delete()

        # Обновляем статус и количество слайдов
        instance.converted_slides_status = 'pending'
        instance.slide_count = 0
        instance.save(update_fields=['converted_slides_status', 'slide_count'])
        
        image_paths = handle_lesson_file_conversion(instance)
        
        if image_paths:
            for order, img_path in enumerate(image_paths):
                # Путь должен быть относительным к MEDIA_ROOT
                relative_path = os.path.relpath(img_path, settings.MEDIA_ROOT).replace('\\', '/')
                print(f"DEBUG: img_path = {img_path}")
                print(f"DEBUG: settings.MEDIA_ROOT = {settings.MEDIA_ROOT}")
                print(f"DEBUG: relative_path to save = {relative_path}")
                LessonSlide.objects.create(
                    lesson=instance,
                    image=relative_path,
                    order=order + 1
                )
            instance.converted_slides_status = 'completed'
            instance.slide_count = len(image_paths)
        else:
            instance.converted_slides_status = 'failed'
            instance.slide_count = 0
        
        # Сохраняем окончательный статус. Важно: после этого вызова флаг должен быть удален
        # или обработка флага должна быть завершена, чтобы не мешать будущим сохранениям.
        instance.save(update_fields=['converted_slides_status', 'slide_count'])

        # Удаляем флаг после завершения обработки
        del instance._skip_conversion_signal


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
    courses = models.ManyToManyField('Course', related_name='students_set', blank=True)
    stars = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    experience = models.IntegerField(default=0)
    completed_quizzes = models.ManyToManyField(Quiz, through='QuizAttempt', related_name='completed_by')
    blocked_modules = models.ManyToManyField('Module', related_name='blocked_for_students', blank=True)
    profile_edited_once = models.BooleanField(default=False)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    temporary_password = models.CharField(max_length=100, null=True, blank=True)

    def calculate_level(self):
        return max(1, self.experience // 1000)

    def calculate_progress(self, course):
        # Собираем все уроки и все квизы курса
        all_lessons = set()
        all_quizzes = set()
        for module in course.modules.all():
            all_lessons.update(module.lessons.values_list('id', flat=True))
            all_quizzes.update(module.quizzes.values_list('id', flat=True))
        total_parts = len(all_lessons) + len(all_quizzes)
        if total_parts == 0:
            return 0
        # Завершённые уроки
        completed_lessons = set()
        sp = StudentProgress.objects.filter(user=self.user, course=course).first()
        if sp:
            completed_lessons = set(sp.completed_lessons.values_list('id', flat=True))
        # Завершённые квизы (сданные на 70+)
        from .models import QuizAttempt
        passed_quiz_ids = set(
            QuizAttempt.objects.filter(student=self, quiz__in=all_quizzes, passed=True).values_list('quiz_id', flat=True)
        )
        completed_parts = len(completed_lessons) + len(passed_quiz_ids)
        return int((completed_parts / total_parts) * 100)

    @property
    def username(self):
        return self.user.username

    def __str__(self):
        return self.username


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


class QuizAttempt(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.FloatField()
    passed = models.BooleanField(default=False)
    attempt_number = models.IntegerField(default=1)
    stars_penalty = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} - Attempt {self.attempt_number}"




