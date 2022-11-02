class Aria2Status:
    def __init__(self, message=""):
        self.status = {
            "is_done": False,
            "is_error": False,
            "message": message,
            "args": {}
        }

    def set_done(self, status: bool):
        self.status["is_done"] = status

    def set_error(self, status: bool):
        self.status["is_error"] = status

    def set_message(self, message: str):
        self.status["message"] = message

    def set_args(self, **kwargs):
        self.status["args"] = kwargs

    def get_dict(self) -> dict:
        return self.status
