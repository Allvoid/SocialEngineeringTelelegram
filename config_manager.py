import json
from constants import CONFIG_FILE

class ConfigManager:
    def __init__(self):
        self.tokens = self._load()

    def _load(self):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def get(self, bot_name: str) -> str:
        return self.tokens.get(bot_name, '')

    def set(self, bot_name: str, token: str):
        self.tokens[bot_name] = token
        self._save()

    def clear(self, bot_name: str):
        if bot_name in self.tokens:
            del self.tokens[bot_name]
            self._save()

    def _save(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.tokens, f, ensure_ascii=False, indent=4)
        except Exception as e:
            raise IOError(f'Не удалось сохранить {CONFIG_FILE}: {e}')
