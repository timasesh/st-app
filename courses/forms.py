# courses/forms.py
# courses/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Lesson, Module, Course, Student
from .models import Question, Answer
from django.db import transaction
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import re
from .models import StudentMessageRequest


class StudentRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(required=False, label='Имя')
    last_name = forms.CharField(required=False, label='Фамилия')

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Отключаем встроенные подсказки
        self.fields['username'].help_text = ''
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''

    def clean_password2(self):
        # Отключаем стандартные проверки
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.is_student = True
        if commit:
            user.save()
            with transaction.atomic():
                student = Student.objects.create(user=user)
                student.email = user.email
                student.first_name = user.first_name
                student.last_name = user.last_name
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

        if not video and not video_url:
            raise ValidationError('Необходимо указать либо видеофайл, либо URL видео')
        if video and video_url:
            raise ValidationError('Нельзя указать одновременно видеофайл и URL видео')

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
        fields = ['title', 'description', 'modules', 'image']
        widgets = {
            'modules': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Описание — textarea с placeholder
        self.fields['description'].widget = forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Краткое описание курса'})
        # Модули — чекбоксы с прокруткой
        self.fields['modules'].widget.attrs.update({'style': 'max-height:180px;overflow-y:auto;background:#f8f9fa;border-radius:10px;padding:0.7rem 1rem;margin-bottom:1.2rem;'})
        # Картинка — стилизованный input
        self.fields['image'].widget.attrs.update({'class': 'form-control', 'accept': 'image/*'})
        self.fields['title'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Название курса'})


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
    course = forms.ModelChoiceField(queryset=Course.objects.all(), required=True)
    module = forms.ModelChoiceField(queryset=Module.objects.all(), required=True)
    quiz = forms.ModelChoiceField(queryset=Quiz.objects.all(), required=True)


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['avatar', 'phone_number', 'email']
        widgets = {
            'department': forms.NumberInput(attrs={'min': 1, 'max': 12}),
        }


class StudentExcelUploadForm(forms.Form):
    file = forms.FileField(label='Загрузить Excel-файл', required=True)


class StudentMessageRequestForm(forms.ModelForm):
    class Meta:
        model = StudentMessageRequest
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Введите ваше сообщение...'}),
        }


