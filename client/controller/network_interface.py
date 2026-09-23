from abc import ABC, abstractmethod

class INetworkController(ABC):

    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def listen_server(self) -> None:
        pass

    @abstractmethod
    def send_msg(self, msg: str) -> None:
        pass

    @abstractmethod
    def create_match(self) -> None:
        pass

    @abstractmethod
    def join_match(self, id_match: int) -> None:
        pass

    @abstractmethod
    def move(self, col: int) -> None:
        pass

    @abstractmethod
    def quit(self) -> None:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def accept(self) -> None:
        pass

    @abstractmethod
    def reject(self) -> None:
        pass
