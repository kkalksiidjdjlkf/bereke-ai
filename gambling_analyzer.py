"""
Gambling Addiction Analyzer (Лудомания)
Анализ поведенческих паттернов, связанных с игровой зависимостью.

5 ключевых параметров:
1. Blink Rate — частота моргания (транс / паника)
2. Mouth Tension — напряжение рта (ожидание результата)
3. Head Velocity — скорость движения головы (импульсивность / тильт)
4. Eye Fixation — фиксация взгляда в центре (потеря реальности)
5. Self-Touching — перекрытие лица руками (осознание проигрыша)
"""

import numpy as np
from collections import deque
import time


class GamblingAnalyzer:
    """Анализатор признаков игровой зависимости на основе лицевых ландмарков."""

    def __init__(self, fps=7.0):
        """
        Args:
            fps: Ожидаемая частота кадров входных данных
        """
        self.fps = fps

        # ===== Blink Rate =====
        # Хранение времён морганий для расчёта частоты
        self._blink_times = deque(maxlen=200)
        self._last_blink_count = 0
        self._blink_rate_per_min = 0.0  # нормальная: 15-20/мин

        # ===== Mouth Tension =====
        # Буфер расстояний между уголками губ (нормализованных)
        self._mouth_width_history = deque(maxlen=60)
        self._mouth_tension_score = 0.0  # 0-1

        # ===== Head Velocity =====
        # Позиции центра лица для расчёта скорости
        self._face_center_history = deque(maxlen=30)
        self._face_center_times = deque(maxlen=30)
        self._head_velocity = 0.0  # пикс/сек (нормализовано)
        self._head_velocity_score = 0.0  # 0-1

        # ===== Eye Fixation =====
        # Отслеживание направления взгляда (насколько взгляд зафиксирован в центре)
        self._gaze_positions = deque(maxlen=90)  # ~13 сек при 7fps
        self._eye_fixation_score = 0.0  # 0-1 (1 = полная фиксация)

        # ===== Self-Touching =====
        # Обнаружение руки на лице (через YOLO person + уменьшение видимой площади лица)
        self._face_area_history = deque(maxlen=30)
        self._self_touch_score = 0.0  # 0-1
        self._face_visibility_history = deque(maxlen=30)

        # ===== Общий скор зависимости =====
        self._addiction_risk_score = 0.0  # 0-1
        self._analysis_count = 0

        # ===== Зоны риска =====
        self._zone_history = deque(maxlen=300)  # ~42 сек истории

    def analyze(self, landmarks_68, face_bbox, frame_shape,
                blink_count=0, ear_value=0.3, yolo_persons=None):
        """
        Основной метод анализа кадра.

        Args:
            landmarks_68: numpy array (68, 2) — 68 лицевых ландмарков LBF
            face_bbox: (x, y, w, h) — bounding box лица
            frame_shape: (height, width) кадра
            blink_count: текущий счётчик морганий из _detect_blink_and_eyes
            ear_value: текущее значение EAR
            yolo_persons: список YOLO-детекций [{'bbox': [x1,y1,x2,y2], ...}]

        Returns:
            dict: результаты анализа
        """
        self._analysis_count += 1
        now = time.time()
        h_frame, w_frame = frame_shape[:2]

        if landmarks_68 is None or face_bbox is None:
            return self._build_result()

        pts = landmarks_68
        fx, fy, fw, fh = face_bbox

        # Нормализация по расстоянию между внешними углами глаз
        outer_eye_dist = np.linalg.norm(pts[36] - pts[45])
        if outer_eye_dist < 1e-6:
            outer_eye_dist = 1.0
        D = outer_eye_dist

        # ===== 1. BLINK RATE =====
        self._update_blink_rate(blink_count, now)

        # ===== 2. MOUTH TENSION =====
        self._update_mouth_tension(pts, D)

        # ===== 3. HEAD VELOCITY =====
        face_cx = fx + fw / 2.0
        face_cy = fy + fh / 2.0
        self._update_head_velocity(face_cx, face_cy, w_frame, now)

        # ===== 4. EYE FIXATION =====
        self._update_eye_fixation(pts, w_frame, h_frame)

        # ===== 5. SELF-TOUCHING =====
        self._update_self_touching(face_bbox, yolo_persons, w_frame, h_frame)

        # ===== ОБЩИЙ РИСК =====
        self._calculate_addiction_risk()

        return self._build_result()

    # ----------------------------------------------------------------
    # 1. BLINK RATE
    # ----------------------------------------------------------------
    def _update_blink_rate(self, current_blink_count, now):
        """
        Blink Rate: частота моргания.
        - Низкая (<10/мин): транс, гиперфокус на экране → признак зависимости
        - Нормальная (15-20/мин): ОК
        - Высокая (>25/мин): паника, усталость, тильт
        """
        # Детектим новые моргания
        new_blinks = current_blink_count - self._last_blink_count
        if new_blinks > 0:
            for _ in range(new_blinks):
                self._blink_times.append(now)
        self._last_blink_count = current_blink_count

        # Считаем частоту за последние 60 секунд
        window = 60.0  # секунд
        recent = [t for t in self._blink_times if now - t < window]
        if len(recent) >= 2:
            elapsed = now - recent[0]
            if elapsed > 3.0:  # минимум 3 секунды для стабильности
                self._blink_rate_per_min = len(recent) / elapsed * 60.0
            else:
                self._blink_rate_per_min = 0.0
        elif self._analysis_count > 20 and len(recent) <= 1:
            # Прошло достаточно кадров но морганий почти нет → возможно транс
            self._blink_rate_per_min = max(0.5, len(recent) * 2.0)
        else:
            self._blink_rate_per_min = 0.0

    def get_blink_rate_score(self):
        """
        Blink Rate Score: 0-1 (1 = тревожно).
        Низкий (<10) = транс (плохо). Нормальный (15-20) = ОК. Высокий (>25) = паника (плохо).
        """
        rate = self._blink_rate_per_min
        if rate < 0.1 and self._analysis_count < 15:
            return 0.0  # недостаточно данных на старте
        if rate < 0.1 and self._analysis_count >= 15:
            # Долго нет морганий → вероятный транс
            return 0.6
        if rate < 10:
            # Низкий — транс/гиперфокус
            return min(1.0, (10 - rate) / 10.0 * 0.8 + 0.1)
        elif rate <= 22:
            # Нормальная зона
            return 0.0
        else:
            # Высокий — паника/усталость
            return min(1.0, (rate - 22) / 20.0)

    # ----------------------------------------------------------------
    # 2. MOUTH TENSION
    # ----------------------------------------------------------------
    def _update_mouth_tension(self, pts, D):
        """
        Mouth Tension: напряжение рта.
        Расстояние между уголками губ (pts[48] и pts[54]) нормализовано на D.
        При напряжении губы сжимаются → mouth_width уменьшается.
        Также: вертикальное сжатие губ (pts[51]-pts[57]).
        """
        mouth_w = np.linalg.norm(pts[48] - pts[54]) / D
        mouth_h = np.linalg.norm(pts[51] - pts[57]) / D

        # Tension = узкий + сжатый рот (не улыбка)
        # Нормальный рот: ~0.60-0.70 ширина, ~0.10-0.15 высота
        # Напряжённый: ширина < 0.62, высота < 0.09
        width_tension = max(0.0, (0.65 - mouth_w) / 0.18)  # 0 при 0.65, 1 при 0.47
        height_tension = max(0.0, (0.10 - mouth_h) / 0.07)  # сжатые губы

        tension = min(1.0, (width_tension * 0.6 + height_tension * 0.4))
        self._mouth_width_history.append(tension)

        # Усреднение по окну
        if len(self._mouth_width_history) >= 3:
            self._mouth_tension_score = float(np.mean(list(self._mouth_width_history)[-15:]))
        else:
            self._mouth_tension_score = tension

    # ----------------------------------------------------------------
    # 3. HEAD VELOCITY
    # ----------------------------------------------------------------
    def _update_head_velocity(self, cx, cy, frame_width, now):
        """
        Head Velocity: скорость движения головы.
        Резкие движения = импульсивность, тильт.
        Нормализовано по ширине кадра.
        """
        self._face_center_history.append((cx, cy))
        self._face_center_times.append(now)

        if len(self._face_center_history) >= 3:
            positions = list(self._face_center_history)
            times = list(self._face_center_times)

            # Мгновенная скорость (последние 3 кадра)
            velocities = []
            for i in range(1, min(len(positions), 5)):
                dx = positions[-1][0] - positions[-i-1][0]
                dy = positions[-1][1] - positions[-i-1][1]
                dt = times[-1] - times[-i-1]
                if dt > 0.01:
                    speed = np.sqrt(dx**2 + dy**2) / dt / frame_width  # нормализовано
                    velocities.append(speed)

            if velocities:
                self._head_velocity = float(np.max(velocities))
            else:
                self._head_velocity = 0.0

        # Скор: плавная шкала
        # Нормальное движение: <0.03/сек (нормализовано)
        # Импульсивное: >0.2/сек
        v = self._head_velocity
        if v < 0.03:
            self._head_velocity_score = 0.0
        elif v < 0.2:
            self._head_velocity_score = (v - 0.03) / 0.17 * 0.5
        else:
            self._head_velocity_score = min(1.0, 0.5 + (v - 0.2) / 0.3 * 0.5)

    # ----------------------------------------------------------------
    # 4. EYE FIXATION
    # ----------------------------------------------------------------
    def _update_eye_fixation(self, pts, w_frame, h_frame):
        """
        Eye Fixation: насколько взгляд зафиксирован в одной точке.
        Используем среднюю позицию зрачков (iris landmarks приблизительно).
        Для 68 LBF ландмарков — центр глаз как приближение.
        Высокая фиксация = потеря реальности (гиперфокус на экране).
        """
        # Центр правого глаза: среднее pts[36:42]
        right_eye_center = np.mean(pts[36:42], axis=0)
        # Центр левого глаза: среднее pts[42:48]
        left_eye_center = np.mean(pts[42:48], axis=0)
        # Средний взгляд
        gaze_center = (right_eye_center + left_eye_center) / 2.0

        # Нормализуем по размеру кадра
        gaze_norm = (gaze_center[0] / w_frame, gaze_center[1] / h_frame)
        self._gaze_positions.append(gaze_norm)

        if len(self._gaze_positions) >= 7:
            positions = np.array(list(self._gaze_positions))
            # Стандартное отклонение позиций взгляда
            std_x = np.std(positions[:, 0])
            std_y = np.std(positions[:, 1])
            gaze_spread = np.sqrt(std_x**2 + std_y**2)

            # Чем меньше разброс — тем выше фиксация
            # LBF ландмарки дают джиттер ~0.01-0.03, учитываем это
            # Нормальный разброс: >0.07 (глаза активно двигаются)
            # Фиксация: <0.04 (взгляд практически неподвижен)
            if gaze_spread < 0.015:
                self._eye_fixation_score = 1.0
            elif gaze_spread < 0.06:
                self._eye_fixation_score = max(0.0, (0.06 - gaze_spread) / 0.045)
            else:
                self._eye_fixation_score = 0.0
        else:
            self._eye_fixation_score = 0.0

    # ----------------------------------------------------------------
    # 5. SELF-TOUCHING
    # ----------------------------------------------------------------
    def _update_self_touching(self, face_bbox, yolo_persons, w_frame, h_frame):
        """
        Self-Touching: перекрытие лица руками.
        Определяем через:
        - Резкое уменьшение видимой площади лица (рука закрывает часть)
        - Появление YOLO-рук/объектов поверх лица

        Основной метод: если площадь лица резко уменьшается или
        ландмарки теряют стабильность — вероятно рука перед лицом.
        """
        fx, fy, fw, fh = face_bbox
        face_area = fw * fh
        frame_area = w_frame * h_frame

        # Нормализованная площадь лица
        face_area_norm = face_area / max(frame_area, 1)
        self._face_area_history.append(face_area_norm)

        if len(self._face_area_history) >= 5:
            areas = list(self._face_area_history)
            # Базовая площадь (медиана за историю)
            baseline = np.median(areas)
            current = areas[-1]

            if baseline > 0.005:
                # Резкое уменьшение площади = что-то перекрывает лицо
                drop_ratio = 1.0 - (current / baseline)
                if drop_ratio > 0.08:
                    # Площадь упала на >8% — вероятно рука на лице
                    self._self_touch_score = min(1.0, drop_ratio / 0.3)
                else:
                    # Плавное затухание
                    self._self_touch_score = max(0.0, self._self_touch_score * 0.9)
            else:
                self._self_touch_score = 0.0

            # Дополнительно: резкие колебания площади (рука двигается)
            if len(areas) >= 7:
                recent_std = np.std(areas[-7:])
                if recent_std > baseline * 0.05:
                    self._self_touch_score = min(1.0,
                        self._self_touch_score + recent_std / baseline * 0.5)
        else:
            self._self_touch_score = 0.0

    # ----------------------------------------------------------------
    # ОБЩИЙ РИСК ЗАВИСИМОСТИ
    # ----------------------------------------------------------------
    def _calculate_addiction_risk(self):
        """
        Объединяем 5 параметров в общий скор риска зависимости.
        Веса подобраны по значимости для лудомании.
        """
        blink_score = self.get_blink_rate_score()

        weights = {
            'blink_rate': 0.15,       # Транс / паника
            'mouth_tension': 0.20,    # Напряжение — ожидание результата
            'head_velocity': 0.20,    # Импульсивность / тильт
            'eye_fixation': 0.25,     # Потеря реальности — самый важный
            'self_touching': 0.20,    # Осознание проигрыша
        }

        risk = (
            blink_score * weights['blink_rate'] +
            self._mouth_tension_score * weights['mouth_tension'] +
            self._head_velocity_score * weights['head_velocity'] +
            self._eye_fixation_score * weights['eye_fixation'] +
            self._self_touch_score * weights['self_touching']
        )

        self._addiction_risk_score = min(1.0, max(0.0, risk))
        self._zone_history.append(self._addiction_risk_score)

    def get_risk_zone(self):
        """
        Определяет зону риска.

        Returns:
            str: 'normal', 'attention', 'warning', 'danger'
        """
        score = self._addiction_risk_score
        if score < 0.2:
            return 'normal'
        elif score < 0.45:
            return 'attention'
        elif score < 0.7:
            return 'warning'
        else:
            return 'danger'

    def get_recommendation(self):
        """Рекомендация на основе текущего состояния."""
        zone = self.get_risk_zone()
        blink = self.get_blink_rate_score()

        if zone == 'normal':
            return '✅ Состояние в норме'
        elif zone == 'attention':
            if self._eye_fixation_score > 0.4:
                return '👁 Вы долго смотрите в одну точку. Отведите взгляд.'
            if self._mouth_tension_score > 0.4:
                return '😬 Напряжение рта. Расслабьте челюсть, сделайте вдох.'
            return '⚠️ Обратите внимание на своё состояние.'
        elif zone == 'warning':
            if self._head_velocity_score > 0.4:
                return '🔄 Импульсивные движения. Рекомендуем паузу!'
            if blink > 0.5:
                return '👀 Моргание нарушено. Вы в трансе или перевозбуждены.'
            return '⚠️ Повышенный риск. Сделайте перерыв.'
        else:
            if self._self_touch_score > 0.4:
                return '🛑 Вы закрываете лицо. Остановитесь и отдохните!'
            return '🛑 ВЫСОКИЙ РИСК! Немедленно сделайте перерыв!'

    def _build_result(self):
        """Формирует словарь результатов."""
        blink_score = self.get_blink_rate_score()
        zone = self.get_risk_zone()

        return {
            'gambling_risk': round(self._addiction_risk_score, 3),
            'risk_zone': zone,
            'recommendation': self.get_recommendation(),

            # 5 параметров
            'blink_rate': {
                'blinks_per_min': round(self._blink_rate_per_min, 1),
                'score': round(blink_score, 3),
                'status': 'транс' if self._blink_rate_per_min < 10 and blink_score > 0.3
                         else 'паника' if self._blink_rate_per_min > 25
                         else 'норма'
            },
            'mouth_tension': {
                'score': round(self._mouth_tension_score, 3),
                'status': 'напряжение' if self._mouth_tension_score > 0.4
                         else 'норма'
            },
            'head_velocity': {
                'velocity': round(self._head_velocity, 4),
                'score': round(self._head_velocity_score, 3),
                'status': 'импульсивность' if self._head_velocity_score > 0.4
                         else 'норма'
            },
            'eye_fixation': {
                'score': round(self._eye_fixation_score, 3),
                'status': 'гиперфокус' if self._eye_fixation_score > 0.5
                         else 'фиксация' if self._eye_fixation_score > 0.25
                         else 'норма'
            },
            'self_touching': {
                'score': round(self._self_touch_score, 3),
                'status': 'обнаружено' if self._self_touch_score > 0.3
                         else 'нет'
            },

            'analysis_count': self._analysis_count,
        }

    def get_summary(self):
        """Итоговая сводка за сессию."""
        if len(self._zone_history) == 0:
            return {'status': 'no_data'}

        history = list(self._zone_history)
        return {
            'total_analyses': self._analysis_count,
            'average_risk': round(float(np.mean(history)), 3),
            'max_risk': round(float(np.max(history)), 3),
            'time_in_danger': round(sum(1 for x in history if x >= 0.7) / len(history) * 100, 1),
            'time_in_warning': round(sum(1 for x in history if 0.45 <= x < 0.7) / len(history) * 100, 1),
            'time_normal': round(sum(1 for x in history if x < 0.2) / len(history) * 100, 1),
        }
