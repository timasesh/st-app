from django.urls import path
from . import views

urlpatterns = [
    # Главные страницы
    path('', views.student_login, name='student_login'),
    path('admin_page/', views.admin_page, name='admin_page'),
    path('student_page/', views.student_page, name='student_page'),
    path('profile/', views.student_profile, name='student_profile'),
    path('students/<int:user_id>/', views.student_details, name='student_details'),
    path('logout/', views.logout_view, name='logout'),
    path('success/', views.success_view, name='success'),

    # Курсы
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('delete/course/<int:course_id>/', views.delete_course, name='delete_course'),
    path('create_course/', views.create_course, name='create_course'),

    # Модули
    path('module/details/<int:module_id>/', views.module_details, name='module_details'),
    path('delete/module/<int:module_id>/', views.delete_module, name='delete_module'),
    path('create_module/', views.create_module, name='create_module'),
    path('create_module/<int:module_id>/', views.create_module, name='create_module_with_id'),
    path('add_module_to_course/<int:course_id>/', views.add_module_to_course, name='add_module_to_course'),
    path('detach_module/<int:course_id>/<int:module_id>/', views.detach_module, name='detach_module'),

    # Уроки
    path('show-lessons/', views.show_lessons, name='show_lessons'),
    path('get-lessons/<int:module_id>/', views.get_lessons, name='get_lessons'),
    path('create_lesson/', views.create_lesson, name='create_lesson'),
    path('create_lesson/<int:module_id>/', views.create_lesson, name='create_lesson_with_module'),
    path('delete/lesson/<int:lesson_id>/', views.delete_lesson, name='delete_lesson'),
    path('detach-lesson/<int:lesson_id>/from-module/<int:module_id>/', views.detach_lesson_from_module, name='detach_lesson'),
    path('lesson/<int:lesson_id>/', views.view_lesson, name='view_lesson'),
    path('replace-video/<int:lesson_id>/', views.replace_video, name='replace_video'),
    path('replace-pdf/<int:lesson_id>/', views.replace_pdf, name='replace_pdf'),
    # Квизы
    path('quizzes/', views.quiz_list, name='quiz_list'),
    path('create/', views.create_quiz, name='create_quiz'),
    path('edit/<int:pk>/', views.edit_quiz, name='edit_quiz'),
    path('quiz/<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('delete/quiz/<int:quiz_id>/', views.delete_quiz, name='delete_quiz'),
    path('quiz/<int:quiz_id>/add-question/', views.add_question, name='add_question'),
    path('bind_quiz_to_module/<int:quiz_id>/', views.bind_quiz_to_module, name='bind_quiz_to_module'),
    path('quiz/<int:quiz_id>/submit/', views.submit_quiz, name='submit_quiz'),
    path('quiz/<int:quiz_id>/result/', views.quiz_result, name='quiz_result'),

    # Студенты
    path('delete_student/<int:student_id>/', views.delete_user, name='delete_student'),
    path('students/', views.student_list, name='student_list'),  # Существующий маршрут для списка студентов
    path('students/<int:student_id>/', views.student_details, name='student_details'),
    path('add_student/', views.add_student, name='add_student'),
    path('admin_login/', views.admin_login, name='admin_login'),
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('update_progress/', views.update_progress, name='update_progress'),

]
from django.conf import settings
from django.conf.urls.static import static

