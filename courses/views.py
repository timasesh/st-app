# courses/views.py
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.forms import modelformset_factory
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import logging
from django.db.models import Count, Avg, Max
import pandas as pd
from django.core.files.storage import default_storage
from django.conf import settings
import os
import random
import string
import traceback
from django.db.utils import IntegrityError
import fitz

from .forms import (
    StudentRegistrationForm, LessonCreationForm, ModuleCreationForm,
    CourseCreationForm, StudentProfileForm, QuizForm, QuestionForm,
    AnswerForm, QuizToModuleForm, StudentExcelUploadForm, StudentMessageRequestForm,
    CourseFeedbackForm
)
from .models import (
    User, Lesson, Module, Course, StudentProgress, Student,
    Question, Answer, Quiz, QuizResult, ProfileEditRequest, CourseAddRequest, Notification, Group, QuizAttempt, StudentMessageRequest, Level,
    CourseFeedback, CourseResult, Achievement, Teacher, Homework, HomeworkSubmission, HomeworkPhoto, WheelSpin
)
from .services import evaluate_and_unlock_achievements, get_achievement_progress

logger = logging.getLogger(__name__)

# Landing Page View
def landing_page(request):
    """
    Главная продающая страница (лендинг) для образовательной платформы ALMAU
    """
    # Получаем статистику для отображения на лендинге
    total_students = Student.objects.count()
    total_courses = Course.objects.count()
    total_levels = Level.objects.count()
    
    # Получаем несколько курсов для демонстрации
    featured_courses = Course.objects.all()[:3]
    
    context = {
        'total_students': total_students,
        'total_courses': total_courses,
        'total_levels': total_levels,
        'featured_courses': featured_courses,
    }
    
    return render(request, 'courses/landing_page.html', context)

# Authentication Views
def login_view(request):
    if request.method == 'POST':
        email = request.POST['username']
        password = request.POST['password']
        user = None
        try:
            from .models import User
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None
        if user is not None:
            login(request, user)
            if user.is_admin:
                return redirect('admin_students_page')
            elif user.is_student:
                return redirect('student_page')
        else:
            error_message = "Неверные учетные данные."
            return render(request, 'courses/login.html', {'error': error_message})
    return render(request, 'courses/login.html')

def student_login(request):
    if request.method == 'POST':
        email = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=email, password=password)
        if user is not None and hasattr(user, 'student'):
            login(request, user)
            return redirect('student_page')
        else:
            # Вместо HttpResponse рендерим ту же страницу с ошибкой
            return render(request, 'courses/student_login.html', {'error': True})
    return render(request, 'courses/student_login.html')

def check_username_availability(request):
    """AJAX view для проверки доступности никнейма"""
    if request.method == 'GET':
        username = request.GET.get('username', '')
        if username:
            is_available = not User.objects.filter(username=username).exists()
            return JsonResponse({
                'available': is_available,
                'message': 'Никнейм доступен' if is_available else 'Никнейм уже занят'
            })
    return JsonResponse({'error': 'Invalid request'})

def student_registration(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                messages.success(request, 'Регистрация прошла успешно! Теперь вы можете войти в систему.')
                return redirect('student_login')
            except Exception as e:
                messages.error(request, f'Ошибка при регистрации: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = StudentRegistrationForm()
    
    return render(request, 'courses/student_registration.html', {'form': form})

def admin_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_students_page')
        else:
            # Вместо HttpResponse рендерим ту же страницу с ошибкой
            return render(request, 'courses/admin_login.html', {'error': True})
    return render(request, 'courses/admin_login.html')

def logout_view(request):
    logout(request)
    return redirect('student_login')

# Admin Views
@login_required
def admin_page(request):
    from .models import ProfileEditRequest, CourseAddRequest, Notification, Group, StudentMessageRequest, Level
    student_form = StudentRegistrationForm()
    excel_form = StudentExcelUploadForm()
    lesson_form = LessonCreationForm()
    module_form = ModuleCreationForm()
    course_form = CourseCreationForm()
    error = None

    # CRUD для уровней
    if request.method == 'POST':
        if 'add_level' in request.POST:
            try:
                number = int(request.POST.get('number'))
                name = request.POST.get('name')
                min_stars = int(request.POST.get('min_stars'))
                max_stars = int(request.POST.get('max_stars'))
                description = request.POST.get('description', '')
                image = request.FILES.get('image')
                
                Level.objects.create(
                    number=number, 
                    name=name, 
                    min_stars=min_stars, 
                    max_stars=max_stars,
                    description=description,
                    image=image
                )
                messages.success(request, f'Уровень "{name}" успешно создан!')
            except Exception as e:
                error = str(e)
        elif 'edit_level' in request.POST:
            try:
                level_id = int(request.POST.get('level_id'))
                level = Level.objects.get(id=level_id)
                level.number = int(request.POST.get('number'))
                level.name = request.POST.get('name')
                level.min_stars = int(request.POST.get('min_stars'))
                level.max_stars = int(request.POST.get('max_stars'))
                
                # Обновляем описание
                level.description = request.POST.get('description', '')
                
                # Обновляем изображение если загружено новое
                new_image = request.FILES.get('image')
                if new_image:
                    # Удаляем старое изображение если есть
                    if level.image:
                        level.image.delete(save=False)
                    level.image = new_image
                
                level.save()
                messages.success(request, f'Уровень "{level.name}" успешно обновлен!')
            except Exception as e:
                error = str(e)
        elif 'remove_image' in request.POST:
            try:
                level_id = int(request.POST.get('level_id'))
                level = Level.objects.get(id=level_id)
                if level.image:
                    level.image.delete(save=False)
                    level.image = None
                    level.save()
                    messages.success(request, f'Изображение уровня "{level.name}" удалено!')
                else:
                    messages.warning(request, 'У этого уровня нет изображения!')
            except Exception as e:
                error = str(e)
        elif 'delete_level' in request.POST:
            try:
                level_id = int(request.POST.get('level_id'))
                level = Level.objects.get(id=level_id)
                level_name = level.name
                # Удаляем изображение если есть
                if level.image:
                    level.image.delete(save=False)
                level.delete()
                messages.success(request, f'Уровень "{level_name}" успешно удален!')
            except Exception as e:
                error = str(e)
        elif 'update_level' in request.POST:
            try:
                level_id = int(request.POST.get('level_id'))
                level = Level.objects.get(id=level_id)
                level.number = int(request.POST.get('number'))
                level.name = request.POST.get('name')
                level.min_stars = int(request.POST.get('min_stars'))
                level.max_stars = int(request.POST.get('max_stars'))
                
                # Обновляем описание
                level.description = request.POST.get('description', '')
                
                # Обновляем изображение если загружено новое
                new_image = request.FILES.get('image')
                if new_image:
                    # Удаляем старое изображение если есть
                    if level.image:
                        level.image.delete(save=False)
                    level.image = new_image
                
                level.save()
                messages.success(request, f'Уровень "{level.name}" успешно обновлен!')
            except Exception as e:
                error = str(e)

    if request.method == 'POST':
        if 'add_student' in request.POST:
            student_form = StudentRegistrationForm(request.POST)
            if student_form.is_valid():
                try:
                    user = student_form.save()
                    messages.success(request, f'Студент {user.username} успешно добавлен!')
                    return redirect('admin_students_page')
                except Exception as e:
                    messages.error(request, f'Ошибка при создании студента: {str(e)}')
            else:
                # Собираем все ошибки формы
                error_messages = []
                for field, errors in student_form.errors.items():
                    for error in errors:
                        if field == '__all__':
                            error_messages.append(error)
                        else:
                            field_label = student_form.fields[field].label or field
                            error_messages.append(f'{field_label}: {error}')
                
                if error_messages:
                    messages.error(request, 'Ошибки при заполнении формы: ' + '; '.join(error_messages))
                else:
                    messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
        elif 'upload_students_excel' in request.POST:
            excel_form = StudentExcelUploadForm(request.POST, request.FILES)
            if excel_form.is_valid():
                excel_file = excel_form.cleaned_data['file']
                file_path = default_storage.save('tmp/' + excel_file.name, excel_file)
                abs_path = os.path.join(settings.MEDIA_ROOT, file_path)
                try:
                    import datetime
                    df = pd.read_excel(abs_path)
                    print(f'Всего строк в файле: {len(df)}')
                    added_count = 0
                    new_students = []
                    for idx, row in df.iterrows():
                        email = get_col(row, 'Электронная почта', 'Почта', 'email')
                        first_name = get_col(row, 'Имя', 'first_name')
                        last_name = get_col(row, 'Фамилия', 'last_name')
                        if not email or '@' not in email:
                            continue
                        username = email
                        try:
                            # Проверяем, нет ли другого пользователя с таким username, но другим email
                            conflict = User.objects.filter(username=username).exclude(email=email).first()
                            if conflict:
                                print(f'Конфликт: username {username} уже занят другим email {conflict.email}')
                                continue  # Можно заменить на conflict.delete() если нужно удалять
                            temp_password = generate_random_password()
                            user, created = User.objects.get_or_create(email=email, defaults={
                                'username': username,
                                'first_name': first_name,
                                'last_name': last_name,
                                'is_student': True
                            })
                            user.username = email  # username всегда равен email
                            user.set_password(temp_password)
                            user.save()
                            student, s_created = Student.objects.get_or_create(user=user)
                            if not student.email:
                                student.email = email
                            if not student.first_name:
                                student.first_name = first_name
                            if not student.last_name:
                                student.last_name = last_name
                            student.temporary_password = temp_password
                            student.save()
                            if created or s_created:
                                added_count += 1
                            new_students.append(student)
                        except IntegrityError as e:
                            print(f'Ошибка уникальности для {email}: {e}')
                        except Exception as e:
                            print(f'Ошибка при добавлении {email}: {e}')
                    # Создаём новую группу для этой загрузки
                    group_name = f'Группа от {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
                    group = Group.objects.create(name=group_name)
                    group.students.set(new_students)
                    group.save()
                    print(f'Создана группа: {group_name} (студентов: {len(new_students)})')
                    print(f'Обработано строк: {idx+1}')
                    print(f'Добавлено студентов: {added_count}')
                    messages.success(request, f'Все студенты из файла успешно добавлены! ({added_count}) Создана группа: {group_name}')
                except Exception as e:
                    messages.error(request, f'Ошибка при обработке файла: {e}')
                finally:
                    if os.path.exists(abs_path):
                        os.remove(abs_path)
                return redirect('admin_page')
        elif 'add_lesson' in request.POST:
            lesson_form = LessonCreationForm(request.POST, request.FILES)
            if lesson_form.is_valid():
                lesson_form.save()
                return redirect('admin_page')
        elif 'add_module' in request.POST:
            module_form = ModuleCreationForm(request.POST)
            if module_form.is_valid():
                module_form.save()
                return redirect('admin_page')
        elif 'add_course' in request.POST:
            course_form = CourseCreationForm(request.POST)
            if course_form.is_valid():
                course = course_form.save()
                # Назначаем преподавателя если выбран
                teacher_id = request.POST.get('teacher_id')
                if teacher_id:
                    try:
                        teacher = Teacher.objects.get(id=teacher_id)
                        course.teacher = teacher
                        course.save()
                    except Teacher.DoesNotExist:
                        pass
                return redirect('admin_page')
        elif 'delete_course' in request.POST:
            course_id = request.POST['course_id']
            Course.objects.filter(id=course_id).delete()
            return redirect('admin_page')
        elif 'edit_group' in request.POST:
            group_id = request.POST.get('group_id')
            group_name = request.POST.get('group_name')
            if group_id and group_name:
                group = get_object_or_404(Group, id=group_id)
                group.name = group_name
                group.save()
                messages.success(request, f'Группа успешно переименована в "{group_name}"')
            return redirect('admin_page')
        elif 'approve_edit' in request.POST or 'reject_edit' in request.POST:
            req_id = request.POST.get('request_id')
            req = ProfileEditRequest.objects.get(id=req_id)
            if 'approve_edit' in request.POST:
                req.status = 'approved'
                req.admin_response = request.POST.get('admin_response', '')
                req.student.profile_edited_once = False
                req.student.save()
                Notification.objects.create(
                    student=req.student,
                    type='profile_edit',
                    message=f'Ваш запрос на редактирование профиля подтверждён. {req.admin_response or ""}'
                )
            else:
                req.status = 'rejected'
                req.admin_response = request.POST.get('admin_response', '')
                Notification.objects.create(
                    student=req.student,
                    type='profile_edit',
                    message=f'Ваш запрос на редактирование профиля отклонён. {req.admin_response or ""}'
                )
            req.save()
            return redirect('admin_page')
        elif 'approve_course_add' in request.POST or 'reject_course_add' in request.POST:
            req_id = request.POST.get('request_id')
            req = CourseAddRequest.objects.get(id=req_id)
            if 'approve_course_add' in request.POST:
                # Получаем выбранный курс для назначения
                assigned_course_id = request.POST.get('assigned_course_id')
                if assigned_course_id:
                    assigned_course = Course.objects.get(id=assigned_course_id)
                    req.assigned_course = assigned_course
                    req.status = 'approved'
                    req.admin_response = request.POST.get('admin_response', '')
                    req.student.courses.add(assigned_course)
                    Notification.objects.create(
                        student=req.student,
                        type='course_approved',
                        message=f'Ваш запрос на добавление курса "{req.course_name}" подтверждён. Вам назначен курс "{assigned_course.title}". {req.admin_response or ""}'
                    )
                else:
                    messages.error(request, 'Пожалуйста, выберите курс для назначения.')
                    return redirect('admin_page')
            else:
                req.status = 'rejected'
                req.admin_response = request.POST.get('admin_response', '')
                Notification.objects.create(
                    student=req.student,
                    type='course_rejected',
                    message=f'Ваш запрос на добавление курса "{req.course_name}" отклонён. {req.admin_response or ""}'
                )
            req.save()
            return redirect('admin_page')
        elif 'approve_message' in request.POST or 'reject_message' in request.POST:
            req_id = request.POST.get('message_request_id')
            req = StudentMessageRequest.objects.get(id=req_id)
            if 'approve_message' in request.POST:
                req.status = 'approved'
                req.admin_response = request.POST.get('admin_response', '')
                Notification.objects.create(
                    student=req.student,
                    type='profile_edit',
                    message=f'Ваш произвольный запрос подтверждён. {req.admin_response or ""}'
                )
            else:
                req.status = 'rejected'
                req.admin_response = request.POST.get('admin_response', '')
                Notification.objects.create(
                    student=req.student,
                    type='profile_edit',
                    message=f'Ваш произвольный запрос отклонён. {req.admin_response or ""}'
                )
            req.save()
            return redirect('admin_page')
        elif 'group_create' in request.POST:
            group_name = request.POST.get('group_name')
            student_ids = request.POST.getlist('group_students')
            if group_name and student_ids:
                group, created = Group.objects.get_or_create(name=group_name)
                new_students = Student.objects.filter(id__in=student_ids)
                old_students = set(group.students.all())
                group.students.set(new_students)
                # Уведомления для новых участников
                for student in new_students:
                    if student not in old_students:
                        Notification.objects.create(
                            student=student,
                            type='profile_edit',
                            message=f'Вы присоединились к группе "{group.name}".'
                        )
                        # Уведомления для остальных участников
                        for other in new_students:
                            if other != student:
                                Notification.objects.create(
                                    student=other,
                                    type='profile_edit',
                                    message=f'К вам в группу "{group.name}" присоединился {student.user.username}.'
                                )
                messages.success(request, f'Группа "{group_name}" создана!')
            return redirect('admin_page')
        elif 'attach_group_to_course' in request.POST:
            group_id = request.POST.get('group_id')
            course_id = request.POST.get('course_id')
            group = Group.objects.get(id=group_id)
            course = Course.objects.get(id=course_id)
            for student in group.students.all():
                student.courses.add(course)
            messages.success(request, f'Все студенты из группы "{group.name}" прикреплены к курсу "{course.title}"!')
            return redirect('admin_page')
        # === Notifications CRUD ===
        elif 'create_notification' in request.POST:
            try:
                student_id = int(request.POST.get('notification_student_id'))
                notif_type = request.POST.get('notification_type')
                message_text = request.POST.get('notification_message', '').strip()
                priority = int(request.POST.get('notification_priority', 1))
                is_read = bool(request.POST.get('notification_is_read'))
                target_student = Student.objects.get(id=student_id)
                Notification.objects.create(
                    student=target_student,
                    type=notif_type,
                    message=message_text,
                    priority=priority,
                    is_read=is_read
                )
                messages.success(request, 'Уведомление создано.')
            except Exception as e:
                messages.error(request, f'Ошибка создания уведомления: {e}')
            return redirect('admin_page')
        elif 'update_notification' in request.POST:
            try:
                notif_id = int(request.POST.get('notification_id'))
                notif = Notification.objects.get(id=notif_id)
                notif.type = request.POST.get('notification_type', notif.type)
                notif.message = request.POST.get('notification_message', notif.message)
                notif.priority = int(request.POST.get('notification_priority', notif.priority))
                notif.is_read = bool(request.POST.get('notification_is_read'))
                notif.save()
                messages.success(request, 'Уведомление обновлено.')
            except Exception as e:
                messages.error(request, f'Ошибка обновления уведомления: {e}')
            return redirect('admin_page')
        elif 'delete_notification' in request.POST:
            try:
                notif_id = int(request.POST.get('notification_id'))
                Notification.objects.filter(id=notif_id).delete()
                messages.success(request, 'Уведомление удалено.')
            except Exception as e:
                messages.error(request, f'Ошибка удаления уведомления: {e}')
            return redirect('admin_page')
        # === Achievements CRUD ===
        elif 'create_achievement' in request.POST:
            try:
                code = request.POST.get('ach_code').strip()
                title = request.POST.get('ach_title').strip()
                description = request.POST.get('ach_description', '').strip()
                ctype = request.POST.get('ach_condition_type')
                cvalue = int(request.POST.get('ach_condition_value', 1))
                reward = request.POST.get('ach_reward').strip()
                reward_icon = request.POST.get('ach_reward_icon', '🎁').strip() or '🎁'
                Achievement.objects.get_or_create(
                    code=code,
                    defaults={
                        'title': title,
                        'description': description,
                        'condition_type': ctype,
                        'condition_value': cvalue,
                        'reward': reward,
                        'reward_icon': reward_icon,
                        'is_active': True,
                    }
                )
                messages.success(request, 'Достижение создано.')
            except Exception as e:
                messages.error(request, f'Ошибка создания достижения: {e}')
            return redirect('admin_page')
        elif 'update_achievement' in request.POST:
            try:
                ach_id = int(request.POST.get('achievement_id'))
                ach = Achievement.objects.get(id=ach_id)
                ach.code = request.POST.get('ach_code', ach.code).strip() or ach.code
                ach.title = request.POST.get('ach_title', ach.title).strip()
                ach.description = request.POST.get('ach_description', ach.description).strip()
                ach.condition_type = request.POST.get('ach_condition_type', ach.condition_type)
                ach.condition_value = int(request.POST.get('ach_condition_value', ach.condition_value))
                ach.reward = request.POST.get('ach_reward', ach.reward).strip()
                ach.reward_icon = request.POST.get('ach_reward_icon', ach.reward_icon).strip() or ach.reward_icon
                ach.is_active = bool(request.POST.get('ach_is_active'))
                ach.save()
                messages.success(request, 'Достижение обновлено.')
            except Exception as e:
                messages.error(request, f'Ошибка обновления достижения: {e}')
            return redirect('admin_page')
        elif 'delete_achievement' in request.POST:
            try:
                ach_id = int(request.POST.get('achievement_id'))
                Achievement.objects.filter(id=ach_id).delete()
                messages.success(request, 'Достижение удалено.')
            except Exception as e:
                messages.error(request, f'Ошибка удаления достижения: {e}')
            return redirect('admin_page')

    students = Student.objects.all()
    lessons = Lesson.objects.all()
    modules = Module.objects.all()
    courses = Course.objects.all()
    quizzes = Quiz.objects.all()
    available_lessons = Lesson.objects.all()  # Все доступные уроки
    edit_requests = ProfileEditRequest.objects.filter(status='pending').select_related('student__user')
    course_add_requests = CourseAddRequest.objects.filter(status='pending').select_related('student__user', 'course')
    message_requests = StudentMessageRequest.objects.filter(status='pending').select_related('student__user')
    groups = Group.objects.all().prefetch_related('students')
    levels = Level.objects.all().order_by('number')
    teachers = Teacher.objects.all().order_by('last_name', 'first_name')
    # Notifications list for admin management
    notifications_admin = Notification.objects.all().select_related('student__user').order_by('-created_at')[:500]
    notification_type_choices = Notification._meta.get_field('type').choices
    achievements_admin = Achievement.objects.all().order_by('condition_type', 'condition_value')

    # Формируем данные о прогрессе достижений студентов (для подвкладки "Скоро подарок")
    from .services import get_achievement_progress
    achievement_progress_data = []
    
    for student in students:
        for achievement in achievements_admin:
            if achievement.is_active:
                progress_data = get_achievement_progress(student, achievement)
                if progress_data['percentage'] > 50 and progress_data['percentage'] < 100:
                    achievement_progress_data.append({
                        'student': student,
                        'achievement': achievement,
                        'progress_data': {
                            'progress_percentage': progress_data['percentage'],
                            'current_value': progress_data['current'],
                            'target_value': progress_data['target']
                        }
                    })
    
    # Сортируем по проценту выполнения (по убыванию)
    achievement_progress_data.sort(key=lambda x: x['progress_data']['progress_percentage'], reverse=True)

    # Формируем словарь прогресса для быстрого доступа в шаблоне (по факту завершённых уроков)
    progress_dict = {}
    for student in students:
        for course in student.courses.all():
            # Создаём объект прогресса, если его нет
            sp, created = StudentProgress.objects.get_or_create(user=student.user, course=course)
            # Получаем все уроки курса
            all_lessons = set()
            for module in course.modules.all():
                all_lessons.update(module.lessons.values_list('id', flat=True))
            all_lessons_count = len(all_lessons)
            completed_lessons = set(sp.completed_lessons.values_list('id', flat=True))
            if all_lessons_count > 0:
                percent = int((len(completed_lessons) / all_lessons_count) * 100)
            else:
                percent = 0
            sp.progress = percent
            sp.save()
            key = f'{student.user.id}_{course.id}'
            progress_dict[key] = percent

    context = {
        'student_form': student_form,
        'excel_form': excel_form,
        'lesson_form': lesson_form,
        'module_form': module_form,
        'course_form': course_form,
        'students': students,
        'lessons': lessons,
        'modules': modules,
        'courses': courses,
        'quizzes': quizzes,
        'available_lessons': available_lessons,  # Добавляем в контекст
        'progress_dict': progress_dict,          # Новый словарь для шаблона
        'edit_requests': edit_requests,
        'course_add_requests': course_add_requests,
        'groups': groups,
        'message_requests': message_requests,
        'levels': levels,
        'teachers': teachers,
        'error': error,
        'notifications_admin': notifications_admin,
        'notification_type_choices': notification_type_choices,
        'all_achievements': achievements_admin,
        'achievement_progress_data': achievement_progress_data,
    }
    return render(request, 'courses/admin_page_test.html', context)

@login_required
def admin_levels(request):
    levels = Level.objects.all().order_by('number')
    error = None
    if request.method == 'POST':
        if 'add_level' in request.POST:
            try:
                number = int(request.POST.get('number'))
                name = request.POST.get('name')
                min_stars = int(request.POST.get('min_stars'))
                max_stars = int(request.POST.get('max_stars'))
                Level.objects.create(number=number, name=name, min_stars=min_stars, max_stars=max_stars)
            except Exception as e:
                error = str(e)
        elif 'edit_level' in request.POST:
            try:
                level_id = int(request.POST.get('level_id'))
                level = Level.objects.get(id=level_id)
                level.number = int(request.POST.get('number'))
                level.name = request.POST.get('name')
                level.min_stars = int(request.POST.get('min_stars'))
                level.max_stars = int(request.POST.get('max_stars'))
                level.save()
            except Exception as e:
                error = str(e)
        elif 'delete_level' in request.POST:
            try:
                level_id = int(request.POST.get('level_id'))
                Level.objects.filter(id=level_id).delete()
            except Exception as e:
                error = str(e)
    levels = Level.objects.all().order_by('number')
    return render(request, 'courses/admin_levels.html', {'levels': levels, 'error': error})

# Student Views
@login_required
def levels_page(request):
    """Отдельная страница для отображения всех уровней"""
    from .models import Level
    
    if not hasattr(request.user, 'student'):
        return redirect('student_login')
    
    student = request.user.student
    all_levels = Level.objects.all().order_by('number').only('number', 'name', 'min_stars', 'max_stars', 'image', 'description')
    
    context = {
        'student': student,
        'all_levels': all_levels,
    }
    return render(request, 'courses/levels_page.html', context)

@login_required
def rating_page(request):
    """Отдельная страница для отображения рейтинга"""
    if not hasattr(request.user, 'student'):
        return redirect('student_login')
    
    student = request.user.student
    groups = student.groups.all().prefetch_related('students__user')
    
    context = {
        'student': student,
        'groups': groups,
    }
    return render(request, 'courses/rating_page.html', context)

@login_required
def student_page(request):
    student = get_object_or_404(Student, user=request.user)
    courses = student.courses.all()
    from .models import QuizResult, Quiz, CourseAddRequest, Course, StudentMessageRequest, Level
    quiz_results = QuizResult.objects.filter(user=request.user)
    for result in quiz_results:
        quiz = getattr(result, 'quiz', None)
        if quiz and hasattr(quiz, 'stars') and quiz.stars > 0 and not result.stars_given:
            percent = int((result.score / result.total_questions) * 100) if hasattr(result, 'total_questions') and result.total_questions else 0
            if percent == 100:
                student.update_stars(quiz.stars, f"Квиз {quiz.title}")
                result.stars_given = True
                result.save()
                
                # Пересчитываем достижения после начисления звёзд за квиз
                try:
                    evaluate_and_unlock_achievements(student)
                except Exception as e:
                    print(f"Ошибка при пересчёте достижений после начисления звёзд за квиз: {e}")
    
    # Convert progress_data to a dictionary with course IDs as keys
    progress_data = {}
    course_completed_data = {}
    for course in courses:
        # Используем правильную логику расчета прогресса (уроки + квизы)
        progress_value = student.calculate_progress(course)
        progress_data[course.id] = progress_value
        
        # Проверяем, завершен ли курс
        course_completed = course.is_completed_by(student)
        course_completed_data[course.id] = course_completed
        
        # Обновляем прогресс в базе данных для консистентности
        sp = StudentProgress.objects.filter(user=request.user, course=course).first()
        if sp:
            sp.progress = progress_value
            sp.save()

    show_course_notification = False
    all_courses = Course.objects.all()
    add_course_requests = CourseAddRequest.objects.filter(student=student).order_by('-created_at')
    message_requests = StudentMessageRequest.objects.filter(student=student).order_by('-created_at')
    notifications = Notification.objects.filter(student=student).order_by('-created_at')[:10]
    unread_count = Notification.objects.filter(student=student, is_read=False).count()
    
    # Создаем тестовые уведомления если их нет (для демонстрации)
    if not notifications.exists():
        test_notifications = [
            {
                'type': 'group_added',
                'message': f'Вы присоединились к группе "{student.groups.first().name}".' if student.groups.exists() else 'Добро пожаловать в Study Task!',
                'priority': 2,
                'is_read': False
            },
            {
                'type': 'stars_awarded',
                'message': 'Поздравляем! Вы получили звезды за активность.',
                'priority': 1,
                'is_read': False
            },
            {
                'type': 'level_up',
                'message': f'Отличная работа! Вы достигли уровня {student.level_number}.',
                'priority': 3,
                'is_read': True
            }
        ]
        
        for notif_data in test_notifications:
            Notification.objects.create(
                student=student,
                type=notif_data['type'],
                message=notif_data['message'],
                priority=notif_data['priority'],
                is_read=notif_data['is_read']
            )
        
        # Обновляем данные после создания
        notifications = Notification.objects.filter(student=student).order_by('-created_at')[:20]
        unread_count = Notification.objects.filter(student=student, is_read=False).count()
    
    # Данные для вкладок "Уровни" и "Рейтинг"
    all_levels = Level.objects.all().only('number', 'name', 'min_stars', 'max_stars', 'description', 'image').order_by('number')
    
    # Пересчитываем достижения при загрузке страницы
    try:
        evaluate_and_unlock_achievements(student)
    except Exception as e:
        print(f"Ошибка при пересчёте достижений в student_page: {e}")
        import traceback
        traceback.print_exc()
    
    # Достижения
    from .models import Achievement, StudentAchievement
    all_achievements = Achievement.objects.filter(is_active=True).order_by('condition_type', 'condition_value')
    unlocked_achievements = StudentAchievement.objects.filter(student=student).select_related('achievement').order_by('-unlocked_at')
    unlocked_ids = set(unlocked_achievements.values_list('achievement_id', flat=True))
    locked_achievements = all_achievements.exclude(id__in=unlocked_ids)
    progress_by_id = {}
    
    # Данные о домашних заданиях
    from .models import Homework
    homeworks = Homework.objects.filter(student=student).order_by('-created_at')
    pending_homeworks_count = homeworks.filter(submissions__is_submitted=False).count()
    submitted_homeworks_count = homeworks.filter(submissions__is_submitted=True, submissions__is_completed=False).count()
    completed_homeworks_count = homeworks.filter(submissions__is_completed=True).count()
    recent_homeworks = homeworks[:5]  # Последние 5 заданий
    for ach in all_achievements:
        try:
            progress_by_id[ach.id] = get_achievement_progress(student, ach)
        except Exception as e:
            print(f"Ошибка при расчёте прогресса достижения {ach.title}: {e}")
            progress_by_id[ach.id] = {'current': 0, 'target': ach.condition_value or 1, 'percentage': 0}
    groups = student.groups.all().prefetch_related('students__user')
    
    # Получаем квизы студента (из модулей курсов и прямые назначения)
    student_quizzes = []
    
    # Квизы из модулей курсов
    for course in courses:
        for module in course.modules.all():
            for quiz in module.quizzes.filter(is_active=True):
                if quiz not in student_quizzes:
                    student_quizzes.append(quiz)
    
    # Прямые назначения квизов
    for quiz in student.assigned_quizzes.filter(is_active=True):
        if quiz not in student_quizzes:
            student_quizzes.append(quiz)
    
    # Добавляем информацию о результатах квизов
    for quiz in student_quizzes:
        latest_attempt = QuizAttempt.objects.filter(
            student=student, 
            quiz=quiz
        ).order_by('-created_at').first()
        
        if latest_attempt:
            quiz.latest_attempt = latest_attempt
            quiz.best_score = QuizAttempt.objects.filter(
                student=student, 
                quiz=quiz
            ).aggregate(Max('score'))['score__max']
        else:
            quiz.latest_attempt = None
            quiz.best_score = None
    
    # Создаем рейтинг групп
    rating_groups = []
    for group in groups:
        group_students = group.students.all().select_related('user').order_by('-stars', 'user__first_name')
        students_with_rating = []
        for position, group_student in enumerate(group_students, 1):
            students_with_rating.append({
                'student': group_student,
                'position': position
            })
        
        rating_groups.append({
            'name': group.name,
            'students_with_rating': students_with_rating
        })
    
    # Количество групп для хедера
    groups_count = groups.count()
    
    if request.method == 'POST':
        if 'mark_notifications_read' in request.POST:
            # Маркируем все уведомления как прочитанные
            Notification.objects.filter(student=student, is_read=False).update(is_read=True)
            return redirect('student_page')
        elif 'course_code' in request.POST:
            course_code = request.POST.get('course_code')
            try:
                course = Course.objects.get(course_code=course_code)
                student.courses.add(course)
                show_course_notification = True
                Notification.objects.create(
                    student=student,
                    type='course_approved',
                    message=f'Вы были добавлены на курс "{course.title}" через код.'
                )
                # Пересчитываем данные прогресса для обновленного списка курсов
                updated_progress_data = {}
                updated_course_completed_data = {}
                for course in student.courses.all():
                    progress_value = student.calculate_progress(course)
                    updated_progress_data[course.id] = progress_value
                    updated_course_completed_data[course.id] = course.is_completed_by(student)
                
                return render(request, 'courses/student_page.html', {
                    'courses': student.courses.all(),
                    'progress_data': updated_progress_data,
                    'course_completed_data': updated_course_completed_data,
                    'student': student,
                    'show_course_notification': show_course_notification,
                    'all_courses': all_courses,
                    'course_requests': add_course_requests,
                    'message_requests': message_requests,
                    'notifications': notifications,
                    'unread_notifications_count': unread_count,
                    'all_levels': all_levels,
                    'rating_groups': rating_groups,
                    'groups_count': groups_count,
                    'all_achievements': all_achievements,
                    'unlocked_achievements': unlocked_achievements,
                    'locked_achievements': locked_achievements,
                    'progress_by_id': progress_by_id,
                    'pending_homeworks_count': pending_homeworks_count,
                    'submitted_homeworks_count': submitted_homeworks_count,
                    'completed_homeworks_count': completed_homeworks_count,
                    'recent_homeworks': recent_homeworks,
                })
            except Course.DoesNotExist:
                error_message = "Курс с данным кодом не найден."
                return render(request, 'courses/student_page.html', {
                    'courses': courses,
                    'progress_data': progress_data,
                    'course_completed_data': course_completed_data,
                    'error_message': error_message,
                    'student': student,
                    'all_courses': all_courses,
                    'course_requests': add_course_requests,
                    'message_requests': message_requests,
                    'notifications': notifications,
                    'unread_notifications_count': unread_count,
                    'all_levels': all_levels,
                    'rating_groups': rating_groups,
                    'groups_count': groups_count,
                    'all_achievements': all_achievements,
                    'unlocked_achievements': unlocked_achievements,
                    'locked_achievements': locked_achievements,
                    'progress_by_id': progress_by_id,
                    'pending_homeworks_count': pending_homeworks_count,
                    'submitted_homeworks_count': submitted_homeworks_count,
                    'completed_homeworks_count': completed_homeworks_count,
                    'recent_homeworks': recent_homeworks,
                })
        elif 'add_course_request' in request.POST:
            course_name = request.POST.get('course_name')
            comment = request.POST.get('course_comment')
            
            if course_name:
                CourseAddRequest.objects.create(
                    student=student, 
                    course_name=course_name, 
                    comment=comment
                )
                Notification.objects.create(
                    student=student,
                    type='course_approved',
                    message=f'Ваш запрос на добавление курса "{course_name}" отправлен администратору.'
                )
                messages.success(request, 'Запрос на добавление курса отправлен!')
            else:
                messages.error(request, 'Пожалуйста, укажите название курса.')
            
            return redirect('student_page')
        elif 'message_request' in request.POST:
            message = request.POST.get('message')
            if message:
                StudentMessageRequest.objects.create(student=student, message=message)
                Notification.objects.create(
                    student=student,
                    type='profile_edit',
                    message='Ваш произвольный запрос отправлен администратору.'
                )
                messages.success(request, 'Произвольный запрос отправлен!')
                return redirect('student_page')
        elif 'delete_message_request' in request.POST:
            req_id = request.POST.get('delete_message_request')
            req = StudentMessageRequest.objects.filter(id=req_id, student=student).first()
            if req:
                req.delete()
                messages.success(request, 'Запрос удалён!')
                return redirect('student_page')
    
    return render(request, 'courses/student_page.html', {
        'courses': courses,
        'progress_data': progress_data,
        'course_completed_data': course_completed_data,
        'student': student,
        'show_course_notification': show_course_notification,
        'all_courses': all_courses,
        'course_requests': add_course_requests,
        'message_requests': message_requests,
        'notifications': notifications,
        'unread_notifications_count': unread_count,
        'all_levels': all_levels,
        'rating_groups': rating_groups,
        'groups_count': groups_count,
        'all_achievements': all_achievements,
        'unlocked_achievements': unlocked_achievements,
        'locked_achievements': locked_achievements,
        'progress_by_id': progress_by_id,
        'student_quizzes': student_quizzes,
        'pending_homeworks_count': pending_homeworks_count,
        'submitted_homeworks_count': submitted_homeworks_count,
        'completed_homeworks_count': completed_homeworks_count,
        'recent_homeworks': recent_homeworks,
    })

@login_required
def student_profile(request):
    student = get_object_or_404(Student, user=request.user)
    from .models import ProfileEditRequest

    # Проверяем наличие активного запроса
    active_request = ProfileEditRequest.objects.filter(student=student, status='pending').first()
    last_request = ProfileEditRequest.objects.filter(student=student).order_by('-created_at').first()
    admin_response = None
    admin_status = None
    if last_request and last_request.status in ['approved', 'rejected']:
        admin_response = last_request.admin_response
        admin_status = last_request.status

    if request.method == 'POST':
        if 'request_edit' in request.POST:
            # Создать заявку на редактирование
            if not active_request:
                ProfileEditRequest.objects.create(student=student)
                Notification.objects.create(
                    student=student,
                    type='profile_edit',
                    message='Ваш запрос на редактирование профиля отправлен администратору.'
                )
                messages.success(request, 'Запрос на редактирование отправлен администратору.')
            return redirect('student_profile')
        else:
            form = StudentProfileForm(request.POST, request.FILES, instance=student)
            if form.is_valid():
                form.save()
                student.profile_edited_once = True
                student.save()
                messages.success(request, 'Профиль успешно обновлен!')
                return redirect('student_profile')
            else:
                # Добавляем отладочную информацию
                print("Form errors:", form.errors)
                messages.error(request, f'Ошибка при обновлении профиля: {form.errors}')
    else:
        form = StudentProfileForm(instance=student)

    return render(request, 'courses/student_profile.html', {
        'form': form,
        'student': student,
        'active_request': active_request,
        'admin_response': admin_response,
        'admin_status': admin_status,
    })

# Student Management Views
@login_required
def student_details(request, user_id):
    try:
        student = Student.objects.get(user_id=user_id)
    except Student.DoesNotExist:
        # Try to find by student ID if user_id doesn't work
        try:
            student = Student.objects.get(id=user_id)
        except Student.DoesNotExist:
            from django.http import Http404
            raise Http404("Student not found")
    
    # Подготовка данных о прогрессе
    progress_data = []
    for course in student.courses.all():
        # Используем правильную логику расчета прогресса (уроки + квизы)
        progress_value = student.calculate_progress(course)
        progress_data.append({
            'course': course.title,
            'progress': progress_value,
        })
        
        # Обновляем прогресс в базе данных для консистентности
        sp = StudentProgress.objects.filter(user=student.user, course=course).first()
        if sp:
            sp.progress = progress_value
            sp.save()

    return render(request, 'courses/student_details.html', {
        'student': student,
        'progress_data': progress_data,
    })

# Course Management Views
@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    quiz_results = {}
    for module in course.modules.all():
        for quiz in module.quizzes.all():
            result = QuizAttempt.objects.filter(student__user=request.user, quiz=quiz).order_by('-attempt_number').first()
            if result:
                quiz_results[quiz.id] = {
                    'score': result.score,
                    'passed': result.passed,
                    'percent': result.score
                }
    student_progress = StudentProgress.objects.filter(user=request.user, course=course).first()
    completed_lessons = set()
    if student_progress:
        completed_lessons = set(student_progress.completed_lessons.values_list('id', flat=True))
    # Прогресс по каждому модулю
    module_progress = {}
    for module in course.modules.all():
        lessons = list(module.lessons.all())
        if lessons:
            completed = sum(1 for lesson in lessons if lesson.id in completed_lessons)
            percent = int((completed / len(lessons)) * 100)
        else:
            percent = 0
        module_progress[module.id] = percent
    # Для блокировки уроков по модулю
    next_lesson_id_by_module = {}
    for module in course.modules.all():
        for lesson in module.lessons.all():
            if lesson.id not in completed_lessons:
                next_lesson_id_by_module[module.id] = lesson.id
                break

    # Подготавливаем данные о слайдах для передачи через json_script
    all_lesson_slides_data = {}
    for module in course.modules.all():
        for lesson in module.lessons.all():
            # Если требуется конвертация, но слайдов нет — попробуем сконвертировать на лету
            if lesson.convert_pdf_to_slides and lesson.pdf and not lesson.slides.exists():
                try:
                    from .services import handle_lesson_file_conversion
                    from .models import LessonSlide
                    image_paths = handle_lesson_file_conversion(lesson)
                    if image_paths:
                        for order, img_path in enumerate(image_paths):
                            relative_path = os.path.relpath(img_path, settings.MEDIA_ROOT).replace('\\', '/')
                            LessonSlide.objects.create(lesson=lesson, image=relative_path, order=order + 1)
                        lesson.converted_slides_status = 'completed'
                        lesson.slide_count = len(image_paths)
                        lesson.save(update_fields=['converted_slides_status', 'slide_count'])
                    else:
                        lesson.converted_slides_status = 'failed'
                        lesson.slide_count = 0
                        lesson.save(update_fields=['converted_slides_status', 'slide_count'])
                except Exception:
                    # Не прерываем страницу курса, просто оставим без слайдов
                    pass
            # Собираем URL слайдов, если они есть
            if lesson.slides.exists():
                slides_urls = [slide.image.url for slide in lesson.slides.all().order_by('order')]
                all_lesson_slides_data[lesson.id] = slides_urls

    completed_modules_ids = set()
    if student_progress:
        completed_modules_ids = set(student_progress.completed_modules.values_list('id', flat=True))

    modules = list(course.modules.all())
    unlocked_modules_ids = []
    for idx, module in enumerate(modules):
        if idx == 0:
            unlocked_modules_ids.append(module.id)
        elif modules[idx-1].id in completed_modules_ids:
            unlocked_modules_ids.append(module.id)
        elif module.id in completed_modules_ids:
            unlocked_modules_ids.append(module.id)

    # Для кнопки завершения модуля
    completed_lessons = set()
    if student_progress:
        completed_lessons = set(student_progress.completed_lessons.values_list('id', flat=True))
    module_can_be_completed = {}
    for module in modules:
        all_lessons = list(module.lessons.all())
        all_quizzes = list(module.quizzes.all())
        all_lessons_completed = all([lesson.id in completed_lessons for lesson in all_lessons]) if all_lessons else True
        all_quizzes_passed = True
        for quiz in all_quizzes:
            result = quiz_results.get(quiz.id)
            if not result or not result.get('passed'):
                all_quizzes_passed = False
                break
        module_can_be_completed[module.id] = all_lessons_completed and all_quizzes_passed and (module.id not in completed_modules_ids)

    progress = 0
    course_completed = False
    can_leave_feedback = False
    existing_feedback = None
    
    if hasattr(request.user, 'student'):
        student = request.user.student
        progress = student.calculate_progress(course)
        course_completed = course.is_completed_by(student)
        can_leave_feedback = course_completed and not course.has_feedback_from(student)
        existing_feedback = CourseFeedback.objects.filter(student=student, course=course).first()

    return render(request, 'courses/course_detail.html', {
        'course': course,
        'quiz_results': quiz_results,
        'student_progress': student_progress,
        'completed_lessons': completed_lessons,
        'module_progress': module_progress,
        'next_lesson_id_by_module': next_lesson_id_by_module,
        'all_lesson_slides_data': all_lesson_slides_data, # Передаем данные о слайдах
        'completed_modules_ids': completed_modules_ids,
        'unlocked_modules_ids': unlocked_modules_ids,
        'module_can_be_completed': module_can_be_completed,
        'course_progress': progress,
        'course_completed': course_completed,
        'can_leave_feedback': can_leave_feedback,
        'existing_feedback': existing_feedback,
    })

@login_required
def create_course(request):
    if request.method == 'POST':
        course_form = CourseCreationForm(request.POST, request.FILES)
        if course_form.is_valid():
            course_form.save()
            return redirect('admin_courses_page')
    else:
        course_form = CourseCreationForm()

    courses = Course.objects.all()
    return render(request, 'courses/create_course.html', {
        'course_form': course_form,
        'courses': courses,
    })

@login_required
def delete_course(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        course.delete()
        return redirect('admin_courses_page')
    return JsonResponse({'error': 'Метод не разрешен'}, status=405)

# Module Management Views
@login_required
def create_module(request):
    if request.method == 'POST':
        module_form = ModuleCreationForm(request.POST)
        if module_form.is_valid():
            module_form.save()
            return redirect('admin_modules_page')
    else:
        module_form = ModuleCreationForm()

    return render(request, 'courses/create_module.html', {
        'module_form': module_form,
    })

@login_required
def module_details(request, module_id):
    module = Module.objects.get(id=module_id)
    lessons = Lesson.objects.filter(module=module)
    return render(request, 'courses/module_details.html', {
        'module': module,
        'lessons': lessons,
    })

@login_required
def delete_module(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    if request.method == 'POST':
        module.delete()
        return redirect('admin_modules_page')
    return render(request, 'courses/delete_module.html', {'module': module})

def detach_module(request, course_id, module_id):
    course = get_object_or_404(Course, id=course_id)
    module = get_object_or_404(Module, id=module_id)
    course.modules.remove(module)
    return redirect('admin_courses_page')

@login_required
def add_module_to_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    modules = Module.objects.all()

    if request.method == 'POST':
        selected_module_id = request.POST.get('module_id')
        if selected_module_id:
            module = get_object_or_404(Module, id=selected_module_id)
            course.modules.add(module)
            messages.success(request, 'Модуль успешно добавлен к курсу.')
            return redirect('admin_courses_page')

    return render(request, 'courses/add_module_to_course.html', {
        'course': course,
        'modules': modules,
    })

# Lesson Management Views
@login_required
def create_lesson(request, module_id=None):
    if request.method == 'POST':
        lesson_form = LessonCreationForm(request.POST, request.FILES)
        if lesson_form.is_valid():
            lesson = lesson_form.save()
            if module_id:
                module = Module.objects.get(id=module_id)
                module.lessons.add(lesson)
                module.save()
            return redirect('admin_lessons_page')
    else:
        lesson_form = LessonCreationForm()

    return render(request, 'courses/create_lesson.html', {
        'lesson_form': lesson_form,
        'module_id': module_id,
    })

@login_required
def view_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if request.method == 'POST' and 'update_title' in request.POST:
        new_title = request.POST.get('title', '').strip()
        if new_title:
            lesson.title = new_title
            lesson.save()
    return render(request, 'courses/view_lesson.html', {'lesson': lesson})

@login_required
def delete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if request.method == 'POST':
        lesson.delete()
        return redirect('admin_lessons_page')
    return render(request, 'courses/delete_lesson.html', {'lesson': lesson})

@login_required
def replace_video(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if request.method == 'POST' and request.FILES.get('new_video'):
        lesson.video = request.FILES['new_video']
        lesson.save()
        return redirect('view_lesson', lesson_id=lesson.id)
    return HttpResponse("Ошибка при замене видео.", status=400)

@login_required
def replace_pdf(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if request.method == 'POST' and request.FILES.get('new_pdf'):
        lesson.pdf = request.FILES['new_pdf']
        lesson.save()
        return redirect('view_lesson', lesson_id=lesson.id)
    return HttpResponse("Ошибка при замене PDF.", status=400)

@login_required
def edit_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if request.method == 'POST':
        form = LessonCreationForm(request.POST, request.FILES, instance=lesson)
        if form.is_valid():
            form.save()
            return redirect('view_lesson', lesson_id=lesson.id)
    else:
        form = LessonCreationForm(instance=lesson)
    return render(request, 'courses/edit_lesson.html', {'form': form, 'lesson': lesson})

# Quiz Management Views
@login_required
def create_quiz(request):
    if request.method == 'POST':
        quiz_form = QuizForm(request.POST)
        if quiz_form.is_valid():
            quiz = quiz_form.save()
            return redirect('add_question', quiz_id=quiz.id)
    else:
        quiz_form = QuizForm()

    return render(request, 'courses/create_quiz.html', {
        'quiz_form': quiz_form,
    })

@login_required
def add_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    AnswerFormSet = modelformset_factory(Answer, form=AnswerForm, extra=4)

    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        formset = AnswerFormSet(request.POST)

        if question_form.is_valid() and formset.is_valid():
            question = question_form.save(commit=False)
            question.quiz = quiz
            question.save()

            answers = formset.save(commit=False)
            for answer in answers:
                answer.question = question
                answer.save()

            return redirect('add_question', quiz_id=quiz_id)
    else:
        question_form = QuestionForm()
        formset = AnswerFormSet(queryset=Answer.objects.none())

    return render(request, 'courses/add_question.html', {
        'question_form': question_form,
        'formset': formset,
        'quiz': quiz,
    })

@login_required
def quiz_list(request):
    quizzes = Question.objects.all()
    return render(request, 'courses/quiz_list.html', {'quizzes': quizzes})

@login_required
def start_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    student = get_object_or_404(Student, user=request.user)
    module = quiz.module_set.first()
    if not module:
        messages.error(request, f'Квиз "{quiz.title}" не привязан ни к одному модулю. Обратитесь к администратору для привязки квиза к модулю.')
        # Попробуем найти курс через quiz.course_set.first(), если есть связь
        course = None
        if hasattr(quiz, 'course_set') and quiz.course_set.exists():
            course = quiz.course_set.first()
            return redirect('course_detail', course_id=course.id)
        return redirect('student_page')
    course = module.course_set.first()
    if not course:
        messages.error(request, 'Модуль не привязан ни к одному курсу.')
        return redirect('student_page')
    if course not in student.courses.all():
        messages.error(request, 'Вы не записаны на этот курс.')
        return redirect('student_page')
    student_progress = StudentProgress.objects.filter(user=request.user, course=course).first()
    if not student_progress:
        messages.error(request, 'У вас нет прогресса по этому курсу.')
        return redirect('student_page')
    module_lessons = module.lessons.all()
    completed_lessons = student_progress.completed_lessons.all()
    uncompleted_lessons = [lesson for lesson in module_lessons if lesson not in completed_lessons]
    if uncompleted_lessons:
        messages.error(request, f'Для доступа к квизу необходимо пройти все уроки модуля "{module.title}". Осталось пройти {len(uncompleted_lessons)} уроков.')
        return redirect('course_detail', course_id=course.id)
    # Проверяем, сдан ли квиз на 70+
    from .models import QuizAttempt
    last_attempt = QuizAttempt.objects.filter(student=student, quiz=quiz).order_by('-attempt_number').first()
    if last_attempt and last_attempt.passed:
        return redirect('quiz_result', quiz_id=quiz.id)
    if request.method == 'POST':
        correct = 0
        total = quiz.questions.count()
        for question in quiz.questions.all():
            user_answer = request.POST.get(f'question_{question.id}')
            correct_answer = question.answers.filter(is_correct=True).first()
            if user_answer and correct_answer and str(user_answer) == str(correct_answer.id):
                correct += 1
        percent = int((correct / total) * 100) if total else 0
        passed = percent >= 70
        # Определяем номер попытки
        attempt_number = 1
        if last_attempt:
            attempt_number = last_attempt.attempt_number + 1
        # Штраф за неудачу
        stars_penalty = 0
        if not passed:
            stars_penalty = attempt_number * 5
            student.update_stars(-stars_penalty, f"Штраф за неудачную попытку квиза {quiz.title}")
        # Рассчитываем время прохождения
        start_time = request.session.get(f'quiz_start_time_{quiz_id}')
        time_taken = "Н/Д"
        if start_time:
            from datetime import datetime
            import time
            elapsed_seconds = int(time.time() - start_time)
            minutes = elapsed_seconds // 60
            seconds = elapsed_seconds % 60
            time_taken = f"{minutes}:{seconds:02d}"
            # Удаляем время начала из сессии
            del request.session[f'quiz_start_time_{quiz_id}']
        
        QuizAttempt.objects.create(
            student=student,
            quiz=quiz,
            score=percent,
            passed=passed,
            attempt_number=attempt_number,
            stars_penalty=stars_penalty,
            correct_answers=correct,
            incorrect_answers=total - correct,
            total_questions=total,
            time_taken=time_taken
        )
        # Пересчитываем достижения после каждой попытки
        try:
            evaluate_and_unlock_achievements(student)
        except Exception as e:
            print(f"Ошибка при пересчёте достижений: {e}")
            import traceback
            traceback.print_exc()
        
        if passed:
            messages.success(request, f'Квиз сдан! Ваш результат: {percent}%.')
            # Создаем уведомление об успешном прохождении
            Notification.objects.create(
                student=student,
                type='quiz_completed',
                message=f'Квиз "{quiz.title}" успешно пройден! Результат: {percent}% 🎉',
                priority=2
            )
        else:
            messages.error(request, f'Квиз не сдан (результат: {percent}%). Штраф: -{stars_penalty} звёзд. Попробуйте ещё раз.')
            # Создаем уведомление о неудачной попытке
            Notification.objects.create(
                student=student,
                type='quiz_completed',
                message=f'Квиз "{quiz.title}" не пройден. Результат: {percent}%. Штраф: -{stars_penalty} звёзд',
                priority=1
            )
        return redirect('quiz_result', quiz_id=quiz.id)
    # Сохраняем время начала квиза в сессии
    import time
    request.session[f'quiz_start_time_{quiz_id}'] = time.time()
    
    # Создаем уведомление о начале квиза
    Notification.objects.create(
        student=student,
        type='quiz_started',
        message=f'Вы начали прохождение квиза "{quiz.title}"',
        priority=1
    )

    
    return render(request, 'courses/quiz.html', {
        'quiz': quiz,
        'questions': quiz.questions.all()
    })

@login_required
def quiz_result(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    student = get_object_or_404(Student, user=request.user)
    module = quiz.module_set.first()
    course = None
    if module:
        course = module.course_set.first()
    from .models import QuizAttempt, QuizResult
    last_attempt = QuizAttempt.objects.filter(student=student, quiz=quiz).order_by('-attempt_number').first()
    percent = int(last_attempt.score) if last_attempt else 0
    show_stars_notification = False
    stars_awarded = 0
    quiz_result = QuizResult.objects.filter(user=request.user, quiz=quiz).first()
    if last_attempt and last_attempt.passed and last_attempt.attempt_number == 1 and quiz_result and not quiz_result.stars_given:
        if quiz.stars > 0:
            result_info = student.update_stars(quiz.stars, f"Квиз {quiz.title}")
            stars_awarded = quiz.stars
            show_stars_notification = True
            quiz_result.stars_given = True
            quiz_result.save()
            Notification.objects.create(
                student=student,
                type='stars_awarded',
                message=f'Поздравляем! Вы получили {quiz.stars} звёзд за квиз "{quiz.title}".'
            )
    # Обновляем прогресс
    if course:
        progress = student.calculate_progress(course)
        sp = StudentProgress.objects.filter(user=student.user, course=course).first()
        if sp:
            sp.progress = progress
            sp.save()
        # После начисления звёзд пересчитываем достижения
        try:
            evaluate_and_unlock_achievements(student)
        except Exception as e:
            print(f"Ошибка при пересчёте достижений: {e}")
            import traceback
            traceback.print_exc()
    return render(request, 'courses/quiz_result.html', {
        'quiz': quiz,
        'result': last_attempt,
        'course': course,
        'percent': percent,
        'show_stars_notification': show_stars_notification,
        'stars_awarded': stars_awarded,
    })

@login_required
def delete_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    if request.method == 'POST':
        quiz.delete()
        return redirect('admin_quizzes_page')
    return JsonResponse({'error': 'Метод не разрешен'}, status=405)

@login_required
def bind_quiz_to_module(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.method == 'POST':
        form = QuizToModuleForm(request.POST)
        if form.is_valid():
            course = form.cleaned_data['course']
            module = form.cleaned_data['module']
            module.quizzes.add(quiz)
            messages.success(request, 'Квиз успешно привязан к модулю.')
            return redirect('admin_quizzes_page')
    else:
        form = QuizToModuleForm(initial={'quiz': quiz})

    return render(request, 'courses/choose.html', {'form': form, 'quiz': quiz})

@login_required
def edit_quiz(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    
    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        
        if form.is_valid():
            # Сохраняем основную информацию о квизе
            quiz = form.save()
            
            # Получаем все существующие вопросы
            existing_questions = quiz.questions.all()
            
            # Обрабатываем каждый вопрос
            question_ids = request.POST.getlist('question_id[]')
            question_texts = request.POST.getlist('question_text[]')
            
            # Создаем множество ID вопросов, которые нужно сохранить
            questions_to_keep = set()
            
            # Обновляем или создаем вопросы
            for i, (question_id, question_text) in enumerate(zip(question_ids, question_texts)):
                if question_text.strip():  # Проверяем, что текст не пустой
                    if question_id:  # Обновляем существующий вопрос
                        question = Question.objects.get(id=question_id)
                        question.text = question_text
                        question.save()
                    else:  # Создаем новый вопрос
                        question = Question.objects.create(quiz=quiz, text=question_text)
                    
                    questions_to_keep.add(question.id)
                    
                    # Обрабатываем ответы для вопроса
                    answer_texts = request.POST.getlist(f'answer_text_{question.id}')
                    correct_answer = request.POST.get(f'answer_{question.id}')
                    
                    # Удаляем старые ответы
                    question.answers.all().delete()
                    
                    # Создаем новые ответы
                    for j, text in enumerate(answer_texts):
                        if text.strip():  # Проверяем, что текст не пустой
                            Answer.objects.create(
                                question=question,
                                text=text,
                                is_correct=(str(j) == correct_answer)
                            )
            
            # Удаляем вопросы, которых нет в списке для сохранения
            for question in existing_questions:
                if question.id not in questions_to_keep:
                    question.delete()
            
            messages.success(request, 'Квиз успешно обновлен!')
            return redirect('admin_quizzes_page')
    else:
        form = QuizForm(instance=quiz)
    
    # Подготавливаем данные для шаблона
    questions_data = []
    for question in quiz.questions.all():
        questions_data.append({
            'id': question.id,
            'text': question.text,
            'answers': question.answers.all(),
            'correct_answer_index': next((i for i, a in enumerate(question.answers.all()) if a.is_correct), 0)
        })
    
    return render(request, 'courses/edit_quiz.html', {
        'form': form,
        'quiz': quiz,
        'questions_data': questions_data
    })

@login_required
def success_view(request):
    return render(request, 'courses/success.html')

# Progress Tracking Views
@csrf_exempt
def update_progress(request):
    if request.method == 'POST':
        lesson_id = request.POST.get('lesson_id')
        course_id = request.POST.get('course_id')
        user = request.user

        try:
            course = Course.objects.get(id=course_id)
            lesson = Lesson.objects.get(id=lesson_id)
            student_progress, created = StudentProgress.objects.get_or_create(user=user, course=course)

            if lesson not in student_progress.completed_lessons.all():
                student_progress.completed_lessons.add(lesson)

            # Используем правильную логику расчета прогресса (уроки + квизы)
            student = Student.objects.get(user=user)
            progress_value = student.calculate_progress(course)
            
            student_progress.progress = max(0, min(progress_value, 100))
            student_progress.save()

            # Проверяем и начисляем звёзды за завершение курса
            stars_awarded, stars_count = check_and_award_course_stars(student, course)

            # Пересчитываем достижения после обновления прогресса
            try:
                evaluate_and_unlock_achievements(student)
            except Exception as e:
                print(f"Ошибка при пересчёте достижений в update_progress: {e}")

            response_data = {'success': True, 'progress': progress_value}
            if stars_awarded:
                response_data['course_completed'] = True
                response_data['stars_awarded'] = stars_count
                response_data['course_title'] = course.title

            return JsonResponse(response_data)
        except (Course.DoesNotExist, Lesson.DoesNotExist) as e:
            return JsonResponse({'success': False, 'error': 'Курс или урок не найден.'})
    return JsonResponse({'success': False, 'error': 'Некорректный запрос.'})

# Helper Functions
def check_and_award_course_stars(student, course):
    """
    Проверяет завершение курса и начисляет звёзды если курс завершён
    и звёзды ещё не были выданы
    """
    if not course.is_completed_by(student):
        return False, 0
    
    # Создаём или получаем запись о завершении курса
    course_result, created = CourseResult.objects.get_or_create(
        user=student.user,
        course=course,
        defaults={'stars_given': False}
    )
    
    # Если звёзды уже выданы, ничего не делаем
    if course_result.stars_given:
        return False, 0
    
    # Начисляем звёзды
    if course.stars > 0:
        result_info = student.update_stars(course.stars, f"Завершение курса {course.title}")
        course_result.stars_given = True
        course_result.save()
        
        # Создаём уведомление
        Notification.objects.create(
            student=student,
            type='stars_awarded',
            message=f'🎉 Поздравляем! Вы получили {course.stars} звёзд за завершение курса "{course.title}"!',
            priority=3
        )
        
        # Пересчитываем достижения после начисления звёзд
        try:
            evaluate_and_unlock_achievements(student)
        except Exception as e:
            print(f"Ошибка при пересчёте достижений в check_and_award_course_stars: {e}")
        
        return True, course.stars
    
    return False, 0

def calculate_score(post_data, quiz):
    score = 0
    for question in quiz.questions.all():
        user_answer = post_data.get(f'question_{question.id}')
        # Найти правильный ответ
        correct_answer = question.answers.filter(is_correct=True).first()
        if user_answer and correct_answer and str(user_answer) == str(correct_answer.id):
            score += 1
    return score

# User Management Views
@login_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.delete()
        return redirect('admin_page')
    return render(request, 'courses/delete_student.html', {'student': user})

@login_required
def detach_course(request, user_id, course_id):
    if request.method == 'POST':
        student = get_object_or_404(Student, user_id=user_id)
        course = get_object_or_404(Course, id=course_id)
        
        # Открепляем курс от студента
        student.courses.remove(course)
        
        # Удаляем прогресс по этому курсу
        StudentProgress.objects.filter(user=student.user, course=course).delete()
        
        messages.success(request, f'Курс "{course.title}" успешно откреплен от студента {student.user.username}')
        return redirect('admin_page')
    
    return redirect('admin_page')

@login_required
def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()
    # Проверяем, проходил ли пользователь этот квиз
    result = QuizResult.objects.filter(user=request.user, quiz=quiz).first()
    percent = None
    date_taken = None
    if result and result.total_questions:
        percent = int((result.score / result.total_questions) * 100)
        date_taken = result.date_taken
    context = {
        'quiz': quiz,
        'questions': questions,
        'result': result,
        'percent': percent,
        'date_taken': date_taken
    }
    return render(request, 'courses/quiz_detail.html', context)

@login_required
def detach_lesson_from_module(request, lesson_id, module_id):
    module = get_object_or_404(Module, id=module_id)
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if request.method == 'POST':
        module.lessons.remove(lesson)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def detach_quiz_from_module(request, quiz_id, module_id):
    module = get_object_or_404(Module, id=module_id)
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if request.method == 'POST':
        module.quizzes.remove(quiz)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def add_lesson_to_module(request, module_id):
    if request.method == 'POST':
        module = get_object_or_404(Module, id=module_id)
        lesson_id = request.POST.get('lesson_id')
        if lesson_id:
            lesson = get_object_or_404(Lesson, id=lesson_id)
            module.lessons.add(lesson)
            return JsonResponse({'success': True})
    return JsonResponse({'error': 'Ошибка при добавлении урока'}, status=400)

@login_required
def edit_answers_ajax(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    AnswerFormSet = modelformset_factory(Answer, fields=('text', 'is_correct'), extra=0, can_delete=True)
    if request.method == 'POST':
        formset = AnswerFormSet(request.POST, queryset=question.answers.all())
        if formset.is_valid():
            formset.save()
            return HttpResponse('Сохранено!')
    else:
        formset = AnswerFormSet(queryset=question.answers.all())
    return render(request, 'courses/answer_formset_block.html', {'formset': formset, 'question': question})

@login_required
def remove_course_from_student(request, course_id):
    if request.method == 'POST':
        student = get_object_or_404(Student, user=request.user)
        course = get_object_or_404(Course, id=course_id)
        student.courses.remove(course)
        # Also remove any progress data for this course
        StudentProgress.objects.filter(user=request.user, course=course).delete()
        return redirect('student_page')
    return redirect('student_page')

@login_required
def student_public_profile(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    user = student.user
    # Курсы и прогресс
    courses = student.courses.all()
    course_progress = {}
    for course in courses:
        # Используем правильную логику расчета прогресса (уроки + квизы)
        progress_value = student.calculate_progress(course)
        course_progress[course.id] = progress_value
        
        # Обновляем прогресс в базе данных для консистентности
        sp = StudentProgress.objects.filter(user=user, course=course).first()
        if sp:
            sp.progress = progress_value
            sp.save()
    # Группы и рейтинг в группе
    groups = student.groups.all()
    group_ratings = []
    for group in groups:
        group_students = list(group.students.all())
        # Сортировка по звёздам (убывание)
        sorted_students = sorted(group_students, key=lambda s: s.stars, reverse=True)
        place = sorted_students.index(student) + 1 if student in sorted_students else '-'
        group_ratings.append({
            'group': group,
            'place': place,
            'total': len(sorted_students)
        })
    # Пройденные квизы
    quiz_results = QuizResult.objects.filter(user=user).select_related('quiz').order_by('-date_taken')
    quizzes = [
        {
            'quiz': qr.quiz,
            'score': qr.score,
            'total_questions': qr.total_questions,
            'date_taken': qr.date_taken
        }
        for qr in quiz_results
    ]
    # Количество звёзд
    stars = student.stars
    # Передача данных в шаблон
    return render(request, 'courses/student_public_profile.html', {
        'student': student,
        'stars': stars,
        'groups': groups,
        'group_ratings': group_ratings,
        'courses': courses,
        'course_progress': course_progress,  # Добавляем правильные данные прогресса
        'quizzes': quizzes,
    })

@login_required
def delete_group(request, group_id):
    from .models import Group
    group = get_object_or_404(Group, id=group_id)
    if request.method == 'POST':
        group.delete()
        return redirect('admin_page')
    return JsonResponse({'error': 'Метод не разрешен'}, status=405)

@login_required
@require_POST
def mark_notifications_read(request):
    Notification.objects.filter(student__user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})

@login_required
def student_dashboard(request):
    student = get_object_or_404(Student, user=request.user)
    enrollments = []
    for course in student.courses.all():
        progress = student.calculate_progress(course)
        # Обновим прогресс в StudentProgress
        sp = StudentProgress.objects.filter(user=student.user, course=course).first()
        if sp:
            sp.progress = progress
            sp.save()
        enrollments.append({
            'course': course,
            'progress': progress
        })
    context = {
        'student': student,
        'enrollments': enrollments,
    }
    return render(request, 'student_dashboard.html', context)

def get_col(row, *names):
    for name in names:
        for col in row.index:
            if col.strip().lower() == name.strip().lower():
                return str(row[col]).strip()
    return ''

def generate_random_password(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

@login_required
def group_management_page(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    all_students = Student.objects.all().order_by('user__username')
    students_in_group = group.students.all().order_by('user__username')
    students_not_in_group = Student.objects.exclude(id__in=students_in_group.values_list('id', flat=True)).order_by('user__username')

    courses = Course.objects.all().order_by('title')

    if request.method == 'POST':
        if 'edit_group_name' in request.POST:
            new_group_name = request.POST.get('group_name')
            if new_group_name:
                group.name = new_group_name
                group.save()
                messages.success(request, f'Название группы успешно изменено на "{new_group_name}".')
            else:
                messages.error(request, 'Название группы не может быть пустым.')
        elif 'remove_students_from_group' in request.POST:
            student_ids = request.POST.getlist('students_to_remove')
            print(f"DEBUG: Received student_ids for removal: {student_ids}") # Отладочный вывод
            students_to_remove = Student.objects.filter(id__in=student_ids)
            for student in students_to_remove:
                group.students.remove(student)
            group.refresh_from_db() # Обновляем объект группы из базы данных
            messages.success(request, 'Выбранные студенты успешно удалены из группы.')
            print(f"DEBUG: Students in group after removal: {group.students.count()}") # Отладочный вывод
        elif 'add_students_to_group' in request.POST:
            student_ids = request.POST.getlist('students_to_add')
            students_to_add = Student.objects.filter(id__in=student_ids)
            for student in students_to_add:
                group.students.add(student)
            messages.success(request, 'Выбранные студенты успешно добавлены в группу.')
        elif 'attach_course_to_student' in request.POST:
            student_id = request.POST.get('student_id')
            course_id = request.POST.get('course_id')
            student = get_object_or_404(Student, id=student_id)
            course = get_object_or_404(Course, id=course_id)
            if course not in student.courses.all():
                student.courses.add(course)
                messages.success(request, f'Курс "{course.title}" успешно прикреплен к студенту {student.user.username}.')
            else:
                messages.info(request, f'Курс "{course.title}" уже прикреплен к студенту {student.user.username}.')
        
        # После обработки POST-запроса, повторно получаем актуальные данные
        group = get_object_or_404(Group, id=group_id)
        all_students = Student.objects.all().order_by('user__username')
        students_in_group = group.students.all().order_by('user__username')
        students_not_in_group = Student.objects.exclude(id__in=students_in_group.values_list('id', flat=True)).order_by('user__username')
        courses = Course.objects.all().order_by('title')

        context = {
            'group': group,
            'students_in_group': students_in_group,
            'students_not_in_group': students_not_in_group,
            'courses': courses,
        }
        return render(request, 'courses/group_management.html', context)

    # Начальный GET-запрос
    students_in_group = group.students.all().order_by('user__username')
    students_not_in_group = Student.objects.exclude(id__in=students_in_group.values_list('id', flat=True)).order_by('user__username')
    courses = Course.objects.all().order_by('title')

    context = {
        'group': group,
        'students_in_group': students_in_group,
        'students_not_in_group': students_not_in_group,
        'courses': courses,
    }
    return render(request, 'courses/group_management.html', context)

@login_required
@require_POST
@csrf_exempt  # Для простоты тестирования, в продакшене лучше CSRF
def mark_module_complete(request):
    try:
        user = request.user
        module_id = request.POST.get('module_id')
        course_id = request.POST.get('course_id')
        if not module_id or not course_id:
            return JsonResponse({'success': False, 'error': 'No module_id or course_id provided.'}, status=400)
        module = Module.objects.get(id=module_id)
        course = Course.objects.get(id=course_id)
        student = Student.objects.get(user=user)
        sp, created = StudentProgress.objects.get_or_create(user=user, course=course)
        sp.completed_modules.add(module)
        sp.save()

        # Проверяем и начисляем звёзды за завершение курса
        stars_awarded, stars_count = check_and_award_course_stars(student, course)

        response_data = {'success': True}
        if stars_awarded:
            response_data['course_completed'] = True
            response_data['stars_awarded'] = stars_count
            response_data['course_title'] = course.title

        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_POST
@login_required
def mark_lesson_complete(request):
    user = request.user
    lesson_id = request.POST.get('lesson_id')
    course_id = request.POST.get('course_id')
    if not lesson_id or not course_id:
        return JsonResponse({'status': 'error', 'message': 'Отсутствуют данные урока или курса.'}, status=400)
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = get_object_or_404(Course, id=course_id)
    student = get_object_or_404(Student, user=user)
    student_progress, _ = StudentProgress.objects.get_or_create(user=user, course=course)
    if lesson not in student_progress.completed_lessons.all():
        student_progress.completed_lessons.add(lesson)
        student_progress.save()
    # Прогресс
    all_lessons = set()
    for module in course.modules.all():
        all_lessons.update(module.lessons.values_list('id', flat=True))
    completed_lessons = set(student_progress.completed_lessons.values_list('id', flat=True))
    progress = int((len(completed_lessons & all_lessons) / len(all_lessons)) * 100) if all_lessons else 0
    # Следующий урок
    next_lesson_id = None
    ordered_lessons = []
    for module in course.modules.all().order_by('id'):
        ordered_lessons += list(module.lessons.all().order_by('id'))
    for idx, l in enumerate(ordered_lessons):
        if l.id == lesson.id and idx + 1 < len(ordered_lessons):
            next_lesson_id = ordered_lessons[idx + 1].id
            break
    
    # Проверяем и начисляем звёзды за завершение курса
    stars_awarded, stars_count = check_and_award_course_stars(student, course)

    response_data = {
        'status': 'success',
        'message': 'Урок успешно завершён!',
        'new_progress': progress,
        'completed_lesson_id': lesson.id,
        'next_lesson_id': next_lesson_id
    }
    
    if stars_awarded:
        response_data['course_completed'] = True
        response_data['stars_awarded'] = stars_count
        response_data['course_title'] = course.title
    
    return JsonResponse(response_data)

@login_required
def student_message_request(request):
    if not hasattr(request.user, 'student'):
        return redirect('student_page')
    if request.method == 'POST':
        form = StudentMessageRequestForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.student = request.user.student
            msg.status = 'pending'
            msg.save()
            return render(request, 'courses/student_message_success.html')
    else:
        form = StudentMessageRequestForm()
    return render(request, 'courses/student_message_request.html', {'form': form})

@login_required
def admin_message_requests(request):
    if not request.user.is_staff:
        return redirect('admin_page')
    from .models import StudentMessageRequest
    requests = StudentMessageRequest.objects.all().order_by('-created_at')
    return render(request, 'courses/admin_message_requests.html', {'requests': requests})

@login_required
def admin_message_request_detail(request, request_id):
    if not request.user.is_staff:
        return redirect('admin_page')
    from .models import StudentMessageRequest
    msg = StudentMessageRequest.objects.get(id=request_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        response = request.POST.get('admin_response', '')
        if action == 'approve':
            msg.status = 'approved'
        elif action == 'reject':
            msg.status = 'rejected'
        msg.admin_response = response
        from django.utils import timezone
        msg.reviewed_at = timezone.now()
        msg.save()
        return redirect('admin_message_requests')
    return render(request, 'courses/admin_message_request_detail.html', {'msg': msg})


# ===== NOTIFICATION API ENDPOINTS =====

@csrf_exempt
@require_POST
def get_notifications(request):
    """Получение уведомлений для студента (оптимизированная версия)"""
    try:
        student = get_object_or_404(Student, user=request.user)
        # Параметры пагинации
        data = {}
        try:
            data = json.loads(request.body or '{}')
        except Exception:
            data = {}
        offset = int(data.get('offset', 0))
        limit = int(data.get('limit', 10))
        limit = max(1, min(limit, 50))

        # Получаем счетчик непрочитанных отдельно
        unread_count = Notification.objects.filter(student=student, is_read=False).count()
        
        # Порция уведомлений
        notifications_qs = Notification.objects.filter(student=student).order_by('-created_at')
        total_count = notifications_qs.count()
        notifications = notifications_qs[offset:offset+limit]
        
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'type': notification.type,
                'message': notification.message,
                'created_at': notification.created_at.strftime('%d.%m.%Y %H:%M'),
                'is_read': notification.is_read,
                'is_popup_shown': notification.is_popup_shown,
                'priority': notification.priority,
                'icon': get_notification_icon(notification.type),
                'color': get_notification_color(notification.priority)
            })
        
        return JsonResponse({
            'success': True,
            'notifications': notifications_data,
            'unread_count': unread_count,
            'total': total_count,
            'next_offset': offset + len(notifications_data)
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt 
@require_POST
def mark_notification_read(request):
    """Отметить уведомление как прочитанное"""
    try:
        data = json.loads(request.body)
        notification_id = data.get('notification_id')
        
        student = get_object_or_404(Student, email=request.session.get('student_email'))
        notification = get_object_or_404(Notification, id=notification_id, student=student)
        
        notification.is_read = True
        notification.save(update_fields=['is_read'])  # Оптимизация: обновляем только нужное поле
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_POST 
def mark_all_notifications_read(request):
    """Отметить все уведомления как прочитанные"""
    try:
        student = get_object_or_404(Student, user=request.user)
        
        # Массовое обновление для производительности
        Notification.objects.filter(student=student, is_read=False).update(is_read=True)
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_POST
def mark_popup_shown(request):
    """Отметить что всплывающее уведомление было показано"""
    try:
        data = json.loads(request.body)
        notification_id = data.get('notification_id')
        
        student = get_object_or_404(Student, user=request.user)
        notification = get_object_or_404(Notification, id=notification_id, student=student)
        
        notification.is_popup_shown = True
        notification.save(update_fields=['is_popup_shown'])
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_POST
def delete_notification(request):
    """Удалить уведомление"""
    try:
        data = json.loads(request.body)
        notification_id = data.get('notification_id')
        
        student = get_object_or_404(Student, user=request.user)
        notification = get_object_or_404(Notification, id=notification_id, student=student)
        
        notification.delete()
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def get_notification_icon(notification_type):
    """Получить иконку для типа уведомления"""
    icons = {
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
    return icons.get(notification_type, '📢')


def get_notification_color(priority):
    """Получить цвет для приоритета уведомления"""
    colors = {
        1: '#6c757d',  # Низкий - серый
        2: '#17a2b8',  # Средний - голубой  
        3: '#ffc107',  # Высокий - желтый
        4: '#dc3545',  # Критический - красный
    }
    return colors.get(priority, '#6c757d')

@login_required
def course_feedback(request, course_id):
    """Показать форму фидбека или обработать отправку отзыва"""
    course = get_object_or_404(Course, id=course_id)
    student = get_object_or_404(Student, user=request.user)
    
    # Проверяем, завершен ли курс
    if not course.is_completed_by(student):
        return redirect('course_detail', course_id=course_id)
    
    # Проверяем, не оставлял ли уже отзыв
    existing_feedback = CourseFeedback.objects.filter(student=student, course=course).first()
    
    if request.method == 'POST':
        form = CourseFeedbackForm(request.POST, instance=existing_feedback)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.student = student
            feedback.course = course
            feedback.save()
            
            # Добавляем уведомление студенту о принятии отзыва
            Notification.objects.create(
                student=student,
                type='feedback_submitted',
                message=f'Спасибо за отзыв! Ваш отзыв о курсе "{course.title}" принят.',
                extra_data={'course_id': course.id}
            )
            
            return render(request, 'courses/feedback_success.html', {
                'course': course,
                'feedback': feedback
            })
    else:
        form = CourseFeedbackForm(instance=existing_feedback)
    
    return render(request, 'courses/course_feedback.html', {
        'course': course,
        'form': form,
        'existing_feedback': existing_feedback
    })

@login_required 
def course_feedbacks_list(request, course_id):
    """Показать все отзывы о курсе (для администраторов)"""
    if not request.user.is_superuser:
        return redirect('student_page')
        
    course = get_object_or_404(Course, id=course_id)
    feedbacks = CourseFeedback.objects.filter(course=course).select_related('student__user')
    
    # Статистика
    total_feedbacks = feedbacks.count()
    if total_feedbacks > 0:
        avg_rating = feedbacks.aggregate(Avg('rating'))['rating__avg']
        rating_distribution = {}
        for i in range(1, 6):
            rating_distribution[i] = feedbacks.filter(rating=i).count()
    else:
        avg_rating = 0
        rating_distribution = {i: 0 for i in range(1, 6)}
    
    return render(request, 'courses/course_feedbacks_list.html', {
        'course': course,
        'feedbacks': feedbacks,
        'total_feedbacks': total_feedbacks,
        'avg_rating': avg_rating,
        'rating_distribution': rating_distribution
    })

@login_required
def modules_by_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    modules = course.modules.all().order_by('title').values('id', 'title')
    return JsonResponse({'modules': list(modules)})

@login_required
@require_POST
def attach_module_to_course(request):
    module_id = request.POST.get('module_id')
    course_id = request.POST.get('course_id')
    if not module_id or not course_id:
        return JsonResponse({'success': False, 'error': 'Не указан модуль или курс'}, status=400)
    module = get_object_or_404(Module, id=module_id)
    course = get_object_or_404(Course, id=course_id)
    course.modules.add(module)
    return JsonResponse({'success': True})

@login_required
def edit_module(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    if request.method == 'POST':
        form = ModuleCreationForm(request.POST, instance=module)
        if form.is_valid():
            form.save()
            messages.success(request, 'Модуль обновлён')
            return redirect('admin_page')
    else:
        form = ModuleCreationForm(instance=module)
    return render(request, 'courses/create_module.html', {
        'module_form': form,
    })

@login_required
def requests_history(request):
    student_id = request.GET.get('student_id')
    items = []
    profile_qs = ProfileEditRequest.objects.all().select_related('student__user')
    course_add_qs = CourseAddRequest.objects.all().select_related('student__user', 'course')
    message_qs = StudentMessageRequest.objects.all().select_related('student__user')
    if student_id:
        profile_qs = profile_qs.filter(student_id=student_id)
        course_add_qs = course_add_qs.filter(student_id=student_id)
        message_qs = message_qs.filter(student_id=student_id)
    for r in profile_qs:
        items.append({
            'type': 'profile_edit',
            'id': r.id,
            'student': r.student.user.get_full_name() or r.student.user.username,
            'status': r.status,
            'created_at': r.created_at.strftime('%d.%m.%Y %H:%M'),
            'reviewed_at': r.reviewed_at.strftime('%d.%m.%Y %H:%M') if r.reviewed_at else '',
            'course': '',
            'message': '',
            'admin_response': r.admin_response or ''
        })
    for r in course_add_qs:
        items.append({
            'type': 'course_add',
            'id': r.id,
            'student': r.student.user.get_full_name() or r.student.user.username,
            'status': r.status,
            'created_at': r.created_at.strftime('%d.%m.%Y %H:%M'),
            'reviewed_at': r.reviewed_at.strftime('%d.%m.%Y %H:%M') if r.reviewed_at else '',
            'course': r.course.title,
            'message': r.comment or '',
            'admin_response': r.admin_response or ''
        })
    for r in message_qs:
        items.append({
            'type': 'message',
            'id': r.id,
            'student': r.student.user.get_full_name() or r.student.user.username,
            'status': r.status,
            'created_at': r.created_at.strftime('%d.%m.%Y %H:%M'),
            'reviewed_at': r.reviewed_at.strftime('%d.%m.%Y %H:%M') if r.reviewed_at else '',
            'course': '',
            'message': r.message,
            'admin_response': r.admin_response or ''
        })
    # Сортируем по дате создания (новые сверху)
    items.sort(key=lambda x: x['created_at'], reverse=True)
    return JsonResponse({'items': items})

# Новые отдельные страницы админ панели
@login_required
def admin_students_page(request):
    """Страница управления студентами"""
    from .models import Student, Group, StudentMessageRequest, ProfileEditRequest, StudentAchievement
    from django.contrib.auth.models import User
    from django.contrib import messages
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_student':
            try:
                # Создаем пользователя
                username = request.POST.get('email')  # Используем email как username
                email = request.POST.get('email')
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                
                # Проверяем, не существует ли уже пользователь с таким email
                if User.objects.filter(email=email).exists():
                    messages.error(request, 'Пользователь с таким email уже существует')
                else:
                    # Создаем пользователя
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        password='temp123'  # Временный пароль
                    )
                    
                    # Создаем студента
                    student = Student.objects.create(
                        user=user,
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        phone_number=request.POST.get('phone_number', ''),
                        temporary_password='temp123'
                    )
                    
                    # Добавляем в группу, если выбрана
                    group_id = request.POST.get('group')
                    if group_id:
                        try:
                            group = Group.objects.get(id=group_id)
                            student.groups.add(group)
                        except Group.DoesNotExist:
                            pass
                    
                    messages.success(request, f'Студент {first_name} {last_name} успешно добавлен')
                    
            except Exception as e:
                messages.error(request, f'Ошибка при добавлении студента: {str(e)}')
                
        elif action == 'add_group':
            try:
                group_name = request.POST.get('group_name')
                if Group.objects.filter(name=group_name).exists():
                    messages.error(request, 'Группа с таким названием уже существует')
                else:
                    Group.objects.create(name=group_name)
                    messages.success(request, f'Группа "{group_name}" успешно создана')
            except Exception as e:
                messages.error(request, f'Ошибка при создании группы: {str(e)}')
                
        elif action == 'delete_student':
            student_id = request.POST.get('student_id')
            try:
                student = Student.objects.get(id=student_id)
                user = student.user
                student.delete()
                user.delete()
                messages.success(request, 'Студент успешно удален')
            except Student.DoesNotExist:
                messages.error(request, 'Студент не найден')
                
        elif action == 'assign_teacher':
            student_id = request.POST.get('student_id')
            teacher_id = request.POST.get('teacher_id')
            try:
                student = Student.objects.get(id=student_id)
                if teacher_id:
                    teacher = Teacher.objects.get(id=teacher_id)
                    student.teacher = teacher
                else:
                    student.teacher = None
                student.save()
                messages.success(request, f'Студент {student.user.first_name} {student.user.last_name} успешно привязан к преподавателю')
            except (Student.DoesNotExist, Teacher.DoesNotExist):
                messages.error(request, 'Студент или преподаватель не найден')
    
    # Получаем данные для страницы
    students = Student.objects.all().order_by('-user__date_joined')
    groups = Group.objects.all()
    teachers = Teacher.objects.all()
    
    # Объединяем запросы
    message_requests = StudentMessageRequest.objects.all().order_by('-created_at')
    profile_requests = ProfileEditRequest.objects.all().order_by('-created_at')
    
    # Создаем общий список запросов с типом
    total_requests = []
    for message_request in message_requests:
        total_requests.append({
            'id': message_request.id,
            'student': message_request.student,
            'request_type': 'message',
            'message': message_request.message,
            'status': message_request.status,
            'created_at': message_request.created_at,
            'get_status_display': message_request.get_status_display,
        })
    for profile_request in profile_requests:
        total_requests.append({
            'id': profile_request.id,
            'student': profile_request.student,
            'request_type': 'profile',
            'message': 'Редактирование профиля',
            'status': profile_request.status,
            'created_at': profile_request.created_at,
            'get_status_display': profile_request.get_status_display,
        })
    
    # Сортируем по дате создания
    total_requests.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Получаем достижения студентов (более 50% выполнения)
    student_achievements = StudentAchievement.objects.select_related('student', 'achievement').all()
    
    context = {
        'students': students,
        'groups': groups,
        'teachers': teachers,
        'total_requests': total_requests,
        'student_achievements': student_achievements,
        'active_tab': 'students'
    }
    
    return render(request, 'courses/admin_students_page.html', context)

@login_required
def admin_courses_page(request):
    """Страница управления курсами"""
    from .models import Course, Module, Lesson, Quiz
    
    # Получаем данные для страницы
    courses = Course.objects.all()
    modules = Module.objects.all()
    lessons = Lesson.objects.all()
    quizzes = Quiz.objects.all()
    
    context = {
        'courses': courses,
        'modules': modules,
        'lessons': lessons,
        'quizzes': quizzes,
        'active_tab': 'courses'
    }
    
    return render(request, 'courses/admin_courses_page.html', context)

@login_required
def admin_modules_page(request):
    """Страница управления модулями"""
    from .models import Module, Course, Lesson, Quiz
    
    # Получаем данные для страницы
    modules = Module.objects.all()
    courses = Course.objects.all()
    lessons = Lesson.objects.all()
    quizzes = Quiz.objects.all()
    
    context = {
        'modules': modules,
        'courses': courses,
        'lessons': lessons,
        'quizzes': quizzes,
        'active_tab': 'modules'
    }
    
    return render(request, 'courses/admin_modules_page.html', context)

@login_required
def admin_lessons_page(request):
    """Страница управления уроками"""
    from .models import Lesson, Module, Course
    
    # Получаем данные для страницы
    lessons = Lesson.objects.all()
    modules = Module.objects.all()
    courses = Course.objects.all()
    
    context = {
        'lessons': lessons,
        'modules': modules,
        'courses': courses,
        'active_tab': 'lessons'
    }
    
    return render(request, 'courses/admin_lessons_page.html', context)

@login_required
def admin_quizzes_page(request):
    """Страница управления тестами"""
    from .models import Quiz, Module, Course
    
    # Получаем данные для страницы
    quizzes = Quiz.objects.all()
    modules = Module.objects.all()
    courses = Course.objects.all()
    
    context = {
        'quizzes': quizzes,
        'modules': modules,
        'courses': courses,
        'active_tab': 'quizzes'
    }
    
    return render(request, 'courses/admin_quizzes_page.html', context)

@login_required
def admin_requests_page(request):
    """Страница управления запросами"""
    from .models import StudentMessageRequest, ProfileEditRequest, CourseAddRequest
    
    if request.method == 'POST':
        if 'update_status' in request.POST:
            request_type = request.POST.get('request_type')
            request_id = int(request.POST.get('request_id'))
            status = request.POST.get('status')
            
            try:
                if request_type == 'message':
                    req = StudentMessageRequest.objects.get(id=request_id)
                elif request_type == 'profile':
                    req = ProfileEditRequest.objects.get(id=request_id)
                elif request_type == 'course':
                    req = CourseAddRequest.objects.get(id=request_id)
                    if status == 'approved':
                        course_id = request.POST.get('course_id')
                        if not course_id:
                            return JsonResponse({'success': False, 'error': 'Не выбран курс для назначения'})
                        
                        try:
                            course = Course.objects.get(id=course_id)
                            req.assigned_course = course
                            # Добавляем студента к курсу
                            req.student.courses.add(course)
                        except Course.DoesNotExist:
                            return JsonResponse({'success': False, 'error': 'Курс не найден'})
                else:
                    return JsonResponse({'success': False, 'error': 'Неизвестный тип запроса'})
                
                req.status = status
                req.admin_response = request.POST.get('admin_response', '')
                from django.utils import timezone
                req.reviewed_at = timezone.now()
                req.save()
                return JsonResponse({'success': True})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
    
    # Получаем данные для страницы
    message_requests = StudentMessageRequest.objects.all().order_by('-created_at')
    profile_requests = ProfileEditRequest.objects.all().order_by('-created_at')
    course_requests = CourseAddRequest.objects.all().order_by('-created_at')
    courses = Course.objects.all().order_by('title')
    
    context = {
        'message_requests': message_requests,
        'profile_requests': profile_requests,
        'course_requests': course_requests,
        'courses': courses,
        'active_tab': 'requests'
    }
    
    return render(request, 'courses/admin_requests_page.html', context)

@login_required
def get_request_details(request, request_type, request_id):
    """Получение деталей запроса для AJAX"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Доступ запрещен'})
    
    try:
        if request_type == 'message':
            from .models import StudentMessageRequest
            req = StudentMessageRequest.objects.get(id=request_id)
            data = {
                'id': req.id,
                'student_name': f"{req.student.first_name} {req.student.last_name}",
                'student_email': req.student.email,
                'subject': getattr(req, 'subject', ''),
                'message': req.message,
                'status': req.status,
                'created_at': req.created_at.strftime('%d.%m.%Y %H:%M'),
                'admin_response': req.admin_response or '',
                'reviewed_at': req.reviewed_at.strftime('%d.%m.%Y %H:%M') if req.reviewed_at else '',
                'type': 'message'
            }
        elif request_type == 'profile':
            from .models import ProfileEditRequest
            req = ProfileEditRequest.objects.get(id=request_id)
            data = {
                'id': req.id,
                'student_name': f"{req.student.first_name} {req.student.last_name}",
                'student_email': req.student.email,
                'message': 'Запрос на редактирование профиля',
                'status': req.status,
                'created_at': req.created_at.strftime('%d.%m.%Y %H:%M'),
                'admin_response': req.admin_response or '',
                'reviewed_at': req.reviewed_at.strftime('%d.%m.%Y %H:%M') if req.reviewed_at else '',
                'type': 'profile'
            }
        else:
            return JsonResponse({'success': False, 'error': 'Неизвестный тип запроса'})
        
        return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def update_request_status(request):
    """Обновление статуса запроса через AJAX"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Доступ запрещен'})
    
    if request.method == 'POST':
        request_type = request.POST.get('request_type')
        request_id = int(request.POST.get('request_id'))
        status = request.POST.get('status')
        
        try:
            if request_type == 'message':
                from .models import StudentMessageRequest
                req = StudentMessageRequest.objects.get(id=request_id)
            elif request_type == 'profile':
                from .models import ProfileEditRequest
                req = ProfileEditRequest.objects.get(id=request_id)
            elif request_type == 'course':
                from .models import CourseAddRequest
                req = CourseAddRequest.objects.get(id=request_id)
            else:
                return JsonResponse({'success': False, 'error': 'Неизвестный тип запроса'})
            
            req.status = status
            req.admin_response = request.POST.get('admin_response', '')
            from django.utils import timezone
            req.reviewed_at = timezone.now()
            req.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Метод не поддерживается'})

@login_required
def admin_notifications_page(request):
    """Страница управления уведомлениями"""
    from .models import Notification
    
    if request.method == 'POST':
        if 'add_notification' in request.POST:
            try:
                notification_type = request.POST.get('type')
                title = request.POST.get('title')
                message = request.POST.get('message')
                recipient_id = request.POST.get('recipient')
                
                recipient = None
                if recipient_id:
                    from .models import Student
                    recipient = Student.objects.get(id=recipient_id)
                
                Notification.objects.create(
                    type=notification_type,
                    title=title,
                    message=message,
                    recipient=recipient
                )
                messages.success(request, 'Уведомление успешно создано!')
            except Exception as e:
                messages.error(request, f'Ошибка: {str(e)}')
        elif 'delete_notification' in request.POST:
            try:
                notification_id = int(request.POST.get('notification_id'))
                notification = Notification.objects.get(id=notification_id)
                notification.delete()
                messages.success(request, 'Уведомление успешно удалено!')
            except Exception as e:
                messages.error(request, f'Ошибка: {str(e)}')
    
    # Получаем данные для страницы
    notifications = Notification.objects.all()
    
    context = {
        'notifications': notifications,
        'active_tab': 'notifications'
    }
    
    return render(request, 'courses/admin_notifications_page.html', context)

@login_required
def admin_levels_page(request):
    """Страница управления уровнями"""
    from .models import Level
    
    if request.method == 'POST':
        if 'add_level' in request.POST:
            try:
                number = int(request.POST.get('number'))
                name = request.POST.get('name')
                min_stars = int(request.POST.get('min_stars'))
                max_stars = int(request.POST.get('max_stars'))
                description = request.POST.get('description', '')
                image = request.FILES.get('image')
                
                Level.objects.create(
                    number=number, 
                    name=name, 
                    min_stars=min_stars, 
                    max_stars=max_stars,
                    description=description,
                    image=image
                )
                messages.success(request, f'Уровень "{name}" успешно создан!')
            except Exception as e:
                messages.error(request, f'Ошибка: {str(e)}')
        elif 'edit_level' in request.POST:
            try:
                level_id = int(request.POST.get('level_id'))
                level = Level.objects.get(id=level_id)
                level.number = int(request.POST.get('number'))
                level.name = request.POST.get('name')
                level.min_stars = int(request.POST.get('min_stars'))
                level.max_stars = int(request.POST.get('max_stars'))
                level.description = request.POST.get('description', '')
                
                new_image = request.FILES.get('image')
                if new_image:
                    if level.image:
                        level.image.delete(save=False)
                    level.image = new_image
                
                level.save()
                messages.success(request, f'Уровень "{level.name}" успешно обновлен!')
            except Exception as e:
                messages.error(request, f'Ошибка: {str(e)}')
        elif 'remove_image' in request.POST:
            try:
                level_id = int(request.POST.get('level_id'))
                level = Level.objects.get(id=level_id)
                if level.image:
                    level.image.delete(save=False)
                    level.image = None
                    level.save()
                    messages.success(request, f'Изображение уровня "{level.name}" удалено!')
            except Exception as e:
                messages.error(request, f'Ошибка: {str(e)}')
        elif 'delete_level' in request.POST:
            try:
                level_id = int(request.POST.get('level_id'))
                level = Level.objects.get(id=level_id)
                level_name = level.name
                if level.image:
                    level.image.delete(save=False)
                level.delete()
                messages.success(request, f'Уровень "{level_name}" успешно удален!')
            except Exception as e:
                messages.error(request, f'Ошибка: {str(e)}')
    
    # Получаем данные для страницы
    levels = Level.objects.all().order_by('number')
    
    context = {
        'levels': levels,
        'active_tab': 'levels'
    }
    
    return render(request, 'courses/admin_levels_page.html', context)

@login_required
def admin_achievements_page(request):
    """Страница управления достижениями"""
    from .models import Achievement, Student
    
    if request.method == 'POST':
        if 'add_achievement' in request.POST:
            try:
                name = request.POST.get('name')
                description = request.POST.get('description', '')
                condition = request.POST.get('condition')
                image = request.FILES.get('image')
                
                Achievement.objects.create(
                    name=name,
                    description=description,
                    condition=condition,
                    image=image
                )
                messages.success(request, f'Достижение "{name}" успешно создано!')
            except Exception as e:
                messages.error(request, f'Ошибка: {str(e)}')
        elif 'edit_achievement' in request.POST:
            try:
                achievement_id = int(request.POST.get('achievement_id'))
                achievement = Achievement.objects.get(id=achievement_id)
                achievement.name = request.POST.get('name')
                achievement.description = request.POST.get('description', '')
                achievement.condition = request.POST.get('condition')
                
                new_image = request.FILES.get('image')
                if new_image:
                    if achievement.image:
                        achievement.image.delete(save=False)
                    achievement.image = new_image
                
                achievement.save()
                messages.success(request, f'Достижение "{achievement.name}" успешно обновлено!')
            except Exception as e:
                messages.error(request, f'Ошибка: {str(e)}')
        elif 'delete_achievement' in request.POST:
            try:
                achievement_id = int(request.POST.get('achievement_id'))
                achievement = Achievement.objects.get(id=achievement_id)
                achievement_name = achievement.name
                if achievement.image:
                    achievement.image.delete(save=False)
                achievement.delete()
                messages.success(request, f'Достижение "{achievement_name}" успешно удалено!')
            except Exception as e:
                messages.error(request, f'Ошибка: {str(e)}')
    
    # Получаем данные для страницы
    achievements = Achievement.objects.all()
    students = Student.objects.all()
    
    context = {
        'achievements': achievements,
        'students': students,
        'active_tab': 'achievements'
    }
    
    return render(request, 'courses/admin_achievements_page.html', context)

@login_required
def admin_teachers_page(request):
    """Страница управления преподавателями"""
    from .models import Teacher, Course
    from django.db.models import Avg, Count
    
    error = None
    
    # Обработка POST запросов
    if request.method == 'POST':
        if 'add_teacher' in request.POST:
            try:
                # Получаем данные из формы
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                email = request.POST.get('email')
                phone_number = request.POST.get('phone_number', '')
                specialization = request.POST.get('specialization', '')
                bio = request.POST.get('bio', '')
                password = request.POST.get('password')
                avatar = request.FILES.get('avatar')
                
                # Создаем пользователя
                from django.contrib.auth.hashers import make_password
                user = User.objects.create(
                    username=email,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=make_password(password),
                    is_teacher=True
                )
                
                # Создаем профиль преподавателя
                teacher = Teacher.objects.create(
                    user=user,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone_number=phone_number,
                    specialization=specialization,
                    bio=bio,
                    avatar=avatar
                )
                
                messages.success(request, f'Преподаватель {teacher.full_name} успешно добавлен!')
                return redirect('admin_teachers_page')
                
            except Exception as e:
                error = f'Ошибка при создании преподавателя: {str(e)}'
                messages.error(request, error)
                
        elif 'toggle_teacher_status' in request.POST:
            try:
                teacher_id = request.POST.get('teacher_id')
                teacher = Teacher.objects.get(id=teacher_id)
                teacher.is_active = not teacher.is_active
                teacher.save()
                
                status = 'активирован' if teacher.is_active else 'деактивирован'
                messages.success(request, f'Преподаватель {teacher.full_name} {status}!')
                return redirect('admin_teachers_page')
                
            except Exception as e:
                error = f'Ошибка при изменении статуса: {str(e)}'
                messages.error(request, error)
                
        elif 'delete_teacher' in request.POST:
            try:
                teacher_id = request.POST.get('teacher_id')
                teacher = Teacher.objects.get(id=teacher_id)
                teacher_name = teacher.full_name
                
                # Удаляем пользователя (это также удалит профиль преподавателя)
                teacher.user.delete()
                
                messages.success(request, f'Преподаватель {teacher_name} успешно удален!')
                return redirect('admin_teachers_page')
                
            except Exception as e:
                error = f'Ошибка при удалении преподавателя: {str(e)}'
                messages.error(request, error)
    
    # Получаем данные для отображения
    teachers = Teacher.objects.all().order_by('last_name', 'first_name')
    
    # Статистика
    active_teachers_count = teachers.filter(is_active=True).count()
    total_courses_count = Course.objects.filter(teacher__isnull=False).count()
    # Убираем статистику по опыту, так как поле experience_years удалено
    total_teachers_count = teachers.count()
    
    context = {
        'teachers': teachers,
        'active_teachers_count': active_teachers_count,
        'total_courses_count': total_courses_count,
        'total_teachers_count': total_teachers_count,
        'error': error,
        'active_tab': 'teachers'
    }
    
    return render(request, 'courses/admin_teachers_page.html', context)

def teacher_login(request):
    """Логин форма для преподавателей"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            # Ищем пользователя по email
            user = User.objects.get(email=email, is_teacher=True)
            # Проверяем пароль
            if user.check_password(password):
                login(request, user)
                return redirect('teacher_dashboard')  # Редирект на дашборд преподавателя
            else:
                return render(request, 'courses/teacher_login.html', {'error': True})
        except User.DoesNotExist:
            return render(request, 'courses/teacher_login.html', {'error': True})
    
    return render(request, 'courses/teacher_login.html')

@login_required
def teacher_dashboard(request):
    """Дашборд преподавателя"""
    if not hasattr(request.user, 'teacher_profile'):
        return redirect('teacher_login')
    
    teacher = request.user.teacher_profile
    courses = teacher.courses.all()
    
    # Подсчет статистики
    total_modules = sum(course.modules.count() for course in courses)
    total_lessons = sum(module.lessons.count() for course in courses for module in course.modules.all())
    total_quizzes = sum(module.quizzes.count() for course in courses for module in course.modules.all())
    total_students = sum(course.students.count() for course in courses)
    
    context = {
        'teacher': teacher,
        'courses': courses,
        'total_modules': total_modules,
        'total_lessons': total_lessons,
        'total_quizzes': total_quizzes,
        'total_students': total_students,
        'active_tab': 'dashboard'
    }
    
    return render(request, 'courses/teacher_dashboard.html', context)

@login_required
def teacher_courses(request):
    """Управление курсами преподавателя"""
    if not hasattr(request.user, 'teacher_profile'):
        return redirect('teacher_login')
    
    teacher = request.user.teacher_profile
    
    # Обработка создания курса
    if request.method == 'POST' and 'create_course' in request.POST:
        title = request.POST.get('title')
        description = request.POST.get('description')
        stars = request.POST.get('stars', 5)
        image = request.FILES.get('image')
        
        if title and description:
            course = Course.objects.create(
                title=title,
                description=description,
                stars=int(stars),
                teacher=teacher,
                image=image
            )
            messages.success(request, f'Курс "{course.title}" успешно создан!')
            return redirect('teacher_courses')
        else:
            messages.error(request, 'Пожалуйста, заполните все обязательные поля.')
    
    courses = teacher.courses.all()
    
    context = {
        'teacher': teacher,
        'courses': courses,
        'active_tab': 'courses'
    }
    
    return render(request, 'courses/teacher_courses.html', context)

@login_required
def teacher_course_detail(request, course_id):
    """Детальная информация о курсе для преподавателя"""
    if not hasattr(request.user, 'teacher_profile'):
        return redirect('teacher_login')
    
    teacher = request.user.teacher_profile
    try:
        course = teacher.courses.get(id=course_id)
    except Course.DoesNotExist:
        return redirect('teacher_courses')
    
    context = {
        'teacher': teacher,
        'course': course,
        'active_tab': 'courses'
    }
    
    return render(request, 'courses/teacher_course_detail.html', context)

@login_required
def teacher_modules(request):
    """Управление модулями преподавателя"""
    if not hasattr(request.user, 'teacher_profile'):
        return redirect('teacher_login')

    teacher = request.user.teacher_profile
    courses = teacher.courses.all()
    
    # Обработка создания модуля
    if request.method == 'POST' and 'create_module' in request.POST:
        title = request.POST.get('title')
        description = request.POST.get('description')
        course_id = request.POST.get('course_id')
        
        if title and course_id:
            try:
                course = teacher.courses.get(id=course_id)
                module = Module.objects.create(
                    title=title,
                    description=description or ""
                )
                course.modules.add(module)
                messages.success(request, f'Модуль "{module.title}" успешно создан и добавлен к курсу "{course.title}"!')
                return redirect('teacher_modules')
            except Course.DoesNotExist:
                messages.error(request, 'Выбранный курс не найден.')
        else:
            messages.error(request, 'Пожалуйста, заполните все обязательные поля.')
    
    # Получаем модули, которые привязаны к курсам учителя
    modules = []
    for course in courses:
        modules.extend(course.modules.all())
    modules = list(set(modules))  # убираем дубликаты

    context = {
        'teacher': teacher,
        'modules': modules,
        'courses': courses,
        'active_tab': 'modules'
    }

    return render(request, 'courses/teacher_modules.html', context)

@login_required
def teacher_lessons(request):
    """Управление уроками преподавателя"""
    if not hasattr(request.user, 'teacher_profile'):
        return redirect('teacher_login')

    teacher = request.user.teacher_profile
    courses = teacher.courses.all()
    
    # Получаем модули курсов учителя
    modules = []
    for course in courses:
        modules.extend(course.modules.all())
    modules = list(set(modules))  # убираем дубликаты
    
    # Обработка создания урока
    if request.method == 'POST' and 'create_lesson' in request.POST:
        title = request.POST.get('title')
        video_url = request.POST.get('video_url')
        pdf = request.FILES.get('pdf')
        module_id = request.POST.get('module_id')
        
        if title and module_id:
            try:
                # Проверяем, что модуль принадлежит курсам преподавателя
                module = None
                for mod in modules:
                    if mod.id == int(module_id):
                        module = mod
                        break
                
                if module:
                    lesson = Lesson.objects.create(
                        title=title,
                        video_url=video_url or "",
                        pdf=pdf
                    )
                    module.lessons.add(lesson)
                    messages.success(request, f'Урок "{lesson.title}" успешно создан и добавлен к модулю "{module.title}"!')
                    return redirect('teacher_lessons')
                else:
                    messages.error(request, 'Выбранный модуль не найден.')
            except (ValueError, Module.DoesNotExist):
                messages.error(request, 'Выбранный модуль не найден.')
        else:
            messages.error(request, 'Пожалуйста, заполните все обязательные поля.')
    
    # Получаем уроки из модулей
    lessons = []
    for module in modules:
        lessons.extend(module.lessons.all())
    lessons = list(set(lessons))  # убираем дубликаты

    context = {
        'teacher': teacher,
        'lessons': lessons,
        'modules': modules,
        'active_tab': 'lessons'
    }

    return render(request, 'courses/teacher_lessons.html', context)

@login_required
def teacher_quizzes(request):
    if not hasattr(request.user, 'teacher_profile'):
        return redirect('teacher_login')
    
    teacher = request.user.teacher_profile
    
    if request.method == 'POST':
        if 'delete_quiz' in request.POST:
            quiz_id = request.POST.get('quiz_id')
            try:
                quiz = Quiz.objects.get(id=quiz_id)
                quiz.delete()
                messages.success(request, f'Квиз "{quiz.title}" успешно удален.')
                return redirect('teacher_quizzes')
            except Quiz.DoesNotExist:
                messages.error(request, 'Квиз не найден.')
                return redirect('teacher_quizzes')
    """Управление квизами преподавателя"""
    if not hasattr(request.user, 'teacher_profile'):
        return redirect('teacher_login')

    teacher = request.user.teacher_profile
    courses = teacher.courses.all()
    
    # Получаем модули курсов учителя
    modules = []
    for course in courses:
        modules.extend(course.modules.all())
    modules = list(set(modules))  # убираем дубликаты
    
    # Обработка создания квиза
    if request.method == 'POST' and 'create_quiz' in request.POST:
        title = request.POST.get('title')
        description = request.POST.get('description')
        assign_to_module = request.POST.get('assign_to_module') == 'on'
        module_id = request.POST.get('module_id')
        student_ids = request.POST.getlist('student_ids')
        
        if title:
            quiz = Quiz.objects.create(
                title=title,
                description=description or ""
            )
            
            if assign_to_module and module_id:
                try:
                    # Проверяем, что модуль принадлежит курсам преподавателя
                    module = None
                    for mod in modules:
                        if mod.id == int(module_id):
                            module = mod
                            break
                    
                    if module:
                        module.quizzes.add(quiz)
                        messages.success(request, f'Квиз "{quiz.title}" успешно создан и добавлен к модулю "{module.title}"!')
                    else:
                        messages.error(request, 'Выбранный модуль не найден.')
                        quiz.delete()
                        return redirect('teacher_quizzes')
                except (ValueError, Module.DoesNotExist):
                    messages.error(request, 'Выбранный модуль не найден.')
                    quiz.delete()
                    return redirect('teacher_quizzes')
            else:
                # Назначаем студентам
                if student_ids:
                    students = Student.objects.filter(id__in=student_ids)
                    quiz.assigned_students.set(students)
                    student_names = ', '.join([f"{s.user.first_name} {s.user.last_name}" for s in students])
                    messages.success(request, f'Квиз "{quiz.title}" успешно создан и назначен студентам: {student_names}!')
                else:
                    messages.warning(request, f'Квиз "{quiz.title}" создан, но не назначен ни модулю, ни студентам.')
            
            # Перенаправляем на создание вопросов для квиза
            return redirect('teacher_quiz_questions', quiz_id=quiz.id)
        else:
            messages.error(request, 'Пожалуйста, заполните название квиза.')
    
    # Получаем квизы из модулей
    quizzes = []
    for module in modules:
        quizzes.extend(module.quizzes.all())
    
    # Также получаем квизы, назначенные студентам преподавателя
    teacher_students = Student.objects.filter(teacher=teacher)
    for student in teacher_students:
        quizzes.extend(student.assigned_quizzes.all())
    
    quizzes = list(set(quizzes))  # убираем дубликаты

    # Получаем студентов преподавателя
    students = Student.objects.filter(teacher=teacher)
    
    context = {
        'teacher': teacher,
        'quizzes': quizzes,
        'modules': modules,
        'students': students,
        'active_tab': 'quizzes'
    }

    return render(request, 'courses/teacher_quizzes.html', context)

@login_required
def teacher_students(request):
    """Просмотр студентов преподавателя"""
    if not hasattr(request.user, 'teacher_profile'):
        return redirect('teacher_login')
    
    teacher = request.user.teacher_profile
    # Получаем студентов, привязанных к преподавателю
    students = Student.objects.filter(teacher=teacher)
    
    context = {
        'teacher': teacher,
        'students': students,
        'active_tab': 'students'
    }
    
    return render(request, 'courses/teacher_students.html', context)

@login_required
def teacher_quiz_questions(request, quiz_id):
    """Создание вопросов для квиза"""
    if not hasattr(request.user, 'teacher_profile'):
        return redirect('teacher_login')
    
    teacher = request.user.teacher_profile
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Проверяем, что квиз принадлежит преподавателю
    teacher_modules = []
    for course in teacher.courses.all():
        teacher_modules.extend(course.modules.all())
    
    quiz_belongs_to_teacher = False
    for module in teacher_modules:
        if quiz in module.quizzes.all():
            quiz_belongs_to_teacher = True
            break
    
    # Также проверяем, если квиз назначен студентам преподавателя
    if not quiz_belongs_to_teacher:
        teacher_students = Student.objects.filter(teacher=teacher)
        if quiz.assigned_students.filter(id__in=teacher_students.values_list('id', flat=True)).exists():
            quiz_belongs_to_teacher = True
    
    if not quiz_belongs_to_teacher:
        messages.error(request, 'У вас нет доступа к этому квизу.')
        return redirect('teacher_quizzes')
    
    if request.method == 'POST':
        if 'delete_question' in request.POST:
            question_id = request.POST.get('question_id')
            try:
                question = Question.objects.get(id=question_id, quiz=quiz)
                question.delete()
                messages.success(request, 'Вопрос успешно удален.')
                return redirect('teacher_quiz_questions', quiz_id=quiz.id)
            except Question.DoesNotExist:
                messages.error(request, 'Вопрос не найден.')
                return redirect('teacher_quiz_questions', quiz_id=quiz.id)
        elif 'edit_question' in request.POST:
            question_id = request.POST.get('question_id')
            question_text = request.POST.get('question_text')
            print(f"DEBUG: Editing question {question_id} with text: {question_text}")
            try:
                question = Question.objects.get(id=question_id, quiz=quiz)
                question.text = question_text
                question.save()
                
                # Обновляем ответы
                for i in range(1, 5):
                    answer_text = request.POST.get(f'answer_{i}')
                    answer_id = request.POST.get(f'answer_id_{i}')
                    print(f"DEBUG: Answer {i} - text: {answer_text}, id: {answer_id}")
                    if answer_text and answer_id:
                        try:
                            answer = Answer.objects.get(id=answer_id, question=question)
                            answer.text = answer_text
                            answer.save()
                            print(f"DEBUG: Updated answer {answer_id} to: {answer_text}")
                        except Answer.DoesNotExist:
                            print(f"DEBUG: Answer {answer_id} not found")
                            pass
                
                messages.success(request, 'Вопрос успешно обновлен.')
                return redirect('teacher_quiz_questions', quiz_id=quiz.id)
            except Question.DoesNotExist:
                print(f"DEBUG: Question {question_id} not found")
                messages.error(request, 'Вопрос не найден.')
                return redirect('teacher_quiz_questions', quiz_id=quiz.id)
        elif 'add_question' in request.POST:
            question_text = request.POST.get('question_text')
            answers = request.POST.getlist('answer_text')
            correct_answer = request.POST.get('correct_answer')
            
            if question_text and answers and correct_answer is not None:
                question = Question.objects.create(
                    quiz=quiz,
                    text=question_text
                )
                
                for i, answer_text in enumerate(answers):
                    if answer_text.strip():  # Проверяем, что ответ не пустой
                        Answer.objects.create(
                            question=question,
                            text=answer_text,
                            is_correct=(str(i) == correct_answer)
                        )
                
                messages.success(request, f'Вопрос "{question_text[:50]}..." успешно добавлен!')
                return redirect('teacher_quiz_questions', quiz_id=quiz.id)
            else:
                messages.error(request, 'Пожалуйста, заполните все поля вопроса.')
        
        elif 'finish_quiz' in request.POST:
            # Проверяем, есть ли вопросы в квизе
            if quiz.questions.count() == 0:
                messages.error(request, 'Нельзя завершить квиз без вопросов. Добавьте хотя бы один вопрос.')
                return redirect('teacher_quiz_questions', quiz_id=quiz.id)
            
            # Активируем квиз
            quiz.is_active = True
            quiz.save()
            
            messages.success(request, f'Квиз "{quiz.title}" успешно завершен и активирован!')
            return redirect('teacher_quizzes')
    
    questions = quiz.questions.all()
    
    context = {
        'teacher': teacher,
        'quiz': quiz,
        'questions': questions,
        'active_tab': 'quizzes'
    }
    
    return render(request, 'courses/teacher_quiz_questions.html', context)

@login_required
def student_start_quiz(request, quiz_id):
    """Начало прохождения квиза студентом"""
    try:
        student = request.user.student
    except Student.DoesNotExist:
        return redirect('student_login')
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
    
    # Проверяем, доступен ли квиз студенту
    quiz_available = False
    
    # Проверяем через модули курсов
    for course in student.enrolled_courses.all():
        for module in course.modules.all():
            if quiz in module.quizzes.all():
                quiz_available = True
                break
        if quiz_available:
            break
    
    # Проверяем через прямые назначения
    if not quiz_available:
        if quiz in student.assigned_quizzes.all():
            quiz_available = True
    
    if not quiz_available:
        messages.error(request, 'У вас нет доступа к этому квизу.')
        return redirect('student_page')
    
    # Проверяем, есть ли вопросы в квизе
    questions_count = quiz.questions.count()
    if questions_count == 0:
        messages.error(request, 'В этом квизе нет вопросов.')
        return redirect('student_page')
    
    print(f"DEBUG: Quiz {quiz.id} has {questions_count} questions")
    for question in quiz.questions.all():
        print(f"DEBUG: Question {question.id}: {question.text}")
        for answer in question.answers.all():
            print(f"DEBUG: Answer {answer.id}: {answer.text} (correct: {answer.is_correct})")
    
    # Создаем новую попытку
    attempt_number = QuizAttempt.objects.filter(student=student, quiz=quiz).count() + 1
    quiz_attempt = QuizAttempt.objects.create(
        student=student,
        quiz=quiz,
        attempt_number=attempt_number,
        score=0.0,
        passed=False
    )
    
    # Получаем группы студента для отображения в шапке
    groups_count = student.groups.count()
    
    # Рандомизируем вопросы и ответы
    questions = list(quiz.questions.all())
    import random
    random.shuffle(questions)
    
    # Создаем словарь с рандомизированными ответами для каждого вопроса
    questions_with_answers = []
    for question in questions:
        answers = list(question.answers.all())
        random.shuffle(answers)
        questions_with_answers.append({
            'question': question,
            'answers': answers
        })
    
    context = {
        'quiz': quiz,
        'questions_with_answers': questions_with_answers,
        'quiz_attempt': quiz_attempt,
        'groups_count': groups_count
    }
    
    return render(request, 'courses/student_quiz.html', context)

@login_required
def student_submit_quiz(request, quiz_id):
    """Отправка ответов квиза студентом"""
    try:
        student = request.user.student
    except Student.DoesNotExist:
        return redirect('student_login')
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
    
    if request.method == 'POST':
        attempt_id = request.POST.get('quiz_attempt_id')
        quiz_attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=student, quiz=quiz)
        
        # Получаем ответы
        total_questions = quiz.questions.count()
        correct_answers = 0
        
        for question in quiz.questions.all():
            answer_id = request.POST.get(f'question_{question.id}')
            if answer_id:
                try:
                    selected_answer = Answer.objects.get(id=answer_id, question=question)
                    if selected_answer.is_correct:
                        correct_answers += 1
                except Answer.DoesNotExist:
                    pass
        
        # Вычисляем процент правильных ответов
        percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        passed = percentage >= 80  # Проходной балл 80%
        
        # Сохраняем результат
        quiz_attempt.score = percentage
        quiz_attempt.passed = passed
        quiz_attempt.save()
        
        # Если квиз пройден на 100%, даем звезды
        if percentage == 100:
            student.stars += quiz.stars
            student.save()
            messages.success(request, f'Поздравляем! Вы получили {quiz.stars} звезд за идеальное прохождение квиза!')
        
        return redirect('student_quiz_result', quiz_id=quiz.id)
    
    return redirect('student_start_quiz', quiz_id=quiz.id)

@login_required
def student_quiz_result(request, quiz_id):
    """Результат прохождения квиза"""
    try:
        student = request.user.student
    except Student.DoesNotExist:
        return redirect('student_login')
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Получаем последнюю попытку
    latest_attempt = QuizAttempt.objects.filter(
        student=student, 
        quiz=quiz
    ).order_by('-attempt_number').first()
    
    if not latest_attempt:
        messages.error(request, 'Попытка прохождения квиза не найдена.')
        return redirect('student_page')
    
    # Получаем группы студента для отображения в шапке
    groups_count = student.groups.count()
    
    context = {
        'quiz': quiz,
        'attempt': latest_attempt,
        'student': student,
        'groups_count': groups_count
    }
    
    return render(request, 'courses/student_quiz_result.html', context)

@login_required
def teacher_profile(request):
    """Профиль преподавателя"""
    if not hasattr(request.user, 'teacher_profile'):
        return redirect('teacher_login')
    
    teacher = request.user.teacher_profile
    
    context = {
        'teacher': teacher,
        'active_tab': 'profile'
    }
    
    return render(request, 'courses/teacher_profile.html', context)

@login_required
def teacher_student_progress(request):
    """Просмотр прогресса студента для преподавателя"""
    if not hasattr(request.user, 'teacher_profile'):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    teacher = request.user.teacher_profile
    student_id = request.GET.get('student_id')
    
    try:
        student = Student.objects.get(id=student_id, teacher=teacher)
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Student not found'})
    
    # Получаем данные о прогрессе
    from .models import QuizAttempt, StudentProgress
    
    # Прогресс по курсам
    course_progress = []
    for course in student.enrolled_courses.all():
        progress = student.calculate_progress(course)
        course_progress.append({
            'course': course,
            'progress': progress
        })
    
    # Результаты квизов
    quiz_attempts = QuizAttempt.objects.filter(student=student).order_by('-attempt_date')
    
    # Рейтинг студента
    all_students = Student.objects.all().order_by('-stars')
    student_rank = list(all_students.values_list('id', flat=True)).index(student.id) + 1
    
    # Рендерим HTML
    html = render_to_string('courses/teacher_student_progress.html', {
        'student': student,
        'course_progress': course_progress,
        'quiz_attempts': quiz_attempts,
        'student_rank': student_rank
    })
    
    return JsonResponse({'success': True, 'html': html})

# Homework Views
@login_required
def teacher_homework_page(request):
    """Страница домашних заданий для учителя"""
    if not hasattr(request.user, 'teacher_profile'):
        return redirect('teacher_login')
    
    teacher = request.user.teacher_profile
    
    # Получаем всех студентов учителя
    students = Student.objects.filter(teacher=teacher).order_by('user__first_name', 'user__last_name')
    
    # Получаем выбранного студента
    selected_student_id = request.GET.get('student_id')
    selected_student = None
    homeworks = []
    
    if selected_student_id:
        try:
            selected_student = Student.objects.get(id=selected_student_id, teacher=teacher)
            homeworks = Homework.objects.filter(teacher=teacher, student=selected_student).order_by('-created_at')
        except Student.DoesNotExist:
            pass
    
    context = {
        'teacher': teacher,
        'students': students,
        'selected_student': selected_student,
        'homeworks': homeworks,
        'active_tab': 'homework'
    }
    
    return render(request, 'courses/teacher_homework_page.html', context)


@login_required
def teacher_create_homework(request):
    """Создание домашнего задания"""
    if not hasattr(request.user, 'teacher_profile'):
        return redirect('teacher_login')
    
    teacher = request.user.teacher_profile
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        student_id = request.POST.get('student_id')
        due_date = request.POST.get('due_date')
        due_time = request.POST.get('due_time')
        pdf_file = request.FILES.get('pdf_file')
        video_url = request.POST.get('video_url')
        
        if not all([title, description, student_id, due_date, due_time]):
            messages.error(request, 'Пожалуйста, заполните все обязательные поля.')
            return redirect('teacher_create_homework')
        
        try:
            student = Student.objects.get(id=student_id, teacher=teacher)
            
            # Объединяем дату и время
            from datetime import datetime
            due_datetime = datetime.strptime(f"{due_date} {due_time}", "%Y-%m-%d %H:%M")
            
            homework = Homework.objects.create(
                title=title,
                description=description,
                teacher=teacher,
                student=student,
                due_date=due_datetime,
                pdf_file=pdf_file,
                video_url=video_url
            )
            
            # Создаем запись о выполнении
            HomeworkSubmission.objects.create(
                homework=homework,
                student=student
            )
            
            messages.success(request, 'Домашнее задание успешно создано!')
            return redirect('teacher_homework_page')
            
        except Student.DoesNotExist:
            messages.error(request, 'Студент не найден.')
        except Exception as e:
            messages.error(request, f'Ошибка при создании задания: {str(e)}')
    
    # Получаем студентов учителя для формы
    students = Student.objects.filter(teacher=teacher).order_by('user__first_name', 'user__last_name')
    
    context = {
        'teacher': teacher,
        'students': students,
        'active_tab': 'homework'
    }
    
    return render(request, 'courses/teacher_create_homework.html', context)


@login_required
def teacher_homework_detail(request, homework_id):
    """Детали домашнего задания для учителя"""
    if not hasattr(request.user, 'teacher_profile'):
        return redirect('teacher_login')
    
    teacher = request.user.teacher_profile
    homework = get_object_or_404(Homework, id=homework_id, teacher=teacher)
    submission = homework.submissions.first()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'grade':
            grade = request.POST.get('grade')
            comment = request.POST.get('comment')
            
            if submission and grade:
                submission.grade = int(grade)
                submission.teacher_comment = comment
                submission.is_completed = True
                submission.save()
                
                messages.success(request, 'Оценка выставлена!')
                return redirect('teacher_homework_detail', homework_id=homework.id)
        
        elif action == 'delete':
            homework.delete()
            messages.success(request, 'Домашнее задание удалено!')
            return JsonResponse({'success': True})
    
    context = {
        'teacher': teacher,
        'homework': homework,
        'submission': submission,
        'active_tab': 'homework'
    }
    
    return render(request, 'courses/teacher_homework_detail.html', context)


@login_required
def teacher_homework_submissions(request):
    """AJAX для получения выполненных заданий студента"""
    if not hasattr(request.user, 'teacher_profile'):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    teacher = request.user.teacher_profile
    student_id = request.GET.get('student_id')
    
    try:
        student = Student.objects.get(id=student_id, teacher=teacher)
        homeworks = Homework.objects.filter(teacher=teacher, student=student).order_by('-created_at')
        
        html = render_to_string('courses/teacher_homework_list.html', {
            'homeworks': homeworks,
            'student': student
        })
        
        return JsonResponse({'success': True, 'html': html})
        
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Student not found'})

# Student Homework Views
@login_required
def student_homework_page(request):
    """Страница домашних заданий для студента"""
    if not hasattr(request.user, 'student'):
        return redirect('student_login')
    
    student = request.user.student
    
    # Получаем все домашние задания студента
    homeworks = Homework.objects.filter(student=student).order_by('-created_at')
    
    # Группируем по статусу
    pending_homeworks = []
    submitted_homeworks = []
    completed_homeworks = []
    
    for homework in homeworks:
        submission = homework.submissions.first()
        if submission:
            if submission.is_completed:
                completed_homeworks.append(homework)
            elif submission.is_submitted:
                submitted_homeworks.append(homework)
            else:
                pending_homeworks.append(homework)
        else:
            pending_homeworks.append(homework)
    
    context = {
        'student': student,
        'pending_homeworks': pending_homeworks,
        'submitted_homeworks': submitted_homeworks,
        'completed_homeworks': completed_homeworks,
        'total_homeworks': len(homeworks),
        'active_tab': 'homework'
    }
    
    return render(request, 'courses/student_homework_page.html', context)


@login_required
def student_homework_detail(request, homework_id):
    """Детали домашнего задания для студента"""
    if not hasattr(request.user, 'student'):
        return redirect('student_login')
    
    student = request.user.student
    homework = get_object_or_404(Homework, id=homework_id, student=student)
    submission = homework.submissions.first()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'submit':
            # Создаем или обновляем submission
            if not submission:
                submission = HomeworkSubmission.objects.create(
                    homework=homework,
                    student=student
                )
            
            submission.is_submitted = True
            submission.save()
            
            # Обрабатываем загруженные фотографии
            photos = request.FILES.getlist('photos')
            descriptions = request.POST.getlist('photo_descriptions')
            
            for i, photo in enumerate(photos):
                description = descriptions[i] if i < len(descriptions) else ''
                HomeworkPhoto.objects.create(
                    submission=submission,
                    photo=photo,
                    description=description
                )
            
            messages.success(request, 'Домашнее задание отправлено!')
            return redirect('student_homework_detail', homework_id=homework.id)
    
    context = {
        'student': student,
        'homework': homework,
        'submission': submission,
        'active_tab': 'homework'
    }
    
    return render(request, 'courses/student_homework_detail.html', context)


@login_required
def student_homework_submit(request, homework_id):
    """Отправка домашнего задания"""
    if not hasattr(request.user, 'student'):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    student = request.user.student
    homework = get_object_or_404(Homework, id=homework_id, student=student)
    
    if request.method == 'POST':
        try:
            submission = homework.submissions.first()
            if not submission:
                submission = HomeworkSubmission.objects.create(
                    homework=homework,
                    student=student
                )
            
            submission.is_submitted = True
            submission.save()
            
            # Обрабатываем загруженные фотографии
            photos = request.FILES.getlist('photos')
            descriptions = request.POST.getlist('photo_descriptions')
            
            for i, photo in enumerate(photos):
                description = descriptions[i] if i < len(descriptions) else ''
                HomeworkPhoto.objects.create(
                    submission=submission,
                    photo=photo,
                    description=description
                )
            
            # Отправляем уведомление учителю
            try:
                from .models import Notification
                Notification.objects.create(
                    user=homework.teacher.user,
                    title=f"Новое домашнее задание от {student.user.get_full_name()}",
                    message=f"Студент {student.user.get_full_name()} отправил выполнение задания '{homework.title}'",
                    notification_type='homework_submitted',
                    related_id=homework.id
                )
            except Exception as e:
                # Логируем ошибку, но не прерываем процесс
                print(f"Ошибка создания уведомления: {e}")
            
            return JsonResponse({'success': True, 'message': 'Задание успешно отправлено!'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})


@login_required
def student_homework_preview(request, homework_id):
    """Предварительный просмотр домашнего задания перед отправкой"""
    if not hasattr(request.user, 'student'):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    student = request.user.student
    homework = get_object_or_404(Homework, id=homework_id, student=student)
    
    if request.method == 'POST':
        try:
            # Получаем данные для предварительного просмотра
            photos = request.FILES.getlist('photos')
            descriptions = request.POST.getlist('photo_descriptions')
            
            preview_data = []
            for i, photo in enumerate(photos):
                description = descriptions[i] if i < len(descriptions) else ''
                preview_data.append({
                    'name': photo.name,
                    'size': photo.size,
                    'description': description
                })
            
            return JsonResponse({
                'success': True,
                'preview': preview_data,
                'total_photos': len(photos)
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})


@login_required
def student_homework_delete_photo(request, photo_id):
    """Удаление фотографии из отправленного задания"""
    if not hasattr(request.user, 'student'):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    try:
        photo = get_object_or_404(HomeworkPhoto, id=photo_id)
        # Проверяем, что фотография принадлежит студенту
        if photo.submission.student.user == request.user:
            photo.delete()
            return JsonResponse({'success': True, 'message': 'Фотография удалена'})
        else:
            return JsonResponse({'success': False, 'error': 'Unauthorized'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def student_courses_page(request):
    """Отдельная страница курсов студента"""
    student = get_object_or_404(Student, user=request.user)
    courses = student.courses.all()
    
    # Convert progress_data to a dictionary with course IDs as keys
    progress_data = {}
    course_completed_data = {}
    for course in courses:
        # Используем правильную логику расчета прогресса (уроки + квизы)
        progress_value = student.calculate_progress(course)
        progress_data[course.id] = progress_value
        
        # Проверяем, завершен ли курс
        course_completed = course.is_completed_by(student)
        course_completed_data[course.id] = course_completed
        
        # Обновляем прогресс в базе данных для консистентности
        sp = StudentProgress.objects.filter(user=request.user, course=course).first()
        if sp:
            sp.progress = progress_value
            sp.save()

    show_course_notification = False
    all_courses = Course.objects.all()
    
    # Данные для уведомлений
    notifications = Notification.objects.filter(student=student).order_by('-created_at')[:10]
    unread_count = Notification.objects.filter(student=student, is_read=False).count()
    
    if request.method == 'POST':
        if 'course_code' in request.POST:
            course_code = request.POST.get('course_code')
            try:
                course = Course.objects.get(course_code=course_code)
                student.courses.add(course)
                show_course_notification = True
                Notification.objects.create(
                    student=student,
                    type='course_approved',
                    message=f'Вы были добавлены на курс "{course.title}" через код.'
                )
                # Пересчитываем данные прогресса для обновленного списка курсов
                updated_progress_data = {}
                updated_course_completed_data = {}
                for course in student.courses.all():
                    progress_value = student.calculate_progress(course)
                    updated_progress_data[course.id] = progress_value
                    updated_course_completed_data[course.id] = course.is_completed_by(student)
                
                return render(request, 'courses/student_courses_page.html', {
                    'courses': student.courses.all(),
                    'progress_data': updated_progress_data,
                    'course_completed_data': updated_course_completed_data,
                    'student': student,
                    'show_course_notification': show_course_notification,
                    'all_courses': all_courses,
                    'notifications': notifications,
                    'unread_notifications_count': unread_count,
                })
            except Course.DoesNotExist:
                messages.error(request, 'Курс с таким кодом не найден.')
    
    context = {
        'courses': courses,
        'progress_data': progress_data,
        'course_completed_data': course_completed_data,
        'student': student,
        'show_course_notification': show_course_notification,
        'all_courses': all_courses,
        'notifications': notifications,
        'unread_notifications_count': unread_count,
    }
    
    return render(request, 'courses/student_courses_page.html', context)


@login_required
def student_rating_page(request):
    """Отдельная страница рейтинга студента"""
    student = get_object_or_404(Student, user=request.user)
    groups = student.groups.all().prefetch_related('students__user')
    
    # Создаем рейтинг групп
    rating_groups = []
    for group in groups:
        group_students = group.students.all().select_related('user').order_by('-stars', 'user__first_name')
        students_with_rating = []
        for position, group_student in enumerate(group_students, 1):
            students_with_rating.append({
                'student': group_student,
                'position': position
            })
        
        rating_groups.append({
            'name': group.name,
            'students_with_rating': students_with_rating
        })
    
    # Количество групп для хедера
    groups_count = groups.count()
    
    # Данные для уведомлений
    notifications = Notification.objects.filter(student=student).order_by('-created_at')[:10]
    unread_count = Notification.objects.filter(student=student, is_read=False).count()
    
    context = {
        'student': student,
        'groups': groups,
        'rating_groups': rating_groups,
        'groups_count': groups_count,
        'notifications': notifications,
        'unread_notifications_count': unread_count,
    }
    
    return render(request, 'courses/student_rating_page.html', context)

@login_required
def wheel_of_fortune_page(request):
    """Страница колеса фортуны"""
    return render(request, 'courses/wheel_of_fortune_page.html')

@login_required
def check_wheel_status(request):
    """API для проверки статуса колеса фортуны"""
    try:
        can_spin = WheelSpin.can_spin_now(request.user.student)
        next_spin_time = WheelSpin.get_next_spin_time(request.user.student)
        
        return JsonResponse({
            'success': True,
            'can_spin': can_spin,
            'next_spin_time': next_spin_time.isoformat() if next_spin_time else None,
            'current_stars': request.user.student.stars
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def check_spin_availability(request):
    """API для проверки доступности спина колеса фортуны"""
    try:
        from django.utils import timezone
        
        can_spin = WheelSpin.can_spin_now(request.user.student)
        
        response_data = {
            'can_spin': can_spin
        }
        
        if not can_spin:
            next_spin_time = WheelSpin.get_next_spin_time(request.user.student)
            if next_spin_time:
                time_remaining = next_spin_time - timezone.now()
                response_data['time_remaining'] = int(time_remaining.total_seconds())
                response_data['next_spin_time'] = next_spin_time.isoformat()
        
        return JsonResponse(response_data)
    
    except Exception as e:
        return JsonResponse({
            'can_spin': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
@csrf_exempt
def spin_wheel(request):
    """API для вращения колеса фортуны"""
    try:
        # Логируем входящие данные для отладки
        print(f"Spin wheel request from user: {request.user.username}")
        print(f"Request body: {request.body}")
        
        # Проверяем, может ли студент крутить сейчас (раз в 24 часа)
        if not WheelSpin.can_spin_now(request.user.student):
            next_spin_time = WheelSpin.get_next_spin_time(request.user.student)
            print(f"User {request.user.username} already spun recently")
            
            # Вычисляем оставшееся время
            from django.utils import timezone
            time_remaining = next_spin_time - timezone.now()
            hours = int(time_remaining.total_seconds() // 3600)
            minutes = int((time_remaining.total_seconds() % 3600) // 60)
            
            return JsonResponse({
                'success': False,
                'error': f'Вы уже крутили колесо недавно. Следующий спин будет доступен через {hours}ч {minutes}м.',
                'next_spin_time': next_spin_time.isoformat() if next_spin_time else None
            })
        
        data = json.loads(request.body)
        prize = data.get('prize', '0⭐')
        print(f"Prize: {prize}")
        
        # Извлекаем количество звезд из приза
        star_count = int(prize.replace('⭐', ''))
        
        # Создаем запись о спине
        wheel_spin = WheelSpin.objects.create(
            student=request.user.student,
            stars_earned=star_count
        )
        
        # Добавляем звезды к балансу студента
        if star_count > 0:
            student = request.user.student
            student.stars += star_count
            student.save()
        
        return JsonResponse({
            'success': True,
            'prize': prize,
            'stars_earned': star_count,
            'total_stars': request.user.student.stars,
            'spin_id': wheel_spin.id
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
def student_levels_page(request):
    """Отдельная страница уровней студента"""
    student = get_object_or_404(Student, user=request.user)
    
    # Данные для уровней
    all_levels = Level.objects.all().only('number', 'name', 'min_stars', 'max_stars', 'description', 'image').order_by('number')
    
    # Пересчитываем достижения при загрузке страницы
    try:
        evaluate_and_unlock_achievements(student)
    except Exception as e:
        print(f"Ошибка при пересчёте достижений в student_levels_page: {e}")
        import traceback
        traceback.print_exc()
    
    # Достижения
    from .models import Achievement, StudentAchievement
    all_achievements = Achievement.objects.filter(is_active=True).order_by('condition_type', 'condition_value')
    unlocked_achievements = StudentAchievement.objects.filter(student=student).select_related('achievement').order_by('-unlocked_at')
    unlocked_ids = set(unlocked_achievements.values_list('achievement_id', flat=True))
    locked_achievements = all_achievements.exclude(id__in=unlocked_ids)
    progress_by_id = {}
    
    for ach in all_achievements:
        try:
            progress_by_id[ach.id] = get_achievement_progress(student, ach)
        except Exception as e:
            print(f"Ошибка при расчёте прогресса достижения {ach.title}: {e}")
            progress_by_id[ach.id] = {'current': 0, 'target': ach.condition_value or 1, 'percentage': 0}
    
    # Данные для уведомлений
    notifications = Notification.objects.filter(student=student).order_by('-created_at')[:10]
    unread_count = Notification.objects.filter(student=student, is_read=False).count()
    
    context = {
        'student': student,
        'all_levels': all_levels,
        'all_achievements': all_achievements,
        'unlocked_achievements': unlocked_achievements,
        'locked_achievements': locked_achievements,
        'progress_by_id': progress_by_id,
        'notifications': notifications,
        'unread_notifications_count': unread_count,
    }
    
    return render(request, 'courses/student_levels_page.html', context)


@login_required
def student_quizzes_page(request):
    """Отдельная страница квизов студента"""
    student = get_object_or_404(Student, user=request.user)
    
    # Получаем курсы студента
    courses = student.courses.all().prefetch_related('modules__quizzes')
    
    # Получаем квизы студента (из модулей курсов и прямые назначения)
    student_quizzes = []
    
    # Квизы из модулей курсов
    for course in courses:
        for module in course.modules.all():
            for quiz in module.quizzes.filter(is_active=True):
                if quiz not in student_quizzes:
                    student_quizzes.append(quiz)
    
    # Прямые назначения квизов
    for quiz in student.assigned_quizzes.filter(is_active=True):
        if quiz not in student_quizzes:
            student_quizzes.append(quiz)
    
    # Добавляем информацию о результатах квизов
    for quiz in student_quizzes:
        latest_attempt = QuizAttempt.objects.filter(
            student=student, 
            quiz=quiz
        ).order_by('-created_at').first()
        
        if latest_attempt:
            quiz.latest_attempt = latest_attempt
            quiz.best_score = QuizAttempt.objects.filter(
                student=student, 
                quiz=quiz
            ).aggregate(Max('score'))['score__max']
        else:
            quiz.latest_attempt = None
            quiz.best_score = None
    
    # Данные для уведомлений
    notifications = Notification.objects.filter(student=student).order_by('-created_at')[:10]
    unread_count = Notification.objects.filter(student=student, is_read=False).count()
    
    context = {
        'student': student,
        'student_quizzes': student_quizzes,
        'notifications': notifications,
        'unread_notifications_count': unread_count,
    }
    
    return render(request, 'courses/student_quizzes_page.html', context)


@login_required
def student_homework_standalone_page(request):
    """Отдельная страница домашних заданий студента"""
    student = get_object_or_404(Student, user=request.user)
    
    # Получаем все домашние задания студента
    homeworks = Homework.objects.filter(student=student).order_by('-created_at')
    
    # Группируем по статусу
    pending_homeworks = []
    submitted_homeworks = []
    completed_homeworks = []
    
    for homework in homeworks:
        submission = homework.submissions.first()
        if submission:
            if submission.is_completed:
                completed_homeworks.append(homework)
            elif submission.is_submitted:
                submitted_homeworks.append(homework)
            else:
                pending_homeworks.append(homework)
        else:
            pending_homeworks.append(homework)
    
    # Данные для уведомлений
    notifications = Notification.objects.filter(student=student).order_by('-created_at')[:10]
    unread_count = Notification.objects.filter(student=student, is_read=False).count()
    
    context = {
        'student': student,
        'pending_homeworks': pending_homeworks,
        'submitted_homeworks': submitted_homeworks,
        'completed_homeworks': completed_homeworks,
        'total_homeworks': len(homeworks),
        'notifications': notifications,
        'unread_notifications_count': unread_count,
    }
    
    return render(request, 'courses/student_homework_standalone_page.html', context)

@login_required
def student_requests_page(request):
    """Отдельная страница запросов студента"""
    student = get_object_or_404(Student, user=request.user)
    
    # Получаем запросы студента
    add_course_requests = CourseAddRequest.objects.filter(student=student).order_by('-created_at')
    message_requests = StudentMessageRequest.objects.filter(student=student).order_by('-created_at')
    
    # Данные для уведомлений
    notifications = Notification.objects.filter(student=student).order_by('-created_at')[:10]
    unread_count = Notification.objects.filter(student=student, is_read=False).count()
    
    if request.method == 'POST':
        if 'add_course_request' in request.POST:
            course_name = request.POST.get('course_name')
            comment = request.POST.get('course_comment')
            
            if course_name:
                CourseAddRequest.objects.create(
                    student=student, 
                    course_name=course_name, 
                    comment=comment
                )
                Notification.objects.create(
                    student=student,
                    type='course_approved',
                    message=f'Ваш запрос на добавление курса "{course_name}" отправлен администратору.'
                )
                messages.success(request, 'Запрос на добавление курса отправлен!')
            else:
                messages.error(request, 'Пожалуйста, укажите название курса.')
            
            return redirect('student_requests_page')
        elif 'message_request' in request.POST:
            message = request.POST.get('message')
            if message:
                StudentMessageRequest.objects.create(student=student, message=message)
                Notification.objects.create(
                    student=student,
                    type='profile_edit',
                    message='Ваш произвольный запрос отправлен администратору.'
                )
                messages.success(request, 'Произвольный запрос отправлен!')
                return redirect('student_requests_page')
        elif 'delete_message_request' in request.POST:
            req_id = request.POST.get('delete_message_request')
            req = StudentMessageRequest.objects.filter(id=req_id, student=student).first()
            if req:
                req.delete()
                messages.success(request, 'Запрос удалён!')
                return redirect('student_requests_page')
    
    context = {
        'student': student,
        'course_requests': add_course_requests,
        'message_requests': message_requests,
        'notifications': notifications,
        'unread_notifications_count': unread_count,
    }
    
    return render(request, 'courses/student_requests_page.html', context)