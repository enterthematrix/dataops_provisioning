import logging
from colorama import Fore, Style

LOG_FILE = 'deployment.log'

class Logger:
    def __init__(self, log_file: str = LOG_FILE, level=logging.DEBUG):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(level)

        if not self.logger.hasHandlers():
            try:
                # Console handler
                console_handler = logging.StreamHandler()
                console_handler.setLevel(level)

                # File handler
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(level)

                # Logging format
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

                console_handler.setFormatter(formatter)
                file_handler.setFormatter(formatter)

                # Add both handlers to the logger
                self.logger.addHandler(console_handler)
                self.logger.addHandler(file_handler)

            except (OSError, Exception) as e:
                self.logger.error(f"Error initializing logging handlers: {e}")

    def get_logger(self):
        return self.logger

    def log_msg(self, level, msg):
        try:
            match level:
                case 'info':
                    self.logger.setLevel(logging.INFO)
                    self.logger.info(f"{Fore.GREEN}{msg}{Style.RESET_ALL}")
                case 'warning':
                    self.logger.setLevel(logging.WARNING)
                    self.logger.warning(f"{Fore.YELLOW}{msg}{Style.RESET_ALL}")
                case 'error':
                    self.logger.setLevel(logging.ERROR)
                    self.logger.error(f"{Fore.RED}{msg}{Style.RESET_ALL}")
                case _:
                    self.logger.warning("Invalid log level specified; defaulting to warning.")
                    self.logger.warning(msg)
        except Exception as e:
            self.logger.error(f"Error logging message: {e}")