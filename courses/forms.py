# courses/forms.py
# courses/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Lesson, Module, Course, Student
from .models import Question, Answer
from django.db import transaction


class StudentRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

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
        if commit:
            user.save()
            with transaction.atomic():
                Student.objects.create(user=user)  # Создаем объект Student при регистрации пользователя
        return user


class LessonCreationForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'video', 'pdf']


class ModuleCreationForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title', 'lessons']
        widgets = {
            'lessons': forms.CheckboxSelectMultiple
        }


class CourseCreationForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'modules', 'image']  # Добавили поле image
        widgets = {
            'modules': forms.CheckboxSelectMultiple
        }


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
        fields = ['title']


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


