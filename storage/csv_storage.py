import csv
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class CSVStorage:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        self.players_file = os.path.join(data_dir, "players.csv")
        self.sessions_file = os.path.join(data_dir, "sessions.csv")
        self.rooms_file = os.path.join(data_dir, "rooms.csv")

        self._init_files()

    def _init_files(self):
        """Создает CSV файлы с заголовками если они не существуют"""

        # Игроки
        if not os.path.exists(self.players_file):
            with open(self.players_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'user_id', 'username', 'first_name', 'last_name',
                    'total_games', 'total_steps', 'total_rooms',
                    'dragons_found', 'gold_collected',
                    'first_seen', 'last_seen'
                ])

        # Сессии
        if not os.path.exists(self.sessions_file):
            with open(self.sessions_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'session_id', 'user_id', 'start_time', 'end_time',
                    'duration_seconds', 'steps', 'rooms_visited',
                    'dragon_found', 'gold_earned', 'died', 'reason'
                ])

        # Комнаты
        if not os.path.exists(self.rooms_file):
            with open(self.rooms_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'room_id', 'user_id', 'session_id', 'pos_x', 'pos_y',
                    'width', 'height', 'explored', 'has_monster',
                    'has_chest', 'has_trap', 'has_shop',
                    'discovered_at', 'metadata'
                ])

    def _generate_session_id(self, user_id: int) -> str:
        """Генерирует уникальный ID для сессии"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{user_id}_{timestamp}"

    def _get_current_session_id(self, user_id: int) -> Optional[str]:
        """Получает ID активной сессии пользователя"""
        try:
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if (int(row['user_id']) == user_id and
                            row['end_time'] == '' and
                            row['reason'] == ''):
                        return row['session_id']
        except Exception as e:
            logger.error(f"Ошибка при получении сессии: {e}")
        return None

    def save_player(self, user_id: int, username: str, first_name: str, last_name: str):
        """Сохраняет или обновляет информацию об игроке"""
        now = datetime.now().isoformat()

        # Читаем существующих игроков
        players = []
        player_exists = False

        try:
            if os.path.exists(self.players_file):
                with open(self.players_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    players = list(reader)

                    # Ищем существующего игрока
                    for i, player in enumerate(players):
                        if int(player['user_id']) == user_id:
                            # Обновляем данные
                            players[i]['username'] = username
                            players[i]['first_name'] = first_name
                            players[i]['last_name'] = last_name
                            players[i]['last_seen'] = now
                            player_exists = True
                            break
        except Exception as e:
            logger.error(f"Ошибка чтения игроков: {e}")

        # Если игрок новый
        if not player_exists:
            new_player = {
                'user_id': str(user_id),
                'username': username or '',
                'first_name': first_name or '',
                'last_name': last_name or '',
                'total_games': '0',
                'total_steps': '0',
                'total_rooms': '0',
                'dragons_found': '0',
                'gold_collected': '0',
                'first_seen': now,
                'last_seen': now
            }
            players.append(new_player)

        # Записываем обратно
        try:
            with open(self.players_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'user_id', 'username', 'first_name', 'last_name',
                    'total_games', 'total_steps', 'total_rooms',
                    'dragons_found', 'gold_collected',
                    'first_seen', 'last_seen'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(players)
        except Exception as e:
            logger.error(f"Ошибка записи игроков: {e}")

    def save_game_session(self, user_id: int, session_data: Dict[str, Any]):
        """Сохраняет данные игровой сессии"""
        session_id = self._get_current_session_id(user_id)
        now = datetime.now().isoformat()

        if not session_id:
            # Создаем новую сессию
            session_id = self._generate_session_id(user_id)
            try:
                with open(self.sessions_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        session_id, user_id, now, '',  # end_time пустой
                        '',  # duration_seconds
                        session_data.get('steps', 0),
                        session_data.get('rooms_visited', 0),
                        session_data.get('dragon_found', False),
                        session_data.get('gold', 0),
                        False,  # died
                        ''  # reason
                    ])
            except Exception as e:
                logger.error(f"Ошибка создания сессии: {e}")
                return

            logger.info(f"Создана новая сессия {session_id} для пользователя {user_id}")
        else:
            # Обновляем существующую сессию
            sessions = []
            try:
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    sessions = list(reader)

                # Обновляем сессию
                for i, session in enumerate(sessions):
                    if session['session_id'] == session_id:
                        sessions[i]['steps'] = str(session_data.get('steps', 0))
                        sessions[i]['rooms_visited'] = str(session_data.get('rooms_visited', 0))
                        sessions[i]['dragon_found'] = str(session_data.get('dragon_found', False))
                        sessions[i]['gold_earned'] = str(session_data.get('gold', 0))
                        break

                # Записываем обратно
                with open(self.sessions_file, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = [
                        'session_id', 'user_id', 'start_time', 'end_time',
                        'duration_seconds', 'steps', 'rooms_visited',
                        'dragon_found', 'gold_earned', 'died', 'reason'
                    ]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(sessions)

            except Exception as e:
                logger.error(f"Ошибка обновления сессии: {e}")

    def save_room(self, user_id: int, room_data: Dict[str, Any]):
        """Сохраняет данные комнаты"""
        session_id = self._get_current_session_id(user_id)
        if not session_id:
            logger.warning(f"Нет активной сессии для сохранения комнаты user_id={user_id}")
            return

        now = datetime.now().isoformat()

        try:
            with open(self.rooms_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    room_data.get('room_id', ''),
                    user_id,
                    session_id,
                    room_data.get('pos_x', 0),
                    room_data.get('pos_y', 0),
                    room_data.get('width', 3),
                    room_data.get('height', 3),
                    room_data.get('explored', False),
                    room_data.get('has_monster', False),
                    room_data.get('has_chest', False),
                    room_data.get('has_trap', False),
                    room_data.get('has_shop', False),
                    now,
                    json.dumps(room_data.get('metadata', {}), ensure_ascii=False)
                ])
        except Exception as e:
            logger.error(f"Ошибка сохранения комнаты: {e}")

    def update_player_stats(self, user_id: int, steps: int, rooms_visited: int, dragon_found: bool):
        """Обновляет статистику игрока после завершения игры"""
        try:
            players = []
            with open(self.players_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                players = list(reader)

            for i, player in enumerate(players):
                if int(player['user_id']) == user_id:
                    # Обновляем статистику
                    players[i]['total_games'] = str(int(player['total_games']) + 1)
                    players[i]['total_steps'] = str(int(player['total_steps']) + steps)
                    players[i]['total_rooms'] = str(int(player['total_rooms']) + rooms_visited)

                    if dragon_found:
                        players[i]['dragons_found'] = str(int(player['dragons_found']) + 1)

                    # Обновляем last_seen
                    players[i]['last_seen'] = datetime.now().isoformat()
                    break

            # Записываем обратно
            with open(self.players_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'user_id', 'username', 'first_name', 'last_name',
                    'total_games', 'total_steps', 'total_rooms',
                    'dragons_found', 'gold_collected',
                    'first_seen', 'last_seen'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(players)

        except Exception as e:
            logger.error(f"Ошибка обновления статистики игрока: {e}")

    def end_game_session(self, user_id: int):
        """Завершает игровую сессию"""
        session_id = self._get_current_session_id(user_id)
        if not session_id:
            return

        now = datetime.now().isoformat()

        try:
            sessions = []
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                sessions = list(reader)

            for i, session in enumerate(sessions):
                if session['session_id'] == session_id:
                    # Обновляем время завершения
                    sessions[i]['end_time'] = now

                    # Вычисляем длительность
                    start_time = datetime.fromisoformat(session['start_time'])
                    end_time = datetime.fromisoformat(now)
                    duration = int((end_time - start_time).total_seconds())
                    sessions[i]['duration_seconds'] = str(duration)
                    break

            # Записываем обратно
            with open(self.sessions_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'session_id', 'user_id', 'start_time', 'end_time',
                    'duration_seconds', 'steps', 'rooms_visited',
                    'dragon_found', 'gold_earned', 'died', 'reason'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(sessions)

        except Exception as e:
            logger.error(f"Ошибка завершения сессии: {e}")

    def get_player_stats(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получает статистику игрока"""
        try:
            with open(self.players_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for player in reader:
                    if int(player['user_id']) == user_id:
                        return {
                            'total_games': int(player['total_games']),
                            'total_steps': int(player['total_steps']),
                            'total_rooms': int(player['total_rooms']),
                            'dragons_found': int(player['dragons_found']),
                            'gold_collected': int(player['gold_collected']),
                            'first_seen': player['first_seen'],
                            'last_seen': player['last_seen']
                        }
        except Exception as e:
            logger.error(f"Ошибка получения статистики игрока: {e}")
        return None

    def get_player_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает все сессии игрока"""
        sessions = []
        try:
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for session in reader:
                    if int(session['user_id']) == user_id:
                        sessions.append({
                            'session_id': session['session_id'],
                            'start_time': session['start_time'],
                            'end_time': session['end_time'],
                            'duration': int(session['duration_seconds']) if session['duration_seconds'] else 0,
                            'steps': int(session['steps']),
                            'rooms_visited': int(session['rooms_visited']),
                            'dragon_found': session['dragon_found'].lower() == 'true',
                            'gold_earned': int(session['gold_earned']),
                            'died': session['died'].lower() == 'true',
                            'reason': session['reason']
                        })
        except Exception as e:
            logger.error(f"Ошибка получения сессий игрока: {e}")
        return sessions