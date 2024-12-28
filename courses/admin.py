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
from .models import Lesson, User, Course, QuizResult, Student, Quiz

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