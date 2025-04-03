from abc import ABC

class ChatGame(ABC):
    def __init__(self,chatbot):
        self.chatbot = chatbot
        

    async def player_move(self,chatuser,move):
        pass