from django.core.management.base import BaseCommand
from courses.models import Achievement


class Command(BaseCommand):
    help = 'Создаёт стартовый набор достижений (около 32 штук)'

    def handle(self, *args, **options):
        achievements = []
        # По квизам
        achievements += [
            ('quiz_10', 'Первый марафон квизов', 'Выполните 10 квизов и получите фирменные наклейки', 'passed_quizzes', 10, 'Фирменные наклейки', '⭐'),
            ('quiz_20', 'Уверенный игрок', 'Выполните 20 квизов — набор стикеров + значок', 'passed_quizzes', 20, 'Набор стикеров + значок', '⭐'),
            ('quiz_30', 'Настоящий боец', 'Выполните 30 квизов — брендовая тетрадь', 'passed_quizzes', 30, 'Тетрадь Study Task', '⭐'),
            ('quiz_50', 'Полсотни!', 'Выполните 50 квизов — бутылка для воды', 'passed_quizzes', 50, 'Бутылка для воды Study Task', '⭐'),
            ('quiz_75', 'Почти сотня', 'Выполните 75 квизов — рюкзак для сменки', 'passed_quizzes', 75, 'Рюкзак для сменки', '⭐'),
            ('quiz_100', 'Сотня!', 'Выполните 100 квизов — фирменная толстовка', 'passed_quizzes', 100, 'Толстовка Study Task', '⭐'),
        ]
        # Идеальные квизы
        achievements += [
            ('perfect_5', 'Точность 100%', 'Сдайте 5 квизов на 100% — значок «Суперточность»', 'perfect_quizzes', 5, 'Значок «Суперточность»', '🎯'),
            ('perfect_10', 'Снайпер', 'Сдайте 10 квизов на 100% — фирменная кружка', 'perfect_quizzes', 10, 'Кружка Study Task', '🎯'),
            ('perfect_20', 'Легенда тестов', 'Сдайте 20 квизов на 100% — наушники', 'perfect_quizzes', 20, 'Наушники', '🎯'),
        ]
        # Завершённые курсы
        achievements += [
            ('courses_5', 'Первые 5 курсов', 'Пройдите 5 курсов и получите футболку', 'completed_courses', 5, 'Футболка Study Task', '👕'),
            ('courses_10', 'Десятка!', 'Пройдите 10 курсов — спортивная сумка', 'completed_courses', 10, 'Спортивная сумка', '🎒'),
            ('courses_15', 'Пятнашка', 'Пройдите 15 курсов — смарт‑браслет', 'completed_courses', 15, 'Смарт‑браслет', '⌚'),
            ('courses_20', 'Двадцатка', 'Пройдите 20 курсов — планшет', 'completed_courses', 20, 'Планшет', '📱'),
        ]
        # Звёзды
        achievements += [
            ('stars_100', '100 звёзд', 'Накопите 100 звёзд — набор стикеров', 'total_stars', 100, 'Набор стикеров', '🌟'),
            ('stars_250', '250 звёзд', 'Накопите 250 звёзд — брендовая кепка', 'total_stars', 250, 'Кепка Study Task', '🧢'),
            ('stars_500', '500 звёзд', 'Накопите 500 звёзд — футболка', 'total_stars', 500, 'Футболка Study Task', '👕'),
            ('stars_1000', '1000 звёзд', 'Накопите 1000 звёзд — худи', 'total_stars', 1000, 'Худи Study Task', '🧥'),
            ('stars_2000', '2000 звёзд', 'Накопите 2000 звёзд — рюкзак', 'total_stars', 2000, 'Рюкзак Study Task', '🎒'),
        ]
        # Уровни
        achievements += [
            ('level_2', 'Уровень 2', 'Достигните уровня 2 — наклейки', 'level_reached', 2, 'Наклейки Study Task', '🏅'),
            ('level_3', 'Уровень 3', 'Достигните уровня 3 — значок', 'level_reached', 3, 'Значок Study Task', '🏅'),
            ('level_4', 'Уровень 4', 'Достигните уровня 4 — бутылка', 'level_reached', 4, 'Бутылка Study Task', '🏅'),
            ('level_5', 'Уровень 5', 'Достигните уровня 5 — футболка', 'level_reached', 5, 'Футболка Study Task', '🏅'),
        ]
        # Дополнительно, смешанные цели, чтобы довести до ~32
        achievements += [
            ('streak_quiz_7', 'Серия 7 дней', 'Проходите квизы 7 дней подряд — блокнот', 'passed_quizzes', 25, 'Блокнот Study Task', '📓'),
            ('streak_quiz_14', 'Серия 14 дней', 'Проходите квизы 14 дней подряд — термокружка', 'passed_quizzes', 40, 'Термокружка', '🥤'),
            ('mix_start', 'Стартовый сет', '10 квизов и 1 курс — набор наклеек', 'passed_quizzes', 10, 'Набор наклеек', '🎒'),
            ('mix_mid', 'Уверенный старт', '30 квизов и 3 курса — кепка', 'passed_quizzes', 30, 'Кепка Study Task', '🧢'),
            ('mix_pro', 'Путь чемпиона', '75 квизов и 10 курсов — худи', 'passed_quizzes', 75, 'Худи Study Task', '🧥'),
            ('mix_legend', 'Легенда Study Task', '100 квизов и 20 курсов — планшет', 'passed_quizzes', 100, 'Планшет', '📱'),
            ('perfect_master', 'Мастер точности', '20 идеальных квизов — наушники', 'perfect_quizzes', 20, 'Наушники', '🎧'),
            ('courses_pro', 'Учебный профи', '15 курсов — смарт‑браслет', 'completed_courses', 15, 'Смарт‑браслет', '⌚'),
        ]

        created = 0
        for code, title, description, ctype, cvalue, reward, icon in achievements:
            _, is_created = Achievement.objects.get_or_create(
                code=code,
                defaults={
                    'title': title,
                    'description': description,
                    'condition_type': ctype,
                    'condition_value': cvalue,
                    'reward': reward,
                    'reward_icon': icon,
                    'is_active': True,
                }
            )
            if is_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Создано достижений: {created}. Всего: {Achievement.objects.count()}'))


