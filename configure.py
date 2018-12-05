import json
import os.path
from configparser import ConfigParser, NoSectionError, NoOptionError
from json import JSONDecodeError
from typing import Callable, Optional

from . import logger

YES_NO_VALIDATOR = lambda _i: len(_i) == 1 and _i in 'YyNn'


class Configure:
    """
    config.ini周りの記録設定を司る
    """

    def __init__(self, configure_path, encoding='UTF-8'):
        """
        :param configure_path: config.iniへのパス
        """
        self._config = ConfigParser()
        self.configure_path = configure_path
        self.logger = logger.get_logger('utils.configure')
        self._reload(encoding, force_quit=False)

    @staticmethod
    def _prompt(prompt: str, validator: Callable[[str], bool] = lambda _i: True, default=None) -> str:
        """
        ユーザに何か質問して、バリデータに適う入力を返す
        TODO: 別にこのモジュールになくてもいい
        :param prompt: 質問文（答えのヒント込み）
        :param validator: 入力をチェックする関数
        :param default: 入力がなかった場合、設定されるデフォルト値。Noneだと無効
        :return: 入力値。
        """
        while True:
            _input = input(prompt)
            if not _input:
                if default is not None:
                    return default
            elif validator(_input):
                return _input

    def export(self, configure_path, force=False) -> bool:
        if os.path.exists(configure_path) and not force:
            self.logger.error('{} is already exist.')
        else:
            with open(configure_path, 'w') as configfile:
                self._config.write(configfile)
                self.logger.debug('Save successful!')
                return True
        return False

    def _reload(self, encoding: str = 'UTF-8', force_quit=True):
        """
        configure_pathにあるファイルを読み直す
        :param encoding: config file's encoding.
        :param force_quit:
        """
        if os.path.exists(self.configure_path):
            self._config.read(self.configure_path, encoding)
        else:
            if force_quit:
                self.logger.error('{} is not exist. Plz make it first.'.format(self.configure_path))
                exit(1)
            else:
                _i = Configure._prompt('{} is not exist. Create it? [Y/n]'.format(self.configure_path),
                                       YES_NO_VALIDATOR, 'y')
                if _i in 'Yy':
                    self.export(self.configure_path)

    def _save(self):
        """
        Sort all keys then save config.
        """
        for section in self._config.sections():
            for (k, v) in sorted(self._config.items(section), key=lambda x: x[0]):
                self._config.remove_option(section, k)
                self._config.set(section, k, v)

        with open(self.configure_path, 'w') as configfile:
            self._config.write(configfile)

    def _read_conf(self, section: str, key: str, default_val: str = None, required: bool = True) -> Optional[str]:
        """
        設定値の読み込み
        :param str section: Section name. NOT EMPTY!
        :param str key: Key name. NOT EMPTY!
        :param default_val: 値が指定されていない時に使われる値。default=Noneはrequired=Falseでのみ容認。
        :param required: bool Trueなら、値が不正な時スクリプトが止まる。
        :return: Optional[str] 取得できればその値。できなければNone。
        """
        self._reload()
        if not section or not key:
            self.logger.error('Plz specify section/key name!')
            return None

        try:
            return self._config.get(section, key)
        except NoSectionError:
            self.logger.error('no section named {}.'.format(section))
        except NoOptionError:
            self.logger.error('no value for {}.{}'.format(section, key))

        if required and default_val is None:
            self.logger.error('this field cannot to be set None')
        else:
            self.logger.info('use default value: {}.'.format(default_val))
            return default_val
        return None

    def read(self, section: str, key: str, default_val: str = None, required: bool = True) -> Optional[str]:
        """
        設定値の読み込み
        param → read help(_read_conf).
        """
        value = self._read_conf(section, key, default_val, required)
        try:
            self._config.get(section, key)
        except (NoSectionError, NoOptionError):
            if value is not None:  # デフォルト値が保存されてないなら保存してしまう
                self.write(section, key, value)
        return value

    def read_bool(self, section: str, key: str, default_val: bool = None, required: bool = True) -> Optional[bool]:
        """
        bool型設定値の読み込み
        param → read help(_read_conf).
        """
        value = self._read_conf(section, key, str(default_val), required)
        value_b = None
        if type(value) is not str:
            self.logger.warning('value type for {}.{} is not "bool" (value = {}).'.format(section, key, value))
            if type(default_val) is bool:
                value_b = default_val
        else:
            _v = value.upper()
            if _v in ['TRUE', 'FALSE']:
                value_b = _v == 'TRUE'
            else:
                self.logger.warning('value type for {}.{} is not "bool" (value = {}).'.format(section, key, value))
                if type(default_val) is bool:
                    value_b = default_val
        try:
            self._config.get(section, key)
        except (NoSectionError, NoOptionError):
            if value_b is not None:  # デフォルト値が保存されてないなら保存してしまう
                self.write(section, key, str(value_b))
        return value_b

    def read_float(self, section: str, key: str, default_val: float = None, required: bool = True) -> Optional[float]:
        """
        浮動小数点型設定値の読み込み
        param → read help(read_conf).
        """
        value = self._read_conf(section, key, str(default_val), required)
        value_f = None
        try:
            value_f = float(value)
        except ValueError:
            self.logger.warning('value type for {}.{} is not "float" (value = {}).'.format(section, key, value))
            if type(default_val) is float:
                value_f = default_val
        try:
            self._config.get(section, key)
        except (NoSectionError, NoOptionError):
            if value_f is not None:  # デフォルト値が保存されてないなら保存してしまう
                self.write(section, key, str(value_f))
        return value_f

    def read_int(self, section: str, key: str, default_val: int = None, required: bool = True) -> Optional[int]:
        """
        整数型設定値の読み込み
        param → read help(_read_conf).
        """
        value = self._read_conf(section, key, str(default_val), required)
        value_i = None
        try:
            value_i = int(value, 10)
        except ValueError:
            self.logger.warning('value type for {}.{} is not "int" (value = {}).'.format(section, key, value))
            if type(default_val) is int:
                value_i = default_val
        try:
            self._config.get(section, key)
        except (NoSectionError, NoOptionError):
            if value_i is not None:  # デフォルト値が保存されてないなら保存してしまう
                self.write(section, key, str(value_i))
        return value_i

    def read_json(self, section: str, key: str):
        """
        JSON型設定値の読み込み
        param → read help(_read_conf).
        """
        ret = self._read_conf(section, key)
        try:
            return json.loads(ret)
        except JSONDecodeError:
            self.logger.warning("Value type for {}.{} is not \"json\" (value = {}).".format(section, key, ret))
        return None

    def write(self, section: str, key: str, value: str, store: bool = True):
        """
        設定値の書き込み
        """
        self._reload()
        if not section or not key:
            self.logger.error('Plz specify section/key name!')
            exit(1)
        try:
            self._config.set(section, key, value)
        except NoSectionError:
            self.logger.warning('No section named {}. Create new one.'.format(section))
            self._config.add_section(section)
            self._config.set(section, key, value)
        self.logger.info('Set value: {}.{} = {}.'.format(section, key, value))
        if store:
            self._save()
