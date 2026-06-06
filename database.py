"""
Database Module for Wellbeing Monitoring System
SQLite storage for sessions, face analysis, voice analysis, wellbeing data.
All methods use context manager (with sqlite3.connect) for thread safety.
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List


class WellbeingDatabase:
    def __init__(self, db_path: str = "wellbeing_monitor.db"):
        self.db_path = db_path
        self._init_database()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                duration_seconds REAL,
                user_notes TEXT,
                environment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS face_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                fatigue_score REAL,
                eye_closure_ratio REAL,
                blink_rate REAL,
                blink_consistency REAL,
                eye_openness REAL,
                mouth_openness REAL,
                face_detected BOOLEAN,
                primary_indicator TEXT,
                gambling_risk_score REAL DEFAULT 0.0,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )''')
            # Ensure gambling_risk_score column exists in older DBs
            try:
                c.execute('ALTER TABLE face_analysis ADD COLUMN gambling_risk_score REAL DEFAULT 0.0')
            except Exception:
                pass  # column already exists
            c.execute('''CREATE TABLE IF NOT EXISTS voice_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                stress_score REAL,
                anxiety_score REAL,
                pitch_hz REAL,
                pitch_variation REAL,
                speech_rate_wpm REAL,
                loudness_rms REAL,
                loudness_status TEXT,
                voice_quality TEXT,
                primary_indicator TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS breathing_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                breathing_rate REAL,
                breathing_status TEXT,
                breathing_irregularity REAL,
                energy_level REAL,
                rhythm_consistency REAL,
                primary_indicator TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS wellbeing_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                overall_concern_score REAL,
                primary_concern TEXT,
                secondary_concern TEXT,
                fatigue_score REAL,
                stress_score REAL,
                anxiety_score REAL,
                breathing_score REAL,
                recommendations TEXT,
                concern_level TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                wellbeing_analysis_id INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                recommendation_text TEXT,
                recommendation_type TEXT,
                priority TEXT,
                category TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id),
                FOREIGN KEY (wellbeing_analysis_id) REFERENCES wellbeing_analysis(id)
            )''')

            # ===================== HEALTH SYMPTOMS (from DOC.FAI.ME) =====================
            c.execute('''CREATE TABLE IF NOT EXISTS health_conditions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name_kz TEXT NOT NULL,
                name_ru TEXT NOT NULL,
                name_en TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                severity_level TEXT DEFAULT 'info',
                camera_detectable BOOLEAN DEFAULT 0,
                recommendation_kz TEXT,
                recommendation_ru TEXT,
                emergency BOOLEAN DEFAULT 0
            )''')

            c.execute('''CREATE TABLE IF NOT EXISTS health_symptom_detection (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                person_id INTEGER DEFAULT 1,
                timestamp TIMESTAMP NOT NULL,
                condition_code TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                detected BOOLEAN DEFAULT 0,
                raw_value REAL,
                threshold_value REAL,
                face_region TEXT,
                notes TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )''')

            c.execute('''CREATE TABLE IF NOT EXISTS vital_signs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                person_id INTEGER DEFAULT 1,
                timestamp TIMESTAMP NOT NULL,
                estimated_heart_rate REAL,
                heart_rate_confidence REAL,
                estimated_spo2 REAL,
                spo2_confidence REAL,
                estimated_resp_rate REAL,
                resp_rate_confidence REAL,
                skin_temperature_zone TEXT,
                pallor_score REAL DEFAULT 0.0,
                jaundice_score REAL DEFAULT 0.0,
                cyanosis_score REAL DEFAULT 0.0,
                redness_score REAL DEFAULT 0.0,
                dryness_score REAL DEFAULT 0.0,
                rash_score REAL DEFAULT 0.0,
                overall_skin_health TEXT DEFAULT 'normal',
                alert_level TEXT DEFAULT 'none',
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )''')

            # ===================== KNOWN FACES (face recognition) =====================
            c.execute('''CREATE TABLE IF NOT EXISTS known_faces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                embedding TEXT NOT NULL,
                thumbnail TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')

            # Migration: add thumbnail column if missing (for existing DBs)
            try:
                c.execute("SELECT thumbnail FROM known_faces LIMIT 1")
            except sqlite3.OperationalError:
                c.execute("ALTER TABLE known_faces ADD COLUMN thumbnail TEXT")

            conn.commit()
            self._seed_health_conditions(conn)
        print(f"✅ Database initialized: {self.db_path}")

    # ===================== SEED HEALTH CONDITIONS =====================
    def _seed_health_conditions(self, conn):
        """Populate health_conditions reference table from DOC.FAI.ME data."""
        conditions = [
            # === SKIN CONDITIONS (camera detectable) ===
            ('PALLOR', 'Бозару', 'Бледность', 'Pallor',
             'skin', 'Анемия немесе қан жоғалуына тән белгі. Беттің, қолдың бозаруы.',
             'warning', 1,
             'Дәрігерге барыңыз, қан анализін тапсырыңыз',
             'Обратитесь к врачу, сдайте анализ крови', 0),

            ('JAUNDICE', 'Сарғаю', 'Желтуха', 'Jaundice',
             'skin', 'Билирубиннің көтерілуі — бауыр/өт жолдары ауруы белгісі. Склера да сары.',
             'warning', 1,
             'Жедел дәрігерге барыңыз — бауыр функциясын тексеріңіз',
             'Срочно обратитесь к врачу — проверьте функцию печени', 0),

            ('CYANOSIS', 'Көгеру', 'Цианоз', 'Cyanosis',
             'skin', 'Оттегі жетіспеушілігі — еріндер, тырнақтар көгереді.',
             'critical', 1,
             'Жедел жәрдем! SpO2 тексеріңіз',
             'Экстренная помощь! Проверьте SpO2', 1),

            ('FACIAL_REDNESS', 'Қызару', 'Покраснение лица', 'Facial Redness',
             'skin', 'Қызба (температура көтерілуі) немесе аллергиялық реакция белгісі.',
             'info', 1,
             'Температураңызды өлшеңіз',
             'Измерьте температуру', 0),

            ('SKIN_RASH', 'Бөртпе', 'Кожная сыпь', 'Skin Rash',
             'skin', 'Жұқпалы аурулар немесе аллергиялық реакция белгісі.',
             'warning', 1,
             'Дәрігерге қаралыңыз',
             'Обратитесь к дерматологу', 0),

            ('SKIN_DRYNESS', 'Құрғақтық', 'Сухость кожи', 'Skin Dryness',
             'skin', 'Дегидратация, қант диабеті немесе тері ауруы белгісі.',
             'info', 1,
             'Су ішіңіз, тері күтімін жақсартыңыз',
             'Пейте воду, улучшите уход за кожей', 0),

            # === PULSE CONDITIONS ===
            ('BRADYCARDIA', 'Брадикардия', 'Брадикардия', 'Bradycardia',
             'pulse', 'Пульс <60 соққы/мин. Жоғары физикалық дайындық немесе патология.',
             'warning', 1,
             'Пульсіңізді қадағалаңыз, дәрігерге хабарласыңыз',
             'Наблюдайте за пульсом, обратитесь к врачу', 0),

            ('TACHYCARDIA', 'Тахикардия', 'Тахикардия', 'Tachycardia',
             'pulse', 'Пульс >100 соққы/мин тыныш күйде. Қызба, стресс, жүрек ауруы.',
             'warning', 1,
             'Тыныштаныңыз, дәрігерге хабарласыңыз',
             'Успокойтесь, обратитесь к врачу', 0),

            ('CRITICAL_PULSE_LOW', 'Қауіпті баяу пульс', 'Критически низкий пульс',
             'Critical Low Pulse',
             'pulse', 'Пульс <40 — жедел көмек қажет.',
             'critical', 1,
             'ЖЕДЕЛ ЖӘРДЕМ шақырыңыз!',
             'Вызовите СКОРУЮ ПОМОЩЬ!', 1),

            ('CRITICAL_PULSE_HIGH', 'Қауіпті жоғары пульс', 'Критически высокий пульс',
             'Critical High Pulse',
             'pulse', 'Пульс >130 тыныш күйде — жедел көмек қажет.',
             'critical', 1,
             'ЖЕДЕЛ ЖӘРДЕМ шақырыңыз!',
             'Вызовите СКОРУЮ ПОМОЩЬ!', 1),

            # === SpO2 CONDITIONS ===
            ('SPO2_LOW', 'SpO2 төмендеу', 'SpO2 снижение', 'Low SpO2',
             'spo2', 'SpO2 93-94% — бақылау қажет.',
             'warning', 0,
             'Тыныс алуыңызды тексеріңіз',
             'Проверьте дыхание', 0),

            ('SPO2_CRITICAL', 'SpO2 қауіпті', 'SpO2 критический', 'Critical SpO2',
             'spo2', 'SpO2 <90% — гипоксемия, оттеги қажет.',
             'critical', 0,
             'ЖЕДЕЛ ЖӘРДЕМ! Оттеги қажет!',
             'СКОРАЯ ПОМОЩЬ! Нужен кислород!', 1),

            # === TEMPERATURE CONDITIONS ===
            ('SUBFEBRIL', 'Субфебрилді', 'Субфебрильная', 'Subfebril Fever',
             'temperature', 'Температура 37.1-38.0°C — жеңіл инфекция.',
             'info', 1,
             'Температураны бақылаңыз, сұйықтық ішіңіз',
             'Наблюдайте за температурой, пейте жидкость', 0),

            ('MODERATE_FEVER', 'Орташа қызба', 'Умеренная лихорадка', 'Moderate Fever',
             'temperature', 'Температура 38.1-39.0°C — инфекциялық процесс.',
             'warning', 1,
             'Дәрігерге хабарласыңыз, жылуды түсіретін дәрі ішіңіз',
             'Обратитесь к врачу, примите жаропонижающее', 0),

            ('HIGH_FEVER', 'Жоғары қызба', 'Высокая лихорадка', 'High Fever',
             'temperature', 'Температура 39.1-40.0°C — асқыну қаупі.',
             'critical', 1,
             'ДӘРІГЕРГЕ ЖЕДЕЛ БАРЫҢЫЗ!',
             'СРОЧНО обратитесь к врачу!', 0),

            ('CRITICAL_FEVER', 'Қауіпті қызба', 'Критическая лихорадка', 'Critical Fever',
             'temperature', 'Температура >40.0°C — жедел жәрдем қажет.',
             'critical', 0,
             'ЖЕДЕЛ ЖӘРДЕМ шақырыңыз!',
             'Вызовите СКОРУЮ ПОМОЩЬ!', 1),

            ('HYPOTHERMIA', 'Гипотермия', 'Гипотермия', 'Hypothermia',
             'temperature', 'Температура <35.0°C — жылу реттеу бұзылған.',
             'critical', 0,
             'ЖЕДЕЛ ЖӘРДЕМ! Жылытуды бастаңыз!',
             'СКОРАЯ ПОМОЩЬ! Начните согревание!', 1),

            # === VOICE CONDITIONS ===
            ('VOICE_HOARSENESS', 'Дауыс қарлығуы', 'Охриплость голоса', 'Voice Hoarseness',
             'voice', 'Дауыс байламдарының бұзылуы — ларингит, полиптер, нейропарез.',
             'info', 0,
             '2 аптадан артық болса — дәрігерге барыңыз',
             'Если более 2 недель — обратитесь к врачу', 0),

            ('VOICE_LOSS', 'Дауыс жоғалуы', 'Потеря голоса', 'Voice Loss',
             'voice', 'Толық дауыс жоғалуы — шұғыл тексеру қажет.',
             'warning', 0,
             'Дәрігерге хабарласыңыз',
             'Обратитесь к врачу', 0),

            # === RESPIRATORY CONDITIONS ===
            ('FAST_BREATHING', 'Жылдам тыныс алу', 'Учащённое дыхание', 'Fast Breathing',
             'breathing', 'Тыныс алу >25 рет/мин — стресс немесе аурухана.',
             'warning', 1,
             '4-4-4 тыныс алу техникасын қолданыңыз',
             'Используйте технику дыхания 4-4-4', 0),

            ('IRREGULAR_BREATHING', 'Тұрақсыз тыныс', 'Нерегулярное дыхание',
             'Irregular Breathing',
             'breathing', 'Тыныс алу ырғағы тұрақсыз.',
             'info', 1,
             'Тыныс алуды нормализациялаңыз',
             'Нормализуйте дыхание', 0),
        ]

        c = conn.cursor()
        for cond in conditions:
            try:
                c.execute('''INSERT OR IGNORE INTO health_conditions
                    (code, name_kz, name_ru, name_en, category, description,
                     severity_level, camera_detectable, recommendation_kz,
                     recommendation_ru, emergency)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', cond)
            except Exception:
                pass
        conn.commit()

    # ===================== STORE HEALTH DATA =====================
    def store_vital_signs(self, session_id: int, data: Dict, person_id: int = 1):
        """Store vital signs analysis (skin color, estimated HR, etc.)."""
        with self._get_conn() as conn:
            c = conn.cursor()
            now = datetime.now().isoformat()
            c.execute('''INSERT INTO vital_signs
                (session_id, person_id, timestamp, estimated_heart_rate, heart_rate_confidence,
                 estimated_spo2, spo2_confidence, estimated_resp_rate, resp_rate_confidence,
                 skin_temperature_zone, pallor_score, jaundice_score, cyanosis_score,
                 redness_score, dryness_score, rash_score, overall_skin_health, alert_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (session_id, person_id, now,
                 data.get('estimated_heart_rate'),
                 data.get('heart_rate_confidence', 0.0),
                 data.get('estimated_spo2'),
                 data.get('spo2_confidence', 0.0),
                 data.get('estimated_resp_rate'),
                 data.get('resp_rate_confidence', 0.0),
                 data.get('skin_temperature_zone', 'unknown'),
                 data.get('pallor_score', 0.0),
                 data.get('jaundice_score', 0.0),
                 data.get('cyanosis_score', 0.0),
                 data.get('redness_score', 0.0),
                 data.get('dryness_score', 0.0),
                 data.get('rash_score', 0.0),
                 data.get('overall_skin_health', 'normal'),
                 data.get('alert_level', 'none')))
            conn.commit()

    def store_symptom_detection(self, session_id: int, data: Dict, person_id: int = 1):
        """Store a detected health symptom."""
        with self._get_conn() as conn:
            c = conn.cursor()
            now = datetime.now().isoformat()
            c.execute('''INSERT INTO health_symptom_detection
                (session_id, person_id, timestamp, condition_code, confidence, detected,
                 raw_value, threshold_value, face_region, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (session_id, person_id, now,
                 data.get('condition_code', 'UNKNOWN'),
                 data.get('confidence', 0.0),
                 data.get('detected', False),
                 data.get('raw_value'),
                 data.get('threshold_value'),
                 data.get('face_region', 'face'),
                 data.get('notes', '')))
            conn.commit()

    def get_health_conditions(self) -> List[Dict]:
        """Get all reference health conditions."""
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM health_conditions ORDER BY category, severity_level')
            return [dict(r) for r in c.fetchall()]

    def get_session_vital_signs(self, session_id: int, person_id: int = None) -> List[Dict]:
        """Get vital signs for a session, optionally filtered by person_id."""
        with self._get_conn() as conn:
            c = conn.cursor()
            if person_id is not None:
                c.execute('SELECT * FROM vital_signs WHERE session_id = ? AND person_id = ? ORDER BY timestamp',
                          (session_id, person_id))
            else:
                c.execute('SELECT * FROM vital_signs WHERE session_id = ? ORDER BY timestamp',
                          (session_id,))
            return [dict(r) for r in c.fetchall()]

    def get_session_symptoms(self, session_id: int, person_id: int = None) -> List[Dict]:
        """Get detected symptoms for a session, optionally filtered by person_id."""
        with self._get_conn() as conn:
            c = conn.cursor()
            person_filter = 'AND sd.person_id = ?' if person_id is not None else ''
            params = (session_id, person_id) if person_id is not None else (session_id,)
            c.execute(f'''SELECT sd.*, hc.name_ru, hc.name_kz, hc.name_en,
                         hc.category, hc.severity_level, hc.recommendation_ru,
                         hc.recommendation_kz, hc.emergency
                         FROM health_symptom_detection sd
                         LEFT JOIN health_conditions hc ON sd.condition_code = hc.code
                         WHERE sd.session_id = ? AND sd.detected = 1 {person_filter}
                         ORDER BY sd.timestamp DESC''',
                      params)
            return [dict(r) for r in c.fetchall()]

    def get_latest_vital_signs(self, session_id: int, person_id: int = None) -> Dict:
        """Get the most recent vital signs for a session."""
        with self._get_conn() as conn:
            c = conn.cursor()
            if person_id is not None:
                c.execute('''SELECT * FROM vital_signs WHERE session_id = ? AND person_id = ?
                             ORDER BY timestamp DESC LIMIT 1''', (session_id, person_id))
            else:
                c.execute('''SELECT * FROM vital_signs WHERE session_id = ?
                             ORDER BY timestamp DESC LIMIT 1''', (session_id,))
            row = c.fetchone()
            return dict(row) if row else {}

    def get_session_person_ids(self, session_id: int) -> List[int]:
        """Get all unique person IDs that have health data in a session."""
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute('SELECT DISTINCT person_id FROM vital_signs WHERE session_id = ? ORDER BY person_id',
                      (session_id,))
            return [r['person_id'] for r in c.fetchall()]

    def get_all_persons_health(self, session_id: int) -> Dict:
        """Get health data grouped by person_id for a session."""
        person_ids = self.get_session_person_ids(session_id)
        if not person_ids:
            return {'persons': [], 'person_count': 0}
        persons = []
        for pid in person_ids:
            latest = self.get_latest_vital_signs(session_id, pid)
            symptoms = self.get_session_symptoms(session_id, pid)
            vitals_history = self.get_session_vital_signs(session_id, pid)
            persons.append({
                'person_id': pid,
                'latest_vital_signs': latest,
                'symptoms': symptoms,
                'vital_signs_history': vitals_history,
            })
        return {'persons': persons, 'person_count': len(persons)}

    # ===================== SESSION =====================
    def create_session(self, user_notes: str = "", environment: str = "local") -> int:
        with self._get_conn() as conn:
            c = conn.cursor()
            now = datetime.now().isoformat()
            c.execute('INSERT INTO sessions (start_time, user_notes, environment) VALUES (?, ?, ?)',
                      (now, user_notes, environment))
            conn.commit()
            sid = c.lastrowid
            print(f"📝 Session {sid} created at {now}")
            return sid

    def end_session(self, session_id: int):
        with self._get_conn() as conn:
            c = conn.cursor()
            now = datetime.now().isoformat()
            c.execute('SELECT start_time FROM sessions WHERE id = ?', (session_id,))
            row = c.fetchone()
            if row:
                start = datetime.fromisoformat(row['start_time'])
                dur = (datetime.fromisoformat(now) - start).total_seconds()
                c.execute('UPDATE sessions SET end_time = ?, duration_seconds = ? WHERE id = ?',
                          (now, dur, session_id))
                conn.commit()
                print(f"✅ Session {session_id} ended. Duration: {dur:.1f}s")

    # ===================== STORE ANALYSIS =====================
    def store_face_analysis(self, session_id: int, data: Dict):
        with self._get_conn() as conn:
            c = conn.cursor()
            now = datetime.now().isoformat()
            c.execute('''INSERT INTO face_analysis
                (session_id, timestamp, fatigue_score, eye_closure_ratio,
                 blink_rate, blink_consistency, eye_openness, mouth_openness,
                 face_detected, primary_indicator, gambling_risk_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (session_id, now,
                 data.get('fatigue_score', 0.0),
                 data.get('eye_closure_ratio', 0.0),
                 data.get('blink_rate', 0.0),
                 data.get('blink_consistency', 0.0),
                 data.get('eye_openness', 0.0),
                 data.get('mouth_openness', 0.0),
                 data.get('face_detected', False),
                 data.get('primary_indicator', 'normal'),
                 data.get('gambling_risk_score', 0.0)))
            conn.commit()

    def store_voice_analysis(self, session_id: int, data: Dict):
        with self._get_conn() as conn:
            c = conn.cursor()
            now = datetime.now().isoformat()
            c.execute('''INSERT INTO voice_analysis
                (session_id, timestamp, stress_score, anxiety_score,
                 pitch_hz, pitch_variation, speech_rate_wpm, loudness_rms,
                 loudness_status, voice_quality, primary_indicator)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (session_id, now,
                 data.get('stress_score', 0.0),
                 data.get('anxiety_score', 0.0),
                 data.get('pitch_hz', 0.0),
                 data.get('pitch_variation', 0.0),
                 data.get('speech_rate_wpm', 0.0),
                 data.get('loudness_rms', 0.0),
                 data.get('loudness_status', 'normal'),
                 data.get('voice_quality', 'good'),
                 data.get('primary_indicator', 'normal')))
            conn.commit()

    def store_breathing_analysis(self, session_id: int, data: Dict):
        with self._get_conn() as conn:
            c = conn.cursor()
            now = datetime.now().isoformat()
            c.execute('''INSERT INTO breathing_analysis
                (session_id, timestamp, breathing_rate, breathing_status,
                 breathing_irregularity, energy_level, rhythm_consistency, primary_indicator)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (session_id, now,
                 data.get('breathing_rate', 0.0),
                 data.get('breathing_status', 'normal'),
                 data.get('breathing_irregularity', 0.0),
                 data.get('energy_level', 0.0),
                 data.get('rhythm_consistency', 0.0),
                 data.get('primary_indicator', 'normal')))
            conn.commit()

    def store_wellbeing_analysis(self, session_id: int, data: Dict) -> int:
        with self._get_conn() as conn:
            c = conn.cursor()
            now = datetime.now().isoformat()
            c.execute('''INSERT INTO wellbeing_analysis
                (session_id, timestamp, overall_concern_score, primary_concern,
                 secondary_concern, fatigue_score, stress_score, anxiety_score,
                 breathing_score, recommendations, concern_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (session_id, now,
                 data.get('overall_concern_score', 0.0),
                 data.get('primary_concern', 'unknown'),
                 data.get('secondary_concern', 'none'),
                 data.get('fatigue_score', 0.0),
                 data.get('stress_score', 0.0),
                 data.get('anxiety_score', 0.0),
                 data.get('breathing_score', 0.0),
                 json.dumps(data.get('recommendations', [])),
                 data.get('concern_level', 'low')))
            conn.commit()
            wid = c.lastrowid
            for rec in data.get('recommendations', []):
                c.execute('''INSERT INTO recommendations
                    (session_id, wellbeing_analysis_id, timestamp,
                     recommendation_text, recommendation_type, priority, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (session_id, wid, now,
                     rec.get('text', ''),
                     rec.get('type', 'general'),
                     rec.get('priority', 'medium'),
                     rec.get('category', 'wellbeing')))
            conn.commit()
            return wid

    # ===================== QUERIES =====================
    def get_session_summary(self, session_id: int) -> Dict:
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM sessions WHERE id = ?', (session_id,))
            row = c.fetchone()
            if not row:
                return {'session': {}, 'face_analysis': [], 'voice_analysis': [],
                        'breathing_analysis': [], 'wellbeing_analysis': [], 'recommendations': []}
            session = dict(row)
            c.execute('SELECT * FROM face_analysis WHERE session_id = ? ORDER BY timestamp', (session_id,))
            face = [dict(r) for r in c.fetchall()]
            c.execute('SELECT * FROM voice_analysis WHERE session_id = ? ORDER BY timestamp', (session_id,))
            voice = [dict(r) for r in c.fetchall()]
            c.execute('SELECT * FROM breathing_analysis WHERE session_id = ? ORDER BY timestamp', (session_id,))
            breath = [dict(r) for r in c.fetchall()]
            c.execute('SELECT * FROM wellbeing_analysis WHERE session_id = ? ORDER BY timestamp', (session_id,))
            well = [dict(r) for r in c.fetchall()]
            c.execute('SELECT * FROM recommendations WHERE session_id = ? ORDER BY timestamp', (session_id,))
            recs = [dict(r) for r in c.fetchall()]
            return {
                'session': session,
                'face_analysis': face,
                'voice_analysis': voice,
                'breathing_analysis': breath,
                'wellbeing_analysis': well,
                'recommendations': recs,
            }

    def get_session_statistics(self, session_id: int) -> Dict:
        with self._get_conn() as conn:
            c = conn.cursor()
            stats = {}
            c.execute('''SELECT AVG(fatigue_score) as avg_fatigue,
                                MAX(fatigue_score) as max_fatigue,
                                MAX(blink_rate) as avg_blink_rate,
                                AVG(eye_openness) as avg_eye_openness,
                                COUNT(*) as count,
                                AVG(gambling_risk_score) as avg_gambling_risk,
                                MAX(gambling_risk_score) as max_gambling_risk
                         FROM face_analysis WHERE session_id = ?''', (session_id,))
            stats['face'] = dict(c.fetchone())
            c.execute('''SELECT AVG(stress_score) as avg_stress,
                                MAX(stress_score) as max_stress,
                                AVG(anxiety_score) as avg_anxiety,
                                AVG(pitch_hz) as avg_pitch,
                                AVG(speech_rate_wpm) as avg_speech_rate,
                                AVG(loudness_rms) as avg_loudness,
                                COUNT(*) as count
                         FROM voice_analysis WHERE session_id = ?''', (session_id,))
            stats['voice'] = dict(c.fetchone())
            c.execute('''SELECT AVG(breathing_rate) as avg_breathing_rate,
                                MAX(breathing_rate) as max_breathing_rate,
                                AVG(breathing_irregularity) as avg_irregularity
                         FROM breathing_analysis WHERE session_id = ?''', (session_id,))
            stats['breathing'] = dict(c.fetchone())
            c.execute('''SELECT AVG(overall_concern_score) as avg_concern,
                                MAX(overall_concern_score) as max_concern,
                                COUNT(*) as analysis_count
                         FROM wellbeing_analysis WHERE session_id = ?''', (session_id,))
            stats['wellbeing'] = dict(c.fetchone())
            return stats

    def get_aggregated_metrics(self, limit: int = 10) -> Dict:
        """Get aggregated metrics from last N sessions for Metrics page."""
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute('SELECT id FROM sessions ORDER BY start_time DESC LIMIT ?', (limit,))
            sids = [r['id'] for r in c.fetchall()]
            if not sids:
                return {'face': {}, 'voice': {}, 'face_eye_values': [], 'voice_stress_values': [], 'sessions_count': 0}
            ph = ','.join('?' * len(sids))
            c.execute(f'''SELECT COUNT(*) as total,
                SUM(CASE WHEN face_detected = 1 THEN 1 ELSE 0 END) as detected,
                SUM(CASE WHEN primary_indicator = 'Happy' THEN 1 ELSE 0 END) as happy,
                SUM(CASE WHEN primary_indicator = 'Neutral' THEN 1 ELSE 0 END) as neutral,
                SUM(CASE WHEN primary_indicator = 'Sad' THEN 1 ELSE 0 END) as sad,
                SUM(CASE WHEN primary_indicator = 'Angry' THEN 1 ELSE 0 END) as angry,
                SUM(CASE WHEN primary_indicator = 'Surprise' THEN 1 ELSE 0 END) as surprise,
                SUM(CASE WHEN primary_indicator = 'Disgust' THEN 1 ELSE 0 END) as disgust,
                SUM(CASE WHEN primary_indicator = 'Fear' THEN 1 ELSE 0 END) as fear,
                SUM(CASE WHEN primary_indicator = 'Contempt' THEN 1 ELSE 0 END) as contempt,
                SUM(CASE WHEN primary_indicator NOT IN ('Happy','Neutral','Sad','Angry','Surprise','Disgust','Fear','Contempt') THEN 1 ELSE 0 END) as other_em,
                AVG(eye_openness) as avg_eye_openness,
                AVG(fatigue_score) as avg_fatigue
                FROM face_analysis WHERE session_id IN ({ph})''', sids)
            face = dict(c.fetchone())
            c.execute(f'SELECT eye_openness FROM face_analysis WHERE session_id IN ({ph}) AND face_detected = 1', sids)
            eye_vals = [r['eye_openness'] for r in c.fetchall() if r['eye_openness'] is not None]
            c.execute(f'''SELECT COUNT(*) as total,
                AVG(stress_score) as avg_stress,
                AVG(loudness_rms) as avg_loudness,
                MAX(stress_score) as max_stress
                FROM voice_analysis WHERE session_id IN ({ph})''', sids)
            voice = dict(c.fetchone())
            c.execute(f'SELECT stress_score FROM voice_analysis WHERE session_id IN ({ph})', sids)
            stress_vals = [r['stress_score'] for r in c.fetchall() if r['stress_score'] is not None]
            return {
                'face': face, 'face_eye_values': eye_vals,
                'voice': voice, 'voice_stress_values': stress_vals,
                'sessions_count': len(sids),
            }

    def get_user_history(self, limit: int = 10) -> List[Dict]:
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute('''SELECT id, start_time, end_time, duration_seconds, user_notes, environment
                         FROM sessions ORDER BY start_time DESC LIMIT ?''', (limit,))
            return [dict(r) for r in c.fetchall()]

    def get_session_quick_stats(self, session_id: int) -> Dict:
        """Quick stats for session list card."""
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute('''SELECT AVG(fatigue_score) as avg_fatigue,
                                MAX(blink_rate) as total_blinks,
                                AVG(eye_openness) as avg_eye_openness,
                                COUNT(*) as face_count,
                                SUM(CASE WHEN face_detected = 1 THEN 1 ELSE 0 END) as face_detected_count,
                                AVG(gambling_risk_score) as avg_gambling_risk,
                                MAX(gambling_risk_score) as max_gambling_risk
                         FROM face_analysis WHERE session_id = ?''', (session_id,))
            face = dict(c.fetchone())
            c.execute('''SELECT AVG(stress_score) as avg_stress,
                                AVG(loudness_rms) as avg_loudness,
                                COUNT(*) as voice_count
                         FROM voice_analysis WHERE session_id = ?''', (session_id,))
            voice = dict(c.fetchone())
            # Dominant emotion
            c.execute('''SELECT primary_indicator, COUNT(*) as cnt
                         FROM face_analysis WHERE session_id = ? AND face_detected = 1
                         GROUP BY primary_indicator ORDER BY cnt DESC LIMIT 1''', (session_id,))
            dom_row = c.fetchone()
            dominant_emotion = dict(dom_row)['primary_indicator'] if dom_row else None
            return {
                'avg_fatigue': face.get('avg_fatigue'),
                'total_blinks': face.get('total_blinks'),
                'avg_eye_openness': face.get('avg_eye_openness'),
                'face_count': face.get('face_count', 0),
                'face_detected_count': face.get('face_detected_count', 0),
                'avg_stress': voice.get('avg_stress'),
                'avg_loudness': voice.get('avg_loudness'),
                'voice_count': voice.get('voice_count', 0),
                'dominant_emotion': dominant_emotion,
                'avg_gambling_risk': face.get('avg_gambling_risk'),
                'max_gambling_risk': face.get('max_gambling_risk'),
            }


    # ===================== KNOWN FACES CRUD =====================
    def add_known_face(self, name: str, embedding: list, thumbnail: str = "") -> int:
        """Store a known face with its embedding vector.
        Args:
            name: Person's name
            embedding: Face embedding vector (list of floats)
            thumbnail: Base64-encoded face thumbnail image
        Returns: ID of the new record
        """
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute('INSERT INTO known_faces (name, embedding, thumbnail) VALUES (?, ?, ?)',
                      (name, json.dumps(embedding), thumbnail))
            conn.commit()
            fid = c.lastrowid
            print(f"✅ Known face added: {name} (id={fid})")
            return fid

    def get_known_faces(self) -> List[Dict]:
        """Get all known faces."""
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute('SELECT id, name, embedding, thumbnail, created_at FROM known_faces ORDER BY created_at DESC')
            results = []
            for r in c.fetchall():
                d = dict(r)
                d['embedding'] = json.loads(d['embedding'])
                results.append(d)
            return results

    def delete_known_face(self, face_id: int) -> bool:
        """Delete a known face by ID."""
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute('DELETE FROM known_faces WHERE id = ?', (face_id,))
            conn.commit()
            deleted = c.rowcount > 0
            if deleted:
                print(f"🗑️ Known face deleted: id={face_id}")
            return deleted

    def update_known_face(self, face_id: int, name: str = None, embedding: list = None, thumbnail: str = None) -> bool:
        """Update a known face."""
        with self._get_conn() as conn:
            c = conn.cursor()
            updates = []
            params = []
            if name is not None:
                updates.append('name = ?')
                params.append(name)
            if embedding is not None:
                updates.append('embedding = ?')
                params.append(json.dumps(embedding))
            if thumbnail is not None:
                updates.append('thumbnail = ?')
                params.append(thumbnail)
            if not updates:
                return False
            params.append(face_id)
            c.execute(f'UPDATE known_faces SET {", ".join(updates)} WHERE id = ?', params)
            conn.commit()
            return c.rowcount > 0


if __name__ == "__main__":
    db = WellbeingDatabase()
    sid = db.create_session(user_notes="Test session", environment="office")
    db.store_face_analysis(sid, {'fatigue_score': 0.3, 'face_detected': True, 'primary_indicator': 'Neutral'})
    db.store_voice_analysis(sid, {'stress_score': 0.2, 'primary_indicator': 'Neutral'})
    db.end_session(sid)
    print("Summary:", db.get_session_summary(sid))
    print("Stats:", db.get_session_statistics(sid))
    print("History:", db.get_user_history())
