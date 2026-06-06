"""
LSTM Predictor Module for Bereke AI
Анализ временных рядов и предсказание состояния пользователя.

Функции:
- Предсказание будущего состояния (стресс, усталость, тревога)
- Обнаружение аномалий в паттернах
- Анализ трендов
"""

import numpy as np
import torch
import torch.nn as nn
from collections import deque
from datetime import datetime
import json
import os


# 8 features: fatigue, stress, anxiety + 5 gambling
FEATURE_LABELS = ['fatigue', 'stress', 'anxiety',
                  'blink_rate', 'mouth_tension', 'head_velocity',
                  'eye_fixation', 'self_touching']
NUM_FEATURES = len(FEATURE_LABELS)  # 8


class LSTMModel(nn.Module):
    """LSTM нейронная сеть для анализа временных рядов."""
    
    def __init__(self, input_size=NUM_FEATURES, hidden_size=64, num_layers=2, output_size=NUM_FEATURES, dropout=0.2):
        """
        Args:
            input_size: Количество входных признаков (8: fatigue, stress, anxiety + 5 gambling)
            hidden_size: Размер скрытого слоя
            num_layers: Количество LSTM слоёв
            output_size: Количество выходных признаков (предсказание)
            dropout: Вероятность dropout для регуляризации
        """
        super(LSTMModel, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM слои
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # Полносвязные слои для предсказания
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, output_size),
            nn.Sigmoid()  # Выход от 0 до 1
        )
        
    def forward(self, x, hidden=None):
        """
        Прямой проход через сеть.
        
        Args:
            x: Входной тензор [batch, seq_len, input_size]
            hidden: Опциональное скрытое состояние
            
        Returns:
            output: Предсказание [batch, output_size]
            hidden: Обновлённое скрытое состояние
        """
        # LSTM
        lstm_out, hidden = self.lstm(x, hidden)
        
        # Берём последний выход последовательности
        last_output = lstm_out[:, -1, :]
        
        # Полносвязный слой
        output = self.fc(last_output)
        
        return output, hidden


class AnomalyDetector(nn.Module):
    """Автоэнкодер для обнаружения аномалий."""
    
    def __init__(self, input_size=NUM_FEATURES, hidden_size=32, latent_size=8):
        super(AnomalyDetector, self).__init__()
        
        # Энкодер
        self.encoder = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, latent_size),
            nn.ReLU()
        )
        
        # Декодер
        self.decoder = nn.Sequential(
            nn.Linear(latent_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, input_size),
            nn.Sigmoid()
        )
        
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded
    
    def get_reconstruction_error(self, x):
        """Возвращает ошибку реконструкции (мера аномальности)."""
        with torch.no_grad():
            reconstructed = self.forward(x)
            error = torch.mean((x - reconstructed) ** 2, dim=-1)
        if error.dim() == 0:
            return error.item()
        return error.squeeze().item()


class LSTMPredictor:
    """
    Основной класс для предсказания состояния и обнаружения аномалий.
    Интегрируется с системой мониторинга Bereke AI.
    """
    
    def __init__(self, sequence_length=10, model_path='models/lstm_model.pt'):
        """
        Args:
            sequence_length: Длина последовательности для анализа
            model_path: Путь к сохранённой модели
        """
        self.sequence_length = sequence_length
        self.model_path = model_path
        
        # Буфер данных для временного ряда
        self.data_buffer = deque(maxlen=sequence_length)
        
        # Инициализация моделей
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"🧠 LSTM использует: {self.device}")
        
        # LSTM модель для предсказания
        self.lstm_model = LSTMModel().to(self.device)
        
        # Автоэнкодер для обнаружения аномалий
        self.anomaly_detector = AnomalyDetector().to(self.device)
        
        # Порог аномалии (настраивается на основе данных)
        self.anomaly_threshold = 0.1
        
        # История предсказаний
        self.prediction_history = []
        
        # Статистика для нормализации
        self.running_mean = np.zeros(NUM_FEATURES)
        self.running_std = np.ones(NUM_FEATURES)
        self.sample_count = 0
        
        # Загрузка модели если существует
        self._load_model()
        
        # Режим обучения
        self.training_mode = True
        self.training_data = []
        
        print("✅ LSTM Predictor инициализирован")
        
    def _load_model(self):
        """Загрузка сохранённой модели."""
        if os.path.exists(self.model_path):
            try:
                checkpoint = torch.load(self.model_path, map_location=self.device)
                self.lstm_model.load_state_dict(checkpoint['lstm_model'])
                self.anomaly_detector.load_state_dict(checkpoint['anomaly_detector'])
                self.running_mean = checkpoint.get('running_mean', np.zeros(NUM_FEATURES))
                self.running_std = checkpoint.get('running_std', np.ones(NUM_FEATURES))
                # Handle old models with fewer features
                if len(self.running_mean) < NUM_FEATURES:
                    self.running_mean = np.zeros(NUM_FEATURES)
                    self.running_std = np.ones(NUM_FEATURES)
                    print(f"⚠️ Old model has fewer features, resetting statistics")
                self.anomaly_threshold = checkpoint.get('anomaly_threshold', 0.1)
                print(f"✅ Модель загружена из {self.model_path}")
            except Exception as e:
                print(f"⚠️ Не удалось загрузить модель: {e}")
                
    def save_model(self):
        """Сохранение модели."""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        checkpoint = {
            'lstm_model': self.lstm_model.state_dict(),
            'anomaly_detector': self.anomaly_detector.state_dict(),
            'running_mean': self.running_mean,
            'running_std': self.running_std,
            'anomaly_threshold': self.anomaly_threshold
        }
        torch.save(checkpoint, self.model_path)
        print(f"✅ Модель сохранена в {self.model_path}")
        
    def _update_statistics(self, features):
        """Обновление статистики для нормализации."""
        self.sample_count += 1
        delta = features - self.running_mean
        self.running_mean += delta / self.sample_count
        delta2 = features - self.running_mean
        self.running_std = np.sqrt(
            ((self.sample_count - 1) * self.running_std**2 + delta * delta2) / self.sample_count
        )
        # Избегаем деления на ноль
        self.running_std = np.maximum(self.running_std, 1e-6)
        
    def _normalize(self, features):
        """Нормализация признаков."""
        return (features - self.running_mean) / self.running_std
    
    def _denormalize(self, features):
        """Денормализация признаков."""
        return features * self.running_std + self.running_mean
        
    def add_data_point(self, fatigue_score, stress_score, anxiety_score,
                       blink_rate_score=0.0, mouth_tension=0.0, head_velocity=0.0,
                       eye_fixation=0.0, self_touching=0.0):
        """
        Добавление новой точки данных в буфер.
        
        Args:
            fatigue_score: Оценка усталости (0-1)
            stress_score: Оценка стресса (0-1)
            anxiety_score: Оценка тревоги (0-1)
            blink_rate_score: Скор моргания (0-1) — gambling
            mouth_tension: Напряжение рта (0-1) — gambling
            head_velocity: Скорость движения головы (0-1) — gambling
            eye_fixation: Фиксация взгляда (0-1) — gambling
            self_touching: Касание лица (0-1) — gambling
            
        Returns:
            dict: Результат анализа (или None если недостаточно данных)
        """
        features = np.array([fatigue_score, stress_score, anxiety_score,
                             blink_rate_score, mouth_tension, head_velocity,
                             eye_fixation, self_touching])
        
        # Обновляем статистику
        self._update_statistics(features)
        
        # Добавляем в буфер
        self.data_buffer.append(features)
        
        # Сохраняем для обучения
        if self.training_mode:
            self.training_data.append(features)
        
        # Если достаточно данных - делаем предсказание
        if len(self.data_buffer) >= self.sequence_length:
            return self._analyze()
        
        return {
            'status': 'collecting',
            'data_points': len(self.data_buffer),
            'required': self.sequence_length,
            'message': f'Сбор данных: {len(self.data_buffer)}/{self.sequence_length}'
        }
    
    def _analyze(self):
        """
        Выполнение анализа LSTM на собранных данных.
        
        Returns:
            dict: Результаты анализа
        """
        # Подготовка данных
        sequence = np.array(list(self.data_buffer))
        
        # Нормализация
        normalized_sequence = np.array([self._normalize(s) for s in sequence])
        
        # Конвертация в тензор
        x = torch.FloatTensor(normalized_sequence).unsqueeze(0).to(self.device)
        
        # Предсказание
        self.lstm_model.eval()
        with torch.no_grad():
            prediction, _ = self.lstm_model(x)
            prediction = prediction.cpu().numpy()[0]
        
        # Денормализация предсказания
        predicted_values = self._denormalize(prediction)
        predicted_values = np.clip(predicted_values, 0, 1)  # Ограничиваем 0-1
        
        # Обнаружение аномалий
        current_features = torch.FloatTensor(sequence[-1]).unsqueeze(0).to(self.device)
        self.anomaly_detector.eval()
        anomaly_score = self.anomaly_detector.get_reconstruction_error(current_features)
        is_anomaly = anomaly_score > self.anomaly_threshold
        
        # Анализ тренда
        trend = self._analyze_trend(sequence)
        
        # Формирование результата
        result = {
            'status': 'analyzed',
            'timestamp': datetime.now().isoformat(),
            
            # Текущие значения
            'current': {label: float(sequence[-1][i]) for i, label in enumerate(FEATURE_LABELS)},
            
            # Предсказание на следующий шаг
            'prediction': {label: float(predicted_values[i]) for i, label in enumerate(FEATURE_LABELS)},
            
            # Изменение (предсказание - текущее)
            'predicted_change': {label: float(predicted_values[i] - sequence[-1][i]) for i, label in enumerate(FEATURE_LABELS)},
            
            # Аномалии
            'anomaly': {
                'score': float(anomaly_score),
                'threshold': self.anomaly_threshold,
                'is_anomaly': bool(is_anomaly)
            },
            
            # Тренды
            'trend': trend,
            
            # Рекомендации на основе предсказания
            'lstm_recommendations': self._generate_predictions_recommendations(
                predicted_values, trend, is_anomaly
            )
        }
        
        # Сохраняем в историю
        self.prediction_history.append(result)
        
        return result
    
    def _analyze_trend(self, sequence):
        """
        Анализ тренда на основе последовательности.
        
        Returns:
            dict: Тренды для каждого показателя
        """
        if len(sequence) < 3:
            return {'overall': 'недостаточно данных'}
        
        trends = {}
        labels = FEATURE_LABELS
        
        for i, label in enumerate(labels):
            values = sequence[:, i]
            
            # Линейная регрессия для определения тренда
            x = np.arange(len(values))
            slope = np.polyfit(x, values, 1)[0]
            
            # Определяем направление тренда
            if slope > 0.02:
                trends[label] = 'растёт ↑'
            elif slope < -0.02:
                trends[label] = 'снижается ↓'
            else:
                trends[label] = 'стабильно →'
                
            # Добавляем числовое значение изменения
            trends[f'{label}_slope'] = float(slope)
        
        # Общий тренд
        avg_slope = np.mean([trends[f'{l}_slope'] for l in labels])
        if avg_slope > 0.02:
            trends['overall'] = 'ухудшение'
        elif avg_slope < -0.02:
            trends['overall'] = 'улучшение'
        else:
            trends['overall'] = 'стабильно'
            
        return trends
    
    def _generate_predictions_recommendations(self, prediction, trend, is_anomaly):
        """
        Генерация рекомендаций на основе предсказания LSTM.
        """
        recommendations = []
        
        # Аномалия
        if is_anomaly:
            recommendations.append("⚠️ Обнаружено необычное изменение показателей")
        
        fatigue = prediction[0]
        stress = prediction[1]
        anxiety = prediction[2]
        
        # Gambling-specific predictions (indices 3-7)
        gambling_features = prediction[3:8] if len(prediction) >= 8 else [0]*5
        gambling_avg = float(np.mean(gambling_features))
        
        # Предупреждения на основе предсказания
        if fatigue > 0.7:
            recommendations.append("🔮 Прогноз: высокая усталость. Рекомендуется отдых в ближайшее время")
        elif fatigue > 0.5 and trend.get('fatigue', '').startswith('растёт'):
            recommendations.append("📈 Усталость растёт. Запланируйте перерыв")
            
        if stress > 0.7:
            recommendations.append("🔮 Прогноз: повышенный стресс. Попробуйте дыхательные упражнения")
        elif stress > 0.5 and trend.get('stress', '').startswith('растёт'):
            recommendations.append("📈 Стресс растёт. Рекомендуется сделать паузу")
            
        if anxiety > 0.6:
            recommendations.append("🔮 Прогноз: повышенная тревожность. Попробуйте техники релаксации")
        
        # Gambling risk predictions
        if gambling_avg > 0.5:
            recommendations.append("🎰 Прогноз: растущий риск лудомании. Срочно рекомендуется перерыв!")
        elif gambling_avg > 0.3:
            recommendations.append("🎰 Прогноз: повышенные признаки игровой зависимости. Будьте осторожны.")
        
        if len(prediction) >= 8 and prediction[6] > 0.5:  # eye_fixation
            recommendations.append("👁 Прогноз: гиперфиксация взгляда усиливается. Отведите глаза от экрана.")
        
        # Положительные тренды
        if trend.get('overall') == 'улучшение':
            recommendations.append("✨ Ваше состояние улучшается! Продолжайте в том же духе")
        elif trend.get('overall') == 'стабильно':
            if max(prediction) < 0.3:
                recommendations.append("✅ Отличное состояние! Продолжайте поддерживать его")
        
        return recommendations if recommendations else ["✅ Прогноз стабильный, показатели в норме"]
    
    def train_online(self, epochs=5, learning_rate=0.001):
        """
        Онлайн-обучение модели на собранных данных.
        Вызывается периодически для адаптации к пользователю.
        """
        if len(self.training_data) < self.sequence_length + 1:
            print("⚠️ Недостаточно данных для обучения")
            return
        
        print(f"🔄 Обучение LSTM на {len(self.training_data)} точках данных...")
        
        # Подготовка данных
        data = np.array(self.training_data)
        X, y = [], []
        
        for i in range(len(data) - self.sequence_length):
            X.append(data[i:i + self.sequence_length])
            y.append(data[i + self.sequence_length])
        
        X = torch.FloatTensor(np.array(X)).to(self.device)
        y = torch.FloatTensor(np.array(y)).to(self.device)
        
        # Обучение LSTM
        self.lstm_model.train()
        optimizer = torch.optim.Adam(self.lstm_model.parameters(), lr=learning_rate)
        criterion = nn.MSELoss()
        
        for epoch in range(epochs):
            optimizer.zero_grad()
            predictions, _ = self.lstm_model(X)
            loss = criterion(predictions, y)
            loss.backward()
            optimizer.step()
            
            if (epoch + 1) % 10 == 0 or epoch == epochs - 1:
                print(f"  Epoch {epoch+1}/{epochs}, Loss: {loss.item():.6f}")
        
        # Обучение автоэнкодера для обнаружения аномалий
        self.anomaly_detector.train()
        ae_optimizer = torch.optim.Adam(self.anomaly_detector.parameters(), lr=learning_rate)
        
        ae_data = torch.FloatTensor(data).to(self.device)
        for epoch in range(epochs * 2):
            ae_optimizer.zero_grad()
            reconstructed = self.anomaly_detector(ae_data)
            ae_loss = criterion(reconstructed, ae_data)
            ae_loss.backward()
            ae_optimizer.step()
        
        # Обновляем порог аномалии
        with torch.no_grad():
            errors = []
            for point in ae_data:
                error = self.anomaly_detector.get_reconstruction_error(point.unsqueeze(0))
                errors.append(error)
            # Порог = среднее + 2 стандартных отклонения
            errors = np.array(errors)
            self.anomaly_threshold = float(np.mean(errors) + 2 * np.std(errors))
        
        print(f"✅ Обучение завершено. Новый порог аномалии: {self.anomaly_threshold:.4f}")
        
        # Сохраняем модель
        self.save_model()
    
    def get_statistics(self):
        """Получение статистики работы LSTM."""
        if not self.prediction_history:
            return {'status': 'no_data', 'message': 'Нет данных для статистики'}
        
        # Собираем предсказания
        predictions = []
        anomalies = 0
        
        for p in self.prediction_history:
            pred_vals = [p['prediction'].get(label, 0) for label in FEATURE_LABELS]
            predictions.append(pred_vals)
            if p['anomaly']['is_anomaly']:
                anomalies += 1
        
        predictions = np.array(predictions)
        
        avg_predictions = {}
        for i, label in enumerate(FEATURE_LABELS):
            if i < predictions.shape[1]:
                avg_predictions[label] = float(np.mean(predictions[:, i]))
            else:
                avg_predictions[label] = 0.0
        
        return {
            'status': 'ok',
            'total_predictions': len(self.prediction_history),
            'anomalies_detected': anomalies,
            'anomaly_rate': anomalies / len(self.prediction_history) if self.prediction_history else 0,
            'average_predictions': avg_predictions,
            'data_points_collected': len(self.training_data),
            'model_device': str(self.device)
        }


# ================== ТЕСТИРОВАНИЕ ==================
if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║              Bereke AI - LSTM Predictor Test               ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    # Создаём предиктор
    predictor = LSTMPredictor(sequence_length=5)
    
    # Симуляция данных
    print("\n📊 Симуляция потока данных...")
    
    np.random.seed(42)
    for i in range(20):
        # Генерируем реалистичные данные с трендом
        t = i / 20
        fatigue = 0.3 + 0.3 * t + np.random.normal(0, 0.05)
        stress = 0.4 + 0.2 * np.sin(t * 3) + np.random.normal(0, 0.05)
        anxiety = 0.35 + 0.1 * t + np.random.normal(0, 0.05)
        # Gambling features
        blink_rate = 0.1 + 0.2 * t + np.random.normal(0, 0.03)
        mouth_tension = 0.15 + 0.25 * t + np.random.normal(0, 0.04)
        head_velocity = 0.05 + 0.15 * np.sin(t * 2) + np.random.normal(0, 0.03)
        eye_fixation = 0.2 + 0.3 * t + np.random.normal(0, 0.05)
        self_touching = 0.05 + 0.1 * t + np.random.normal(0, 0.03)
        
        # Ограничиваем 0-1
        vals = [fatigue, stress, anxiety, blink_rate, mouth_tension,
                head_velocity, eye_fixation, self_touching]
        vals = [np.clip(v, 0, 1) for v in vals]
        
        result = predictor.add_data_point(*vals)
        
        if result['status'] == 'analyzed':
            print(f"\n📈 Шаг {i+1}:")
            print(f"   Текущее: F={result['current']['fatigue']:.2f}, S={result['current']['stress']:.2f}")
            print(f"   Прогноз: F={result['prediction']['fatigue']:.2f}, S={result['prediction']['stress']:.2f}")
            print(f"   Тренд: {result['trend']['overall']}")
            if result['anomaly']['is_anomaly']:
                print(f"   ⚠️ АНОМАЛИЯ: {result['anomaly']['score']:.4f}")
            for rec in result['lstm_recommendations'][:2]:
                print(f"   {rec}")
        else:
            print(f"   {result['message']}")
    
    # Обучение
    print("\n🔄 Запуск онлайн-обучения...")
    predictor.train_online(epochs=20)
    
    # Статистика
    print("\n📊 Статистика:")
    stats = predictor.get_statistics()
    print(f"   Всего предсказаний: {stats['total_predictions']}")
    print(f"   Обнаружено аномалий: {stats['anomalies_detected']}")
    print(f"   Средний прогноз стресса: {stats['average_predictions']['stress']:.2f}")
    print(f"   Средний прогноз тревоги: {stats['average_predictions']['anxiety']:.2f}")
    
    print("\n✅ Тест LSTM завершён!")
