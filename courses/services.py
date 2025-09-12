import os
from django.conf import settings
from PIL import Image
from django.db.models import Count, Sum
from .models import Achievement, Student, StudentAchievement, QuizAttempt, CourseResult, Notification, Level
import fitz  # PyMuPDF for PDF processing
from pptx import Presentation

# Ensure MEDIA_ROOT/slides exists
SLIDES_ROOT = os.path.join(settings.MEDIA_ROOT, 'slides')
os.makedirs(SLIDES_ROOT, exist_ok=True)

def convert_pdf_to_images(pdf_path, lesson_id):
    """
    Converts each page of a PDF into an image and saves it.
    Requires PyMuPDF (fitz) and Pillow.
    """
    images_paths = []
    try:
        doc = fitz.open(pdf_path)
        output_dir = os.path.join(SLIDES_ROOT, str(lesson_id))
        os.makedirs(output_dir, exist_ok=True)

        for i, page in enumerate(doc):
            pix = page.get_pixmap()
            img_path = os.path.join(output_dir, f'page_{i+1}.png')
            pix.save(img_path)
            images_paths.append(img_path)
        doc.close()
    except Exception as e:
        print(f"Error converting PDF {pdf_path}: {e}")
        # Log the error, maybe send a notification to admin
    return images_paths

def convert_pptx_to_images(pptx_path, lesson_id):
    """
    Converts each slide of a PPTX into an image and saves it.
    Requires python-pptx and Pillow.
    """
    images_paths = []
    try:
        prs = Presentation(pptx_path)
        output_dir = os.path.join(SLIDES_ROOT, str(lesson_id))
        os.makedirs(output_dir, exist_ok=True)

        for i, slide in enumerate(prs.slides):
            # python-pptx does not directly render slides to images.
            # This is a placeholder. A more robust solution would involve
            # using an external tool like LibreOffice/PowerPoint automation
            # or a cloud service.
            # For simplicity, we'll just create a dummy image for now or skip.
            # This part needs significant external tool integration.
            # For this example, we'll assume a dummy image or error.
            print(f"Warning: Direct PPTX to image conversion not fully supported without external tools. Skipping slide {i+1} of {pptx_path}")
            # As a workaround for demonstration, let's create a blank image if no external tool is set up.
            dummy_img = Image.new('RGB', (1024, 768), color = (255, 255, 255))
            img_path = os.path.join(output_dir, f'slide_{i+1}.png')
            dummy_img.save(img_path)
            images_paths.append(img_path)
            
    except Exception as e:
        print(f"Error converting PPTX {pptx_path}: {e}")
    return images_paths

def handle_lesson_file_conversion(lesson_instance):
    """
    Handles the conversion of PDF/PPTX files associated with a lesson
    into a series of images if convert_pdf_to_slides is True.
    """
    if lesson_instance.convert_pdf_to_slides and lesson_instance.pdf:
        file_extension = os.path.splitext(lesson_instance.pdf.path)[1].lower()
        if file_extension == '.pdf':
            print(f"Converting PDF: {lesson_instance.pdf.path}")
            return convert_pdf_to_images(lesson_instance.pdf.path, lesson_instance.id)
        elif file_extension in ['.pptx', '.ppt']:
            print(f"Converting PPTX: {lesson_instance.pdf.path}")
            return convert_pptx_to_images(lesson_instance.pdf.path, lesson_instance.id)
    return [] 


def _get_student_achievement_metrics(student: Student) -> dict:
    """Возвращает ключевые метрики для расчёта достижений."""
    try:
        total_passed_quizzes = QuizAttempt.objects.filter(student=student, passed=True).count()
        total_perfect_quizzes = QuizAttempt.objects.filter(student=student, score=100).count()
        total_completed_courses = CourseResult.objects.filter(user=student.user, stars_given=True).count()
        total_stars = student.stars
        current_level = student.calculate_level()

        return {
            'passed_quizzes': total_passed_quizzes,
            'perfect_quizzes': total_perfect_quizzes,
            'completed_courses': total_completed_courses,
            'total_stars': total_stars,
            'level_reached': current_level,
        }
    except Exception as e:
        print(f"Ошибка при расчёте метрик достижений для студента {student.username}: {e}")
        return {
            'passed_quizzes': 0,
            'perfect_quizzes': 0,
            'completed_courses': 0,
            'total_stars': 0,
            'level_reached': 1,
        }


def get_achievement_progress(student: Student, achievement: Achievement) -> dict:
    """Возвращает прогресс по конкретному достижению."""
    try:
        metrics = _get_student_achievement_metrics(student)
        current_value = metrics.get(achievement.condition_type, 0)
        target = achievement.condition_value or 1
        percentage = int(min(100, (current_value / target) * 100)) if target > 0 else 100
        return {
            'current': current_value,
            'target': target,
            'percentage': percentage,
        }
    except Exception as e:
        print(f"Ошибка при расчёте прогресса достижения {achievement.title}: {e}")
        return {
            'current': 0,
            'target': achievement.condition_value or 1,
            'percentage': 0,
        }


def evaluate_and_unlock_achievements(student: Student):
    """Пересчитывает прогресс и открывает доступные достижения.
    Вызывает уведомления для новых достижений.
    """
    if not isinstance(student, Student):
        return []

    try:
        newly_unlocked = []
        metrics = _get_student_achievement_metrics(student)

        for ach in Achievement.objects.filter(is_active=True):
            try:
                value = metrics.get(ach.condition_type, 0)
                if value >= ach.condition_value:
                    sa, created = StudentAchievement.objects.get_or_create(student=student, achievement=ach)
                    if created:
                        newly_unlocked.append(ach)
                        # Уведомление
                        try:
                            Notification.objects.create(
                                student=student,
                                type='achievement_unlocked',
                                message=f'{ach.reward_icon} Достижение открыто: "{ach.title}" — награда: {ach.reward}',
                                priority=2,
                                extra_data={'achievement_code': ach.code}
                            )
                        except Exception as e:
                            print(f"Ошибка при создании уведомления о достижении {ach.title}: {e}")
            except Exception as e:
                print(f"Ошибка при проверке достижения {ach.title}: {e}")
                continue
                
        return newly_unlocked
    except Exception as e:
        print(f"Ошибка при пересчёте достижений для студента {student.username}: {e}")
        return []