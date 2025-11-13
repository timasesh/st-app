# courses/forms.py
# courses/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import User, Lesson, Module, Course, Student, Teacher
from .models import Question, Answer
from django.db import transaction
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import re
from .models import StudentMessageRequest
from .models import CourseFeedback
from .models import CourseAddRequest


class StudentQuickRegistrationForm(forms.ModelForm):
    """Форма быстрой регистрации без пароля."""

    class Meta:
        model = get_user_model()
        fields = ['first_name', 'last_name', 'username', 'email']
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'username': 'Имя пользователя',
            'email': 'Email',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control',
                'placeholder': field.label,
            })

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and get_user_model().objects.filter(username=username).exists():
            raise forms.ValidationError("Пользователь с таким именем уже существует.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and get_user_model().objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует.")
        return email


class StudentRegistrationForm(forms.Form):
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
    
    username = forms.CharField(max_length=150, label='Имя пользователя')
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(required=True, label='Имя')
    last_name = forms.CharField(required=True, label='Фамилия')
    age = forms.IntegerField(min_value=5, max_value=100, required=True, label='Возраст')
    phone_number = forms.CharField(max_length=20, required=True, label='Номер телефона')
    is_school_student = forms.BooleanField(required=False, initial=True, label='Я школьник')
    grade = forms.ChoiceField(choices=[('', 'Выберите класс')] + GRADE_CHOICES, required=False, label='Класс')
    password1 = forms.CharField(widget=forms.PasswordInput, label='Пароль')
    password2 = forms.CharField(widget=forms.PasswordInput, label='Подтверждение пароля')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем CSS классы и атрибуты для полей
        self.fields['grade'].widget.attrs.update({
            'class': 'form-control',
        })

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Проверяем, есть ли пользователь с таким именем
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError(f"Пользователь с именем '{username}' уже существует. Выберите другое имя пользователя.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Проверяем, есть ли пользователь с таким email
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError(f"Пользователь с email '{email}' уже существует. Используйте другой email адрес.")
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают.")
        return password2

    def clean_grade(self):
        is_school_student = self.cleaned_data.get('is_school_student')
        grade = self.cleaned_data.get('grade')
        
        if is_school_student and not grade:
            raise forms.ValidationError("Для школьников обязательно указывать класс")
        if not is_school_student and grade:
            raise forms.ValidationError("Для не школьников класс указывать не нужно")
        
        return grade

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        # Простая валидация номера телефона
        if phone_number:
            # Проверяем, что номер содержит только цифры
            if not phone_number.isdigit():
                raise forms.ValidationError("Номер телефона должен содержать только цифры")
            if len(phone_number) < 10:
                raise forms.ValidationError("Номер телефона должен содержать минимум 10 цифр")
            if len(phone_number) > 11:
                raise forms.ValidationError("Номер телефона должен содержать максимум 11 цифр")
            
            # Проверяем уникальность номера телефона
            if Student.objects.filter(phone_number=phone_number).exists():
                raise forms.ValidationError("Пользователь с таким номером телефона уже существует.")
        return phone_number

    def save(self, commit=True):
        username = self.cleaned_data['username']
        email = self.cleaned_data['email']
        first_name = self.cleaned_data.get('first_name', '')
        last_name = self.cleaned_data.get('last_name', '')
        age = self.cleaned_data.get('age')
        phone_number = self.cleaned_data.get('phone_number', '')
        is_school_student = self.cleaned_data.get('is_school_student', True)
        grade = self.cleaned_data.get('grade')
        password = self.cleaned_data['password1']
        
        with transaction.atomic():
            # Пытаемся найти существующего пользователя
            user = User.objects.filter(username=username).first()
            
            if user:
                # Пользователь существует, обновляем его данные
                user.email = email
                user.first_name = first_name
                user.last_name = last_name
                user.is_student = True
                user.set_password(password)
                if commit:
                    user.save()
            else:
                # Создаем нового пользователя
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                user.is_student = True
                if commit:
                    user.save()
            
            # Создаем объект Student (если его еще нет)
            if commit:
                student, created = Student.objects.get_or_create(
                    user=user,
                    defaults={
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'phone_number': phone_number,
                        'is_school_student': is_school_student,
                        'grade': grade,
                        'age': age,
                    }
                )
                if not created:
                    # Если Student уже существует, обновляем его данные
                    student.email = email
                    student.first_name = first_name
                    student.last_name = last_name
                    student.phone_number = phone_number
                    student.is_school_student = is_school_student
                    student.grade = grade
                    student.age = age
                    student.save()
        
        return user


class LessonCreationForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'video', 'video_url', 'pdf', 'convert_pdf_to_slides']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название урока'}),
            'video': forms.FileInput(attrs={'class': 'form-control'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Ссылка на видео (YouTube, Vimeo, Google Drive, Dropbox, OneDrive)'}),
            'pdf': forms.FileInput(attrs={'class': 'form-control'}),
            'convert_pdf_to_slides': forms.CheckboxInput(attrs={'class': 'form-check-input mt-0 ms-2'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        video = cleaned_data.get('video')
        video_url = cleaned_data.get('video_url')
        pdf = cleaned_data.get('pdf')
        convert_pdf_to_slides = cleaned_data.get('convert_pdf_to_slides')

        # Проверяем, что есть хотя бы один тип контента
        if not video and not video_url and not pdf:
            raise ValidationError('Необходимо указать либо видеофайл, либо URL видео, либо PDF файл')
        
        # Нельзя одновременно загружать видео файл и указывать URL
        if video and video_url:
            raise ValidationError('Нельзя указать одновременно видеофайл и URL видео')

        # Валидация URL видео
        if video_url:
            # Проверка формата URL
            url_validator = URLValidator()
            try:
                url_validator(video_url)
            except ValidationError:
                raise ValidationError('Некорректный формат URL')

            # Проверка поддерживаемых сервисов
            supported_services = [
                'youtube.com', 'youtu.be',  # YouTube
                'vimeo.com',                # Vimeo
                'drive.google.com',         # Google Drive
                'dropbox.com',              # Dropbox
                '1drv.ms', 'onedrive.live.com'  # OneDrive
            ]
            
            if not any(service in video_url.lower() for service in supported_services):
                raise ValidationError('Неподдерживаемый сервис. Используйте YouTube, Vimeo, Google Drive, Dropbox или OneDrive')

            # Специфичные проверки для каждого сервиса
            if 'youtube.com' in video_url or 'youtu.be' in video_url:
                if 'youtube.com/watch' in video_url:
                    if not re.search(r'v=[a-zA-Z0-9_-]+', video_url):
                        raise ValidationError('Некорректная ссылка на YouTube видео')
                elif 'youtu.be' in video_url:
                    if not re.search(r'youtu\.be/[a-zA-Z0-9_-]+', video_url):
                        raise ValidationError('Некорректная ссылка на YouTube видео')

            elif 'drive.google.com' in video_url:
                if not ('/d/' in video_url or 'id=' in video_url):
                    raise ValidationError('Некорректная ссылка на Google Drive')

            elif 'dropbox.com' in video_url:
                if not video_url.endswith(('.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm')):
                    raise ValidationError('Ссылка должна указывать на видеофайл в Dropbox')

            elif '1drv.ms' in video_url or 'onedrive.live.com' in video_url:
                if not ('/redir?' in video_url or '/embed?' in video_url):
                    raise ValidationError('Некорректная ссылка на OneDrive')

        # Валидация конвертации PDF в слайды
        if convert_pdf_to_slides and not pdf:
            raise ValidationError('Для конвертации в слайды необходимо прикрепить PDF файл')

        return cleaned_data


class ModuleCreationForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title', 'description', 'lessons']
        widgets = {
            'lessons': forms.CheckboxSelectMultiple
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['lessons'].required = False
        # Показываем только реально существующие уроки (можно добавить фильтр по статусу, если появится soft delete)
        self.fields['lessons'].queryset = Lesson.objects.all().order_by('id', 'title')
        # Для description — красивый textarea
        if 'description' in self.fields:
            self.fields['description'].widget = forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Краткое описание модуля'})


class CourseCreationForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'modules', 'teacher', 'image', 'stars']
        widgets = {
            'modules': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['title'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Название курса'})
        self.fields['description'].widget = forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 3, 
            'placeholder': 'Краткое описание курса'
        })
        self.fields['modules'].widget.attrs.update({
            'style': 'max-height:180px;overflow-y:auto;background:#f8f9fa;border-radius:10px;padding:0.7rem 1rem;margin-bottom:1.2rem;'
        })
        self.fields['teacher'].widget.attrs.update({'class': 'form-control'})
        self.fields['teacher'].queryset = Teacher.objects.filter(is_active=True).order_by('last_name', 'first_name')
        self.fields['image'].widget.attrs.update({'class': 'form-control', 'accept': 'image/*'})
        self.fields['stars'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Количество звёзд за прохождение'
        })


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text']


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text']


from django import forms
from django.forms import inlineformset_factory
from .models import Quiz, Question, Answer


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'stars']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Название квиза'})
        self.fields['stars'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Звёздочки за квиз', 'min': 1, 'type': 'number'})


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text']


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text', 'is_correct']


AnswerFormSet = inlineformset_factory(Question, Answer, form=AnswerForm, extra=4)

from .models import Course, Module, Quiz, Lesson


class QuizToModuleForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.all(), required=True, label='Курс')
    module = forms.ModelChoiceField(queryset=Module.objects.none(), required=True, label='Модуль')
    quiz = forms.ModelChoiceField(queryset=Quiz.objects.all(), required=True, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Стили
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
        # Если есть initial для quiz — ограничим queryset одним квизом
        quiz_initial = self.initial.get('quiz') if hasattr(self, 'initial') else None
        if quiz_initial:
            try:
                quiz_id = quiz_initial.id if hasattr(quiz_initial, 'id') else int(quiz_initial)
                self.fields['quiz'].queryset = Quiz.objects.filter(id=quiz_id)
                self.fields['quiz'].initial = quiz_id
            except Exception:
                pass
        # Фильтрация модулей по выбранному курсу (данные из POST) или initial
        self.fields['module'].queryset = Module.objects.none()
        if 'course' in self.data:
            try:
                course_id = int(self.data.get('course'))
                self.fields['module'].queryset = Course.objects.get(id=course_id).modules.all().order_by('title')
            except (ValueError, TypeError, Course.DoesNotExist):
                self.fields['module'].queryset = Module.objects.none()
        elif self.initial.get('course'):
            course_obj = self.initial.get('course')
            try:
                self.fields['module'].queryset = course_obj.modules.all().order_by('title')
            except Exception:
                self.fields['module'].queryset = Module.objects.none()


class StudentProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False, label='Имя')
    last_name = forms.CharField(max_length=30, required=False, label='Фамилия')
    age = forms.IntegerField(min_value=5, max_value=100, required=False, label='Возраст')
    grade = forms.ChoiceField(
        choices=[('', 'Выберите класс')] + [
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
        ],
        required=False,
        label='Класс'
    )
    
    class Meta:
        model = Student
        fields = ['avatar', 'phone_number', 'email', 'age', 'grade']
        widgets = {
            'department': forms.NumberInput(attrs={'min': 1, 'max': 12}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем CSS классы для всех полей
        self.fields['avatar'].widget.attrs.update({
            'class': 'form-control-file',
            'accept': 'image/*'
        })
        self.fields['phone_number'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Номер телефона'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Email адрес'
        })
        self.fields['first_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ваше имя'
        })
        self.fields['last_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ваша фамилия'
        })
        
        self.fields['age'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ваш возраст'
        })
        
        self.fields['grade'].widget.attrs.update({
            'class': 'form-control',
        })
        
        # Заполняем поля именем и фамилией из связанного User объекта
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
    
    def save(self, commit=True):
        student = super().save(commit=False)
        
        # Обновляем имя и фамилию в связанном User объекте
        if student.user:
            student.user.first_name = self.cleaned_data.get('first_name', '')
            student.user.last_name = self.cleaned_data.get('last_name', '')
            if commit:
                student.user.save()
        
        # Обновляем возраст
        student.age = self.cleaned_data.get('age')
        
        # Обновляем класс, если пользователь школьник
        if student.is_school_student:
            student.grade = self.cleaned_data.get('grade')
        
        if commit:
            student.save()
        return student


class StudentExcelUploadForm(forms.Form):
    file = forms.FileField(label='Загрузить Excel-файл', required=True)


class StudentMessageRequestForm(forms.ModelForm):
    class Meta:
        model = StudentMessageRequest
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Введите ваше сообщение...'}),
        }


class CourseFeedbackForm(forms.ModelForm):
    """Форма для ввода отзывов о курсе"""
    
    class Meta:
        model = CourseFeedback
        fields = ['rating', 'comment', 'what_liked', 'what_to_improve', 'would_recommend']
        widgets = {
            'rating': forms.RadioSelect(attrs={
                'class': 'feedback-rating',
                'required': True
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Поделитесь своими впечатлениями о курсе...',
                'maxlength': 1000
            }),
            'what_liked': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Что вам больше всего понравилось в курсе?',
                'maxlength': 500
            }),
            'what_to_improve': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Что можно было бы улучшить?',
                'maxlength': 500
            }),
            'would_recommend': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'rating': 'Оцените курс',
            'comment': 'Общий отзыв',
            'what_liked': 'Что понравилось',
            'what_to_improve': 'Что улучшить',
            'would_recommend': 'Рекомендую этот курс другим студентам'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rating'].required = True
        self.fields['comment'].required = True


class CourseAddRequestForm(forms.ModelForm):
    class Meta:
        model = CourseAddRequest
        fields = ['course_name', 'comment']
        widgets = {
            'course_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название курса, который хотите изучать'
            }),
            'comment': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Дополнительная информация (необязательно)'
            }),
        }


