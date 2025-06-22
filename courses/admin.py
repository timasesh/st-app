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
from .models import Lesson, User, Course, QuizResult, Student, Quiz, StudentMessageRequest
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
admin.site.register(Course)

# Регистрируем модель Quiz
admin.site.register(Quiz)

# Регистрируем модель Student с дополнительными полями для админки
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'email')
    search_fields = ('user__username', 'phone_number', 'email')  # Поиск по полям
    list_filter = ('user__is_student',)  # Фильтрация по тому, является ли это студентом
    fields = ('user', 'phone_number', 'email', 'courses')  # Указываем, какие поля отображать в админке
    readonly_fields = ('user',)  # Сделаем поле user только для чтения, так как оно связано с User

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