from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.db.models.signals import post_save
from .validators import validate_video_url
import os
from django.conf import settings
import random
import string
from django.utils import timezone


class User(AbstractUser):
    is_student = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)

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
    description = models.TextField(blank=True, null=True, verbose_name='Описание квиза')
    stars = models.IntegerField(default=1, verbose_name='Звездочки за квиз')
    assigned_students = models.ManyToManyField('Student', related_name='assigned_quizzes', blank=True, verbose_name='Назначенные студенты')
    is_active = models.BooleanField(default=False, verbose_name='Активен')

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


class Course(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    modules = models.ManyToManyField('Module', blank=True)
    course_code = models.CharField(max_length=5, blank=True, unique=True)
    students = models.ManyToManyField('Student', related_name='enrolled_courses', blank=True)
    teacher = models.ForeignKey('Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='courses', verbose_name='Преподаватель')
    image = models.ImageField(upload_to='image/', null=True, blank=True)  # Новое поле для изображения
    stars = models.IntegerField(default=5, verbose_name='Звёзды за курс', help_text='Количество звёзд, которые получит студент за завершение курса')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.course_code:
            self.course_code = self.generate_course_code()
        super().save(*args, **kwargs)

    def generate_course_code(self, length=5):
        """Генерация случайного кода для курса."""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    
    def is_completed_by(self, student):
        """Проверяет, завершен ли курс конкретным студентом"""
        from .models import QuizAttempt
        
        # Получаем прогресс студента
        student_progress = StudentProgress.objects.filter(user=student.user, course=self).first()
        if not student_progress:
            return False
        
        # Проверяем, что все модули завершены
        all_modules = self.modules.all()
        completed_modules = student_progress.completed_modules.all()
        
        if all_modules.count() != completed_modules.count():
            return False
            
        # Дополнительная проверка: все уроки пройдены и все квизы сданы
        for module in all_modules:
            # Проверяем уроки
            module_lessons = module.lessons.all()
            completed_lessons = student_progress.completed_lessons.filter(module=module)
            if module_lessons.count() != completed_lessons.count():
                return False
                
            # Проверяем квизы  
            module_quizzes = module.quizzes.all()
            for quiz in module_quizzes:
                latest_attempt = QuizAttempt.objects.filter(
                    student=student, 
                    quiz=quiz
                ).order_by('-attempt_number').first()
                
                if not latest_attempt or not latest_attempt.passed:
                    return False
        
        return True
        
    def has_feedback_from(self, student):
        """Проверяет, оставил ли студент отзыв о курсе"""
        return CourseFeedback.objects.filter(student=student, course=self).exists()
    
    def get_average_rating(self):
        """Возвращает среднюю оценку курса"""
        from django.db.models import Avg
        avg_rating = self.feedbacks.aggregate(Avg('rating'))['rating__avg']
        if avg_rating:
            return round(avg_rating, 1)
        return 0


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
    completed_modules = models.ManyToManyField('Module', blank=True, related_name='completed_by_students')

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


class CourseResult(models.Model):
    """Модель для отслеживания завершения курсов и выдачи звёзд"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='Курс')
    completed_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата завершения')
    stars_given = models.BooleanField(default=False, verbose_name='Звёзды выданы')

    class Meta:
        unique_together = ('user', 'course')
        verbose_name = 'Результат курса'
        verbose_name_plural = 'Результаты курсов'
        ordering = ['-completed_date']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.course.title}"


class Student(models.Model):
    GRADE_CHOICES = [
        (1, '1 класс'),
        (2, '2 класс'),
        (3, '3 класс'),
        (4, '4 класс'),
        (5, '5 класс'),
        (6, '6 класс'),
        (7, '7 класс'),
        (8, '8 класс'),
        (9, '9 класс'),
        (10, '10 класс'),
        (11, '11 класс'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    courses = models.ManyToManyField('Course', related_name='students_set', blank=True)
    teacher = models.ForeignKey('Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_students', verbose_name='Преподаватель')
    stars = models.IntegerField(default=0)
    completed_quizzes = models.ManyToManyField(Quiz, through='QuizAttempt', related_name='completed_by')
    blocked_modules = models.ManyToManyField('Module', related_name='blocked_for_students', blank=True)
    profile_edited_once = models.BooleanField(default=False)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    temporary_password = models.CharField(max_length=100, null=True, blank=True)
    is_school_student = models.BooleanField(default=True, verbose_name='Школьник')
    grade = models.IntegerField(choices=GRADE_CHOICES, null=True, blank=True, verbose_name='Класс')
    age = models.IntegerField(null=True, blank=True, verbose_name='Возраст')

    def calculate_level(self):
        """Возвращает номер уровня на основе количества звёзд."""
        level = self.get_level()
        return level.number if level else 1

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

    def get_level(self):
        """Возвращает объект Level, соответствующий количеству звёзд студента."""
        return Level.objects.filter(min_stars__lte=self.stars, max_stars__gt=self.stars).order_by('number').first()

    @property
    def level_name(self):
        level = self.get_level()
        return level.name if level else 'Без уровня'
    
    @property
    def level_number(self):
        """Возвращает номер текущего уровня студента."""
        return self.calculate_level()

    @property
    def level(self):
        """Возвращает объект Level для удобства использования в шаблонах."""
        return self.get_level()

    def save(self, *args, **kwargs):
        """Переопределяем save для дополнительной логики если потребуется."""
        # Можно добавить логику для отслеживания изменений уровня
        old_level = None
        if self.pk:  # Если объект уже существует
            try:
                old_student = Student.objects.get(pk=self.pk)
                old_level = old_student.calculate_level()
            except Student.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)


class WheelSpin(models.Model):
    """Модель для отслеживания спина колеса фортуны"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='wheel_spins')
    stars_earned = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')} ({self.stars_earned} звезд)"
    
    @classmethod
    def can_spin_now(cls, student):
        """Проверяет, может ли студент крутить колесо сейчас (раз в 24 часа)"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Получаем время последнего спина
        last_spin = cls.objects.filter(student=student).order_by('-created_at').first()
        
        if not last_spin:
            return True  # Если никогда не крутил, то можно
        
        # Проверяем, прошло ли 24 часа с последнего спина
        time_since_last_spin = timezone.now() - last_spin.created_at
        return time_since_last_spin >= timedelta(hours=24)
    
    @classmethod
    def get_next_spin_time(cls, student):
        """Возвращает время следующего доступного спина"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Получаем время последнего спина
        last_spin = cls.objects.filter(student=student).order_by('-created_at').first()
        
        if not last_spin:
            return None  # Можно крутить сейчас
        
        # Следующий спин через 24 часа после последнего
        return last_spin.created_at + timedelta(hours=24)
        
        # Проверяем, изменился ли уровень после сохранения
        if old_level is not None:
            new_level = self.calculate_level()
            if old_level != new_level:
                # Можно добавить уведомление о повышении уровня
                try:
                    from .models import Notification
                    level_obj = self.get_level()
                    if level_obj:
                        Notification.objects.create(
                            student=self,
                            type='level_up',
                            message=f'Поздравляем! Вы достигли уровня "{level_obj.name}" ({level_obj.number})!'
                        )
                except Exception as e:
                    print(f"Ошибка при создании уведомления о повышении уровня: {e}")
                    
    def clean(self):
        """Валидация модели."""
        super().clean()
        if self.is_school_student and not self.grade:
            raise ValidationError('Для школьников обязательно указывать класс')
        if not self.is_school_student and self.grade:
            raise ValidationError('Для не школьников класс указывать не нужно')

    def update_stars(self, stars_change, reason=""):
        """Безопасное обновление звезд с проверкой уровня."""
        try:
            old_level = self.calculate_level()
            self.stars = max(0, self.stars + stars_change)
            self.save()
            new_level = self.calculate_level()
            
            # Возвращаем информацию об изменении уровня
            return {
                'old_level': old_level,
                'new_level': new_level,
                'level_changed': old_level != new_level,
                'stars': self.stars
            }
        except Exception as e:
            print(f"Ошибка при обновлении звёзд: {e}")
            # В случае ошибки возвращаем базовую информацию
            return {
                'old_level': 1,
                'new_level': 1,
                'level_changed': False,
                'stars': self.stars
            }


class ProfileEditRequest(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[('pending', 'В ожидании'), ('approved', 'Подтверждено'), ('rejected', 'Отклонено')], default='pending')
    admin_response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)


class CourseAddRequest(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    course_name = models.CharField(max_length=200, verbose_name='Название курса', blank=True, null=True)
    assigned_course = models.ForeignKey('Course', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Назначенный курс')
    comment = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('pending', 'В ожидании'), ('approved', 'Подтверждено'), ('rejected', 'Отклонено')], default='pending')
    admin_response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)


class Notification(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=30, choices=[
        ('general', 'Без темы'),
        ('course_approved', 'Курс добавлен'),
        ('course_rejected', 'Курс отклонён'),
        ('stars_awarded', 'Получены звёзды'),
        ('profile_edit', 'Редактирование профиля'),
        ('level_up', 'Повышение уровня'),
        ('quiz_started', 'Квиз начат'),
        ('quiz_completed', 'Квиз завершён'),
        ('group_added', 'Добавлен в группу'),
        ('rating_changed', 'Изменение в рейтинге'),
        ('request_approved', 'Запрос подтверждён'),
        ('request_rejected', 'Запрос отклонён'),
        ('feedback_submitted', 'Отзыв отправлен'),
        ('achievement_unlocked', 'Открыто достижение'),
    ])
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_popup_shown = models.BooleanField(default=False)  # Показывалось ли всплывающее уведомление
    priority = models.IntegerField(default=1, choices=[
        (1, 'Низкий'),
        (2, 'Средний'),
        (3, 'Высокий'),
        (4, 'Критический'),
    ])
    extra_data = models.JSONField(null=True, blank=True)  # Дополнительные данные для уведомления

    class Meta:
        ordering = ['-created_at']
    
    def get_icon(self):
        """Получить иконку для типа уведомления"""
        icons = {
            'general': '🔔',
            'course_approved': '✅',
            'course_rejected': '❌', 
            'stars_awarded': '⭐',
            'profile_edit': '👤',
            'level_up': '🎉',
            'quiz_started': '📝',
            'quiz_completed': '✅',
            'group_added': '👥',
            'rating_changed': '📊',
            'request_approved': '✅',
            'request_rejected': '❌',
            'achievement_unlocked': '🏆',
        }
        return icons.get(self.type, '📢')
    
    def get_type_display_name(self):
        """Получить читаемое название типа уведомления"""
        # Для всех запросов показываем категорию "Запросы"
        request_types = ['profile_edit', 'request_approved', 'request_rejected', 'course_approved', 'course_rejected']
        if self.type in request_types:
            return 'Запросы'
            
        # Для всех взаимодействий с группами показываем категорию "Группы"
        group_types = ['group_added', 'rating_changed']
        if self.type in group_types:
            return 'Группы'
            
        type_names = {
            'general': 'Уведомление',
            'stars_awarded': 'Получены звёзды',
            'level_up': 'Повышение уровня',
            'quiz_started': 'Квиз начат',
            'quiz_completed': 'Квиз завершён',
            'achievement_unlocked': 'Достижение',
        }
        return type_names.get(self.type, 'Уведомление')


class Achievement(models.Model):
    """Достижения с условиями и подарками."""
    CONDITION_TYPES = [
        ('passed_quizzes', 'Пройдено квизов (>=70%)'),
        ('perfect_quizzes', 'Квизы на 100%'),
        ('completed_courses', 'Завершено курсов'),
        ('total_stars', 'Накоплено звёзд'),
        ('level_reached', 'Достигнут уровень'),
    ]

    code = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    condition_type = models.CharField(max_length=32, choices=CONDITION_TYPES)
    condition_value = models.IntegerField()
    reward = models.CharField(max_length=255, help_text='Название приза/награды (наклейки, футболка и т.д.)')
    reward_icon = models.CharField(max_length=16, blank=True, default='🎁')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['condition_type', 'condition_value']

    def __str__(self):
        return f"{self.title} [{self.code}]"


class StudentAchievement(models.Model):
    """Факт получения достижения студентом."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='unlocked_achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='achievements_unlocked')
    unlocked_at = models.DateTimeField(default=timezone.now)
    notified = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'achievement')
        ordering = ['-unlocked_at']

    def __str__(self):
        return f"{self.student.username} → {self.achievement.title}"


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
    correct_answers = models.IntegerField(default=0)
    incorrect_answers = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    time_taken = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} - Attempt {self.attempt_number}"


class StudentMessageRequest(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=[('pending', 'В ожидании'), ('approved', 'Подтверждено'), ('rejected', 'Отклонено')], default='pending')
    admin_response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    unique_code = models.CharField(max_length=6, unique=True, editable=False, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.unique_code:
            while True:
                code = ''.join(random.choices(string.digits, k=6))
                if not StudentMessageRequest.objects.filter(unique_code=code).exists():
                    self.unique_code = code
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Запрос {self.unique_code or self.id} от {self.student}"


class Level(models.Model):
    number = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=100)
    min_stars = models.PositiveIntegerField()
    max_stars = models.PositiveIntegerField()
    image = models.ImageField(upload_to='levels/', null=True, blank=True, help_text='Изображение уровня (необязательно)')
    description = models.TextField(blank=True, null=True, help_text='Описание уровня')

    class Meta:
        ordering = ['number']
        verbose_name = 'Уровень ученика'
        verbose_name_plural = 'Уровни учеников'

    def __str__(self):
        return f"{self.number}. {self.name} ({self.min_stars}-{self.max_stars} ⭐)"
    
    @property
    def image_url(self):
        """Возвращает URL изображения или заглушку"""
        if self.image:
            return self.image.url
        return None
    
    def get_next_level(self):
        """Возвращает следующий уровень или None, если это последний уровень"""
        try:
            return Level.objects.filter(number__gt=self.number).order_by('number').first()
        except Level.DoesNotExist:
            return None


class CourseFeedback(models.Model):
    """Модель для хранения отзывов студентов о курсах"""
    RATING_CHOICES = [
        (1, 'Очень плохо'),
        (2, 'Плохо'), 
        (3, 'Нормально'),
        (4, 'Хорошо'),
        (5, 'Отлично'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='course_feedbacks')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='feedbacks')
    rating = models.IntegerField(choices=RATING_CHOICES, help_text="Оценка курса от 1 до 5 звезд")
    comment = models.TextField(
        blank=True, 
        null=True, 
        help_text="Комментарий о курсе",
        verbose_name="Отзыв"
    )
    what_liked = models.TextField(
        blank=True,
        null=True,
        help_text="Что понравилось в курсе",
        verbose_name="Что понравилось"
    )
    what_to_improve = models.TextField(
        blank=True,
        null=True,
        help_text="Что можно улучшить",
        verbose_name="Что улучшить"
    )
    would_recommend = models.BooleanField(
        default=True,
        help_text="Рекомендовали бы курс другим",
        verbose_name="Рекомендую другим"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'course']  # Один отзыв на курс от студента
        verbose_name = 'Отзыв о курсе'
        verbose_name_plural = 'Отзывы о курсах'
        ordering = ['-created_at']
    
    def __str__(self):
        stars = '⭐' * self.rating
        return f"{self.student.user.get_full_name() or self.student.user.username} - {self.course.title} ({stars})"
    
    @property
    def stars_display(self):
        """Возвращает звезды в виде эмодзи"""
        return '⭐' * self.rating
    
    @property
    def rating_text(self):
        """Возвращает текстовое описание рейтинга"""
        return dict(self.RATING_CHOICES)[self.rating]

    @property
    def rating_text_only(self):
        """Возвращает только текст рейтинга без звезд"""
        return dict(self.RATING_CHOICES)[self.rating]
    
    def get_stars_range(self):
        """Возвращает диапазон звезд для отображения в шаблоне"""
        return range(self.rating)


class Teacher(models.Model):
    """Модель преподавателя"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    last_name = models.CharField(max_length=100, verbose_name='Фамилия')
    email = models.EmailField(unique=True, verbose_name='Email')
    phone_number = models.CharField(max_length=20, verbose_name='Номер телефона', blank=True, null=True)
    avatar = models.ImageField(upload_to='teacher_avatars/', blank=True, null=True, verbose_name='Фото профиля')
    bio = models.TextField(blank=True, null=True, verbose_name='О преподавателе')
    specialization = models.CharField(max_length=200, blank=True, null=True, verbose_name='Специализация')
                    # experience_years = models.PositiveIntegerField(default=0, verbose_name='Годы опыта')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Преподаватель'
        verbose_name_plural = 'Преподаватели'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        """Полное имя преподавателя"""
        return f"{self.first_name} {self.last_name}"

    @property
    def courses_count(self):
        """Количество курсов преподавателя"""
        return self.courses.count()

    def get_avatar_url(self):
        """Возвращает URL аватара или заглушку"""
        if self.avatar:
            return self.avatar.url
        return None


class Homework(models.Model):
    """Модель домашнего задания"""
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание задания')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='homeworks', verbose_name='Преподаватель')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='assigned_homeworks', verbose_name='Студент')
    pdf_file = models.FileField(upload_to='homework_files/', blank=True, null=True, verbose_name='PDF файл')
    video_url = models.URLField(max_length=500, blank=True, null=True, verbose_name='URL видео')
    due_date = models.DateTimeField(verbose_name='Срок выполнения')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Домашнее задание'
        verbose_name_plural = 'Домашние задания'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.student.user.get_full_name()}"

    @property
    def is_overdue(self):
        """Проверяет, просрочено ли задание"""
        return timezone.now() > self.due_date

    @property
    def status(self):
        """Возвращает статус задания"""
        submission = self.submissions.first()
        if submission:
            if submission.is_submitted:
                return 'submitted'
            elif submission.is_completed:
                return 'completed'
        return 'pending'


class HomeworkSubmission(models.Model):
    """Модель выполнения домашнего задания"""
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='submissions', verbose_name='Домашнее задание')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='homework_submissions', verbose_name='Студент')
    is_submitted = models.BooleanField(default=False, verbose_name='Отправлено')
    is_completed = models.BooleanField(default=False, verbose_name='Завершено')
    submitted_at = models.DateTimeField(blank=True, null=True, verbose_name='Дата отправки')
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name='Дата завершения')
    teacher_comment = models.TextField(blank=True, null=True, verbose_name='Комментарий учителя')
    grade = models.PositiveIntegerField(blank=True, null=True, verbose_name='Оценка', help_text='Оценка от 1 до 10')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Выполнение домашнего задания'
        verbose_name_plural = 'Выполнения домашних заданий'
        unique_together = ['homework', 'student']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.homework.title} - {self.student.user.get_full_name()}"

    def save(self, *args, **kwargs):
        if self.is_submitted and not self.submitted_at:
            self.submitted_at = timezone.now()
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)


class HomeworkPhoto(models.Model):
    """Модель фотографий выполненной работы"""
    submission = models.ForeignKey(HomeworkSubmission, on_delete=models.CASCADE, related_name='photos', verbose_name='Выполнение')
    photo = models.ImageField(upload_to='homework_photos/', verbose_name='Фотография')
    description = models.CharField(max_length=200, blank=True, null=True, verbose_name='Описание')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')

    class Meta:
        verbose_name = 'Фотография домашнего задания'
        verbose_name_plural = 'Фотографии домашних заданий'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Фото {self.id} - {self.submission.homework.title}"




