# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from .models import Lesson, User, Course
#
# class UserAdmin(BaseUserAdmin):
#     model = User
#     list_display = ('username', 'is_student', 'is_admin')
#     list_filter = ('is_student', 'is_admin')
#     fieldsets = BaseUserAdmin.fieldsets + (
#         (None, {'fields': ('is_student', 'is_admin')}),
#     )
#     add_fieldsets = BaseUserAdmin.add_fieldsets + (
#         (None, {'fields': ('is_student', 'is_admin')}),
#     )
#
# admin.site.register(User, UserAdmin)
# admin.site.register(Lesson)
#
# admin.site.register(Course)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Lesson, User, Course, QuizResult, Student, Quiz, StudentMessageRequest, Level, CourseFeedback, CourseResult, Homework, HomeworkSubmission, HomeworkPhoto, WheelSpin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils import timezone

class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ('username', 'is_student', 'is_admin')
    list_filter = ('is_student', 'is_admin')
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('is_student', 'is_admin')}),  # добавляем флаги is_student и is_admin
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': ('is_student', 'is_admin')}),  # добавляем флаги при добавлении нового пользователя
    )

admin.site.register(User, UserAdmin)
admin.site.register(Lesson)

# Регистрируем модель Course с кастомной админкой
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'course_code', 'stars', 'students_count', 'modules_count', 'average_rating')
    list_filter = ('stars',)
    search_fields = ('title', 'description', 'course_code')
    ordering = ('title',)
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'course_code', 'image')
        }),
        ('Звёзды и награды', {
            'fields': ('stars',),
            'description': 'Количество звёзд, которые получит студент за полное завершение курса'
        }),
        ('Связи', {
            'fields': ('modules', 'students'),
            'classes': ('collapse',)
        }),
    )
    filter_horizontal = ('modules', 'students')
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj:  # Только для существующих объектов
            fieldsets = fieldsets + (
                ('Отзывы о курсе', {
                    'fields': (),
                    'description': self.get_feedback_summary(obj)
                }),
            )
        return fieldsets

    def get_feedback_summary(self, obj):
        feedbacks = obj.feedbacks.all()
        if not feedbacks:
            return 'Отзывов пока нет'
        
        summary = f'Всего отзывов: {feedbacks.count()}<br>'
        summary += f'Средняя оценка: {self.average_rating(obj)}⭐<br><br>'
        
        for feedback in feedbacks:
            summary += f'<strong>{feedback.student.user.get_full_name() or feedback.student.user.username}</strong><br>'
            summary += f'Оценка: {feedback.stars_display}<br>'
            if feedback.comment:
                summary += f'Комментарий: {feedback.comment}<br>'
            if feedback.what_liked:
                summary += f'Понравилось: {feedback.what_liked}<br>'
            if feedback.what_to_improve:
                summary += f'Можно улучшить: {feedback.what_to_improve}<br>'
            summary += f'Рекомендует курс: {"Да" if feedback.would_recommend else "Нет"}<br><br>'
        
        return format_html(summary)

    def average_rating(self, obj):
        feedbacks = obj.feedbacks.all()
        if not feedbacks:
            return '0.0'
        avg = sum(f.rating for f in feedbacks) / feedbacks.count()
        return f'{avg:.1f}'
    
    def students_count(self, obj):
        """Количество студентов на курсе"""
        return obj.students.count()
    students_count.short_description = 'Студентов'
    
    def modules_count(self, obj):
        """Количество модулей в курсе"""
        return obj.modules.count()
    modules_count.short_description = 'Модулей'

# Регистрируем модель Quiz
admin.site.register(Quiz)

# Регистрируем модель Student с дополнительными полями для админки
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_school_student', 'grade', 'age', 'phone_number', 'email', 'stars', 'level_name')
    search_fields = ('user__username', 'phone_number', 'email', 'first_name', 'last_name')
    list_filter = ('user__is_student', 'is_school_student', 'grade')
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            ('Основная информация', {
                'fields': ('user', 'phone_number', 'email', 'first_name', 'last_name', 'age', 'avatar')
            }),
            ('Статус обучения', {
                'fields': ('is_school_student', 'grade')
            }),
            ('Курсы и прогресс', {
                'fields': ('courses', 'stars'),
                'classes': ('collapse',)
            }),
        )
        
        if obj:  # Только для существующих студентов
            quiz_attempts = QuizAttempt.objects.filter(student=obj).order_by('-created_at')
            if quiz_attempts:
                attempts_summary = '<h3>История прохождения квизов:</h3>'
                for attempt in quiz_attempts:
                    attempts_summary += f'<strong>{attempt.quiz.title}</strong><br>'
                    attempts_summary += f'Попытка №{attempt.attempt_number}<br>'
                    attempts_summary += f'Результат: {attempt.correct_answers}/{attempt.total_questions} '
                    attempts_summary += f'({(attempt.correct_answers/attempt.total_questions*100):.1f}%)<br>'
                    attempts_summary += f'Статус: {"Пройден" if attempt.passed else "Не пройден"}<br>'
                    if attempt.time_taken:
                        attempts_summary += f'Время: {attempt.time_taken}<br>'
                    attempts_summary += '<br>'
                
                fieldsets += (
                    ('Результаты квизов', {
                        'fields': (),
                        'description': format_html(attempts_summary)
                    }),
                )
        
        return fieldsets
    
    def save_model(self, request, obj, form, change):
        # При создании нового студента устанавливаем is_student=True для связанного пользователя
        if not change:  # Если это создание нового объекта
            if obj.user:
                obj.user.is_student = True
                obj.user.save()
        super().save_model(request, obj, form, change)

admin.site.register(QuizResult)


class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'progress')

@admin.register(StudentMessageRequest)
class StudentMessageRequestAdmin(admin.ModelAdmin):
    list_display = ('student', 'message_preview', 'status', 'created_at', 'admin_response_preview')
    list_filter = ('status', 'created_at')
    search_fields = ('student__user__username', 'student__user__first_name', 'student__user__last_name', 'message')
    readonly_fields = ('student', 'message', 'created_at')
    fields = ('student', 'message', 'status', 'admin_response', 'created_at', 'reviewed_at')
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Сообщение'
    
    def admin_response_preview(self, obj):
        if obj.admin_response:
            return obj.admin_response[:50] + '...' if len(obj.admin_response) > 50 else obj.admin_response
        return 'Нет ответа'
    admin_response_preview.short_description = 'Ответ администратора'
    
    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)

@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'min_stars', 'max_stars', 'description')
    ordering = ('number',)
    
    # Добавляем кастомное поле для изображения с предпросмотром
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px; border-radius: 10px;" />', obj.image.url)
        return "Нет изображения"
    image_preview.short_description = 'Предпросмотр изображения'

@admin.register(CourseFeedback)
class CourseFeedbackAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'rating', 'stars_display', 'would_recommend', 'created_at')
    list_filter = ('rating', 'would_recommend', 'created_at', 'course')
    search_fields = ('student__user__username', 'student__user__first_name', 'student__user__last_name', 'course__title', 'comment')
    readonly_fields = ('created_at', 'updated_at', 'stars_display')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('student', 'course', 'rating', 'stars_display')
        }),
        ('Отзыв', {
            'fields': ('comment', 'what_liked', 'what_to_improve', 'would_recommend')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def stars_display(self, obj):
        return obj.stars_display
    stars_display.short_description = 'Звезды'


@admin.register(CourseResult)
class CourseResultAdmin(admin.ModelAdmin):
    """Админка для результатов завершения курсов"""
    list_display = ('user_display', 'course', 'completed_date', 'stars_given_display')
    list_filter = ('stars_given', 'completed_date', 'course')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'course__title')
    ordering = ('-completed_date',)
    readonly_fields = ('completed_date',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'course', 'completed_date')
        }),
        ('Награды', {
            'fields': ('stars_given',),
            'description': 'Были ли выданы звёзды за завершение курса'
        }),
    )
    
    def user_display(self, obj):
        """Отображение пользователя с полным именем"""
        return obj.user.get_full_name() or obj.user.username
    user_display.short_description = 'Студент'
    
    def stars_given_display(self, obj):
        """Красивое отображение статуса выдачи звёзд"""
        if obj.stars_given:
            return format_html('<span style="color: green; font-weight: bold;">✅ Выданы</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;">❌ Не выданы</span>')
    stars_given_display.short_description = 'Звёзды'
    
    def get_queryset(self, request):
        """Оптимизируем запросы"""
        return super().get_queryset(request).select_related('user', 'course')

@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    """Админка для домашних заданий"""
    list_display = ('title', 'teacher', 'student', 'due_date', 'status', 'is_overdue_display')
    list_filter = ('is_active', 'created_at', 'due_date', 'teacher')
    search_fields = ('title', 'description', 'teacher__first_name', 'teacher__last_name', 'student__user__username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'is_overdue_display')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'teacher', 'student')
        }),
        ('Сроки и статус', {
            'fields': ('due_date', 'is_active', 'is_overdue_display')
        }),
        ('Материалы', {
            'fields': ('pdf_file', 'video_url'),
            'classes': ('collapse',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status(self, obj):
        """Отображение статуса задания"""
        submission = obj.submissions.first()
        if submission:
            if submission.is_completed:
                return format_html('<span style="color: green; font-weight: bold;">✅ Завершено</span>')
            elif submission.is_submitted:
                return format_html('<span style="color: orange; font-weight: bold;">📤 Отправлено</span>')
        return format_html('<span style="color: gray; font-weight: bold;">⏳ Не выполнено</span>')
    status.short_description = 'Статус'
    
    def is_overdue_display(self, obj):
        """Отображение просроченности"""
        if obj.is_overdue:
            return format_html('<span style="color: red; font-weight: bold;">⚠️ Просрочено</span>')
        return format_html('<span style="color: green; font-weight: bold;">✅ В сроке</span>')
    is_overdue_display.short_description = 'Просрочено'


@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(admin.ModelAdmin):
    """Админка для выполнения домашних заданий"""
    list_display = ('homework', 'student', 'status', 'grade_display', 'submitted_at')
    list_filter = ('is_submitted', 'is_completed', 'submitted_at', 'completed_at')
    search_fields = ('homework__title', 'student__user__username', 'student__user__first_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'submitted_at', 'completed_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('homework', 'student')
        }),
        ('Статус выполнения', {
            'fields': ('is_submitted', 'is_completed', 'submitted_at', 'completed_at')
        }),
        ('Оценка', {
            'fields': ('grade', 'teacher_comment')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status(self, obj):
        """Отображение статуса выполнения"""
        if obj.is_completed:
            return format_html('<span style="color: green; font-weight: bold;">✅ Завершено</span>')
        elif obj.is_submitted:
            return format_html('<span style="color: orange; font-weight: bold;">📤 Отправлено</span>')
        return format_html('<span style="color: gray; font-weight: bold;">⏳ Не выполнено</span>')
    status.short_description = 'Статус'
    
    def grade_display(self, obj):
        """Отображение оценки"""
        if obj.grade:
            return format_html('<span style="color: blue; font-weight: bold;">{}/10</span>', obj.grade)
        return format_html('<span style="color: gray;">-</span>')
    grade_display.short_description = 'Оценка'


@admin.register(HomeworkPhoto)
class HomeworkPhotoAdmin(admin.ModelAdmin):
    """Админка для фотографий домашних заданий"""
    list_display = ('submission', 'photo_preview', 'description', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('submission__homework__title', 'description')
    ordering = ('-uploaded_at',)
    readonly_fields = ('uploaded_at', 'photo_preview')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('submission', 'photo', 'photo_preview')
        }),
        ('Описание', {
            'fields': ('description',)
        }),
        ('Даты', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )
    
    def photo_preview(self, obj):
        """Предпросмотр фотографии"""
        if obj.photo:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px; border-radius: 10px;" />', obj.photo.url)
        return "Нет фотографии"
    photo_preview.short_description = 'Предпросмотр'


@admin.register(WheelSpin)
class WheelSpinAdmin(admin.ModelAdmin):
    """Админка для спина колеса фортуны"""
    list_display = ('student', 'stars_earned', 'created_at')
    list_filter = ('stars_earned', 'created_at')
    search_fields = ('student__user__username', 'student__user__first_name', 'student__user__last_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('student', 'stars_earned')
        }),
        ('Даты', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student__user')