from django.urls import path
from . import views
from .views_robots import robots_txt

urlpatterns = [
    # Robots.txt
    path('robots.txt', robots_txt, name='robots_txt'),
    
    # Landing Page
    path('', views.landing_page, name='landing_page'),
    
    # Authentication URLs
    path('login/', views.student_login, name='student_login'),
    path('registration/', views.student_registration, name='student_registration'),
    path('check-username/', views.check_username_availability, name='check_username_availability'),
    path('admin_login/', views.admin_login, name='admin_login'),
    path('teacher_login/', views.teacher_login, name='teacher_login'),
    path('teacher_dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/courses/', views.teacher_courses, name='teacher_courses'),
    path('teacher/courses/<int:course_id>/', views.teacher_course_detail, name='teacher_course_detail'),
    path('teacher/modules/', views.teacher_modules, name='teacher_modules'),
    path('teacher/lessons/', views.teacher_lessons, name='teacher_lessons'),
    path('teacher/quizzes/', views.teacher_quizzes, name='teacher_quizzes'),
    path('teacher/students/', views.teacher_students, name='teacher_students'),
path('teacher/student/progress/', views.teacher_student_progress, name='teacher_student_progress'),
path('teacher/quiz/<int:quiz_id>/questions/', views.teacher_quiz_questions, name='teacher_quiz_questions'),
path('teacher/profile/', views.teacher_profile, name='teacher_profile'),
    
         # Homework URLs
     path('teacher/homework/', views.teacher_homework_page, name='teacher_homework_page'),
     path('teacher/homework/create/', views.teacher_create_homework, name='teacher_create_homework'),
     path('teacher/homework/<int:homework_id>/', views.teacher_homework_detail, name='teacher_homework_detail'),
     path('teacher/homework/submissions/', views.teacher_homework_submissions, name='teacher_homework_submissions'),
     
     # Student Homework URLs
     path('student/homework/', views.student_homework_page, name='student_homework_page'),
     path('student/homework/<int:homework_id>/', views.student_homework_detail, name='student_homework_detail'),
     path('student/homework/<int:homework_id>/submit/', views.student_homework_submit, name='student_homework_submit'),
     path('student/homework/<int:homework_id>/preview/', views.student_homework_preview, name='student_homework_preview'),
     path('student/homework/photo/<int:photo_id>/delete/', views.student_homework_delete_photo, name='student_homework_delete_photo'),
    
    path('logout/', views.logout_view, name='logout'),

    # Main Pages
    path('admin_page/', views.admin_page, name='admin_page'),
    path('admin_students/', views.admin_students_page, name='admin_students_page'),
    path('admin_courses/', views.admin_courses_page, name='admin_courses_page'),
    path('admin_modules/', views.admin_modules_page, name='admin_modules_page'),
    path('admin_lessons/', views.admin_lessons_page, name='admin_lessons_page'),
    path('admin_quizzes/', views.admin_quizzes_page, name='admin_quizzes_page'),
    path('admin_requests/', views.admin_requests_page, name='admin_requests_page'),
    path('admin_notifications/', views.admin_notifications_page, name='admin_notifications_page'),
    path('admin_levels/', views.admin_levels_page, name='admin_levels_page'),
    path('admin_achievements/', views.admin_achievements_page, name='admin_achievements_page'),
    path('admin_teachers/', views.admin_teachers_page, name='admin_teachers_page'),
    path('student_page/', views.student_page, name='student_page'),
    path('student/courses/', views.student_courses_page, name='student_courses_page'),
    path('student/rating/', views.student_rating_page, name='student_rating_page'),
    path('student/levels/', views.student_levels_page, name='student_levels_page'),
    path('student/quizzes/', views.student_quizzes_page, name='student_quizzes_page'),
    path('student/homework-standalone/', views.student_homework_standalone_page, name='student_homework_standalone_page'),
    path('student/requests/', views.student_requests_page, name='student_requests_page'),
    path('profile/', views.student_profile, name='student_profile'),
    path('students/<int:user_id>/', views.student_details, name='student_details'),
    path('success/', views.success_view, name='success'),

    # User Management
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('delete_student/<int:user_id>/', views.delete_user, name='delete_student'),  # Alias for delete_user

    # Course Management
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('delete_course/<int:course_id>/', views.delete_course, name='delete_course'),
    path('create_course/', views.create_course, name='create_course'),
    path('add_module_to_course/<int:course_id>/', views.add_module_to_course, name='add_module_to_course'),
    path('detach_course/<int:user_id>/<int:course_id>/', views.detach_course, name='detach_course'),
    path('remove_course/<int:course_id>/', views.remove_course_from_student, name='remove_course_from_student'),

    # Module Management
    path('module/details/<int:module_id>/', views.module_details, name='module_details'),
    path('delete/module/<int:module_id>/', views.delete_module, name='delete_module'),
    path('create_module/', views.create_module, name='create_module'),
    path('create_module/<int:module_id>/', views.create_module, name='create_module_with_id'),
    path('detach_module/<int:course_id>/<int:module_id>/', views.detach_module, name='detach_module'),

    # Lesson Management
    path('create_lesson/', views.create_lesson, name='create_lesson'),
    path('create_lesson/<int:module_id>/', views.create_lesson, name='create_lesson_with_module'),
    path('delete/lesson/<int:lesson_id>/', views.delete_lesson, name='delete_lesson'),
    path('lesson/<int:lesson_id>/', views.view_lesson, name='view_lesson'),
    path('replace-video/<int:lesson_id>/', views.replace_video, name='replace_video'),
    path('replace-pdf/<int:lesson_id>/', views.replace_pdf, name='replace_pdf'),
    path('detach-lesson/<int:lesson_id>/from-module/<int:module_id>/', views.detach_lesson_from_module, name='detach_lesson_from_module'),
    path('detach-quiz/<int:quiz_id>/from-module/<int:module_id>/', views.detach_quiz_from_module, name='detach_quiz_from_module'),
    path('edit_lesson/<int:lesson_id>/', views.edit_lesson, name='edit_lesson'),

    # Quiz Management
    path('quizzes/', views.quiz_list, name='quiz_list'),
    path('create/quiz/', views.create_quiz, name='create_quiz'),
    path('edit/quiz/<int:pk>/', views.edit_quiz, name='edit_quiz'),
    path('quiz/<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('quiz/<int:quiz_id>/start/', views.start_quiz, name='start_quiz'),
    path('quiz/<int:quiz_id>/result/', views.quiz_result, name='quiz_result'),
    path('delete/quiz/<int:quiz_id>/', views.delete_quiz, name='delete_quiz'),
    path('quiz/<int:quiz_id>/add-question/', views.add_question, name='add_question'),
    path('bind_quiz_to_module/<int:quiz_id>/', views.bind_quiz_to_module, name='bind_quiz_to_module'),
    path('student/quiz/<int:quiz_id>/start/', views.student_start_quiz, name='student_start_quiz'),
    path('student/quiz/<int:quiz_id>/submit/', views.student_submit_quiz, name='student_submit_quiz'),
    path('student/quiz/<int:quiz_id>/result/', views.student_quiz_result, name='student_quiz_result'),

    # Progress Tracking
    path('update_progress/', views.update_progress, name='update_progress'),

    # New URL for adding a lesson to a module
    path('add-lesson-to-module/<int:module_id>/', views.add_lesson_to_module, name='add_lesson_to_module'),

    # New URL for editing answers via AJAX
    path('edit_answers_ajax/<int:question_id>/', views.edit_answers_ajax, name='edit_answers_ajax'),

    # New URL for student public profile
    path('student/<int:student_id>/profile/', views.student_public_profile, name='student_public_profile'),

    # New URL for deleting a group
    path('delete_group/<int:group_id>/', views.delete_group, name='delete_group'),
    path('group_management/<int:group_id>/', views.group_management_page, name='group_management'),
    path('mark_notifications_read/', views.mark_notifications_read, name='mark_notifications_read'),
    path('course/feedback/<int:course_id>/', views.course_feedback, name='course_feedback'),
    path('course/feedbacks/<int:course_id>/', views.course_feedbacks_list, name='course_feedbacks_list'),

    # New URL for group management
    path('group/<int:group_id>/manage/', views.group_management_page, name='group_management'),

    # New URL for marking a module as complete
    path('mark_module_complete/', views.mark_module_complete, name='mark_module_complete'),

    # New URL for marking a lesson as complete
    path('mark_lesson_complete/', views.mark_lesson_complete, name='mark_lesson_complete'),

    # New URL for student message request
    path('student_message_request/', views.student_message_request, name='student_message_request'),

    # New URL for admin message requests
    path('admin_message_requests/', views.admin_message_requests, name='admin_message_requests'),
    path('admin_message_request/<int:request_id>/', views.admin_message_request_detail, name='admin_message_request_detail'),
    path('get_request_details/<str:request_type>/<int:request_id>/', views.get_request_details, name='get_request_details'),
    path('update_request_status/', views.update_request_status, name='update_request_status'),
    
    # API endpoints для уведомлений
    path('api/notifications/', views.get_notifications, name='get_notifications'),
    path('api/notifications/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/delete/', views.delete_notification, name='delete_notification'),
    path('api/notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('api/notifications/mark-popup-shown/', views.mark_popup_shown, name='mark_popup_shown'),
    path('api/courses/<int:course_id>/modules/', views.modules_by_course, name='api_modules_by_course'),
    path('api/requests/history/', views.requests_history, name='requests_history'),
    path('module/<int:module_id>/edit/', views.edit_module, name='edit_module'),
    path('attach-module-to-course/', views.attach_module_to_course, name='attach_module_to_course'),

    # Колесо фортуны
path('wheel-of-fortune/', views.wheel_of_fortune_page, name='wheel_of_fortune_page'),
    path('api/spin-wheel/', views.spin_wheel, name='spin_wheel'),
    path('api/check-spin-availability/', views.check_spin_availability, name='check_spin_availability'),
path('api/check-wheel-status/', views.check_wheel_status, name='check_wheel_status'),

]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




class Person: 
    def __init__(self, name): 
        self.name = name 

p = Person("Timur") 
print(p.name)


