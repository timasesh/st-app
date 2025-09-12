from django.core.management.base import BaseCommand
from courses.models import Level


class Command(BaseCommand):
    help = 'Создает начальные уровни для студентов'

    def handle(self, *args, **options):
        levels_data = [
            {'number': 1, 'name': 'Новичок Study Task', 'min_stars': 0, 'max_stars': 100, 'image': 'levels/Новичок.png', 'description': 'Добро пожаловать в Study Task! Начинайте свой путь к знаниям.'},
            {'number': 2, 'name': 'Активный ученик', 'min_stars': 100, 'max_stars': 200, 'image': 'levels/Активный_ученик.png', 'description': 'Вы активно участвуете в обучении и показываете интерес к знаниям.'},
            {'number': 3, 'name': 'Любознательный ум', 'min_stars': 200, 'max_stars': 300, 'image': 'levels/Любознательный_ум.png', 'description': 'Ваша любознательность помогает глубже понимать материал.'},
            {'number': 4, 'name': 'Целеустремлённый студент', 'min_stars': 300, 'max_stars': 400, 'image': 'levels/Целеустремлённый_студент.png', 'description': 'Вы ставите цели и последовательно их достигаете.'},
            {'number': 5, 'name': 'Исследователь знаний', 'min_stars': 400, 'max_stars': 500, 'image': 'levels/Исследователь_знаний.png', 'description': 'Вы исследуете темы глубоко и всесторонне.'},
            {'number': 6, 'name': 'Осознанный участник', 'min_stars': 500, 'max_stars': 600, 'image': 'levels/Осознанный_участник.png', 'description': 'Осознанный подход к обучению приносит отличные результаты.'},
            {'number': 7, 'name': 'Покоритель тем', 'min_stars': 600, 'max_stars': 700, 'image': 'levels/Покоритель_тем.png', 'description': 'Вы успешно покоряете даже самые сложные темы.'},
            {'number': 8, 'name': 'Уверенный практик', 'min_stars': 700, 'max_stars': 800, 'image': 'levels/Уверенный_практик.png', 'description': 'Уверенно применяете знания на практике.'},
            {'number': 9, 'name': 'Ученик с прокачкой', 'min_stars': 800, 'max_stars': 900, 'image': 'levels/Ученик_с_прокачкой.png', 'description': 'Ваши навыки значительно прокачались!'},
            {'number': 10, 'name': 'Гид по теме', 'min_stars': 900, 'max_stars': 1000, 'image': 'levels/Гид_по_теме.png', 'description': 'Вы можете быть гидом для других в изучаемых темах.'},
        ]

        created_count = 0
        updated_count = 0

        for level_data in levels_data:
            level, created = Level.objects.get_or_create(
                number=level_data['number'],
                defaults={
                    'name': level_data['name'],
                    'min_stars': level_data['min_stars'],
                    'max_stars': level_data['max_stars'],
                    'description': level_data.get('description', ''),
                    'image': level_data.get('image', ''),
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Создан уровень: {level}')
                )
            else:
                # Обновляем существующий уровень
                level.name = level_data['name']
                level.min_stars = level_data['min_stars']
                level.max_stars = level_data['max_stars']
                level.description = level_data.get('description', '')
                if level_data.get('image'):
                    level.image = level_data['image']
                level.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Обновлен уровень: {level}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Завершено! Создано: {created_count}, обновлено: {updated_count} уровней.'
            )
        ) 