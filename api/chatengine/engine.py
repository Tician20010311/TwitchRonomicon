from chatengine.models import SimpleCommands , ChatUser
from django.template import Context, Template   
from asgiref.sync import sync_to_async 
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from django.conf import settings
import random 

class ChatEngine:
    def __init__(self,chatbot):
        self.chatbot = chatbot
        self.simple_commands = {}
        self.openai_api_key = settings.OPENAI_API_KEY
        self.non_command_strings = []
        self.load_commands()

    async def update_data(self):
        await sync_to_async(self.load_commands,thread_sensitive=True)()

    def load_commands(self):
        self.simple_commands = {}
        for command in SimpleCommands.objects.filter(chatbot__nickname=self.chatbot.nickname):
            self.simple_commands[command.command] = command.response
        self.non_command_strings = self.simple_commands.keys()
    #Kapott szöveg átfogalmazása
    def rephrase_text(self, text):
        rephrase_prompt = self.chatbot.rephrase_prompt
        llm = ChatOpenAI(model_name="gpt-4o",temperature=1.0,api_key=self.openai_api_key)
        reword_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    rephrase_prompt,
                ),
                ("human" ,"Átfogalmazandó szöveg: " + text)
            ]
        )
        chain = reword_prompt | llm 
        ai_response = chain.invoke({})
        return ai_response.content
    #Generál egy generic responset
    
    def generate_generic_response(self, sender, message):
        generic_prompt = self.chatbot.generic_prompt
        llm = ChatOpenAI(model_name="gpt-4o",temperature=0.7,api_key=self.openai_api_key)
        answer_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    generic_prompt,
                ),
                ("human", sender+": "+message),
            ]
        )
        chain = answer_prompt | llm 
        ai_response = chain.invoke({})
        return ai_response.content
    
    @sync_to_async
    def get_or_create_chatuser(self, nickname):
        chatuser, _ =  ChatUser.objects.get_or_create(chatbot=self.chatbot, platform="twitch", username=nickname)
        return chatuser

    
    async def play_roulette(self,sender, message):
        chatuser = await self.get_or_create_chatuser(sender)
        response = ""
        instructions = f"Kedves @{sender} a rulett parancshoz add meg , hogy mire teszel és mennyit. Tehetsz az alábbiakra : piros , fekete , konkrét szám, páros , páratlan , alacsony (1-18) , magas (19-36)."
        if message == f"{self.chatbot.twitch_prefix}rulett":
            return instructions
        params = message.split(" ")[1:]
        if len(params) != 2:
            return instructions
        bet, amount = params
        if not amount.isdigit():
            return f"Kedves {sender}, a tét csak szám lehet."
        if int(amount) < 1:
            return f"Kedves {sender}, a tét csak pozitív szám lehet" 
        if bet not in ["piros", "fekete", "konkrét", "páros", "páratlan", "alacsony", "magas"] and not bet.isdigit():
            return f"Kedves {sender}, a tét csak piros, fekete, konkrét szá, páros, páratlan, alacsony vagy magas lehet."
        if int(amount) > chatuser.current_score:
            return f"Kedves {sender}, nincs elegő pontod. Jelenelegi pontszámod: {chatuser.current_score}"
        chatuser.current_score -= int(amount)
        rolled_result = random.randint(1, 36)
        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        black_numbers = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
        if bet in ["piros", "fekete"]:
            if (bet == "piros" and rolled_result in red_numbers) or (bet == "fekete" and rolled_result in black_numbers):
                chatuser.current_score += int(amount)*2
                response = f"Gratulálunk! @{sender} nyertél {int(amount)*2} pontot! Az eredmény: {rolled_result}. A jelenelegi pontszámod: {chatuser.current_score}"
            else:
                response = f"Sajnos @{sender}, nem nyertél. Az eredmény: {rolled_result}. A jelenelegi pontszámod: {chatuser.current_score}"
        elif bet in ["páros", "páratlan"]:
            if (bet == "páros" and rolled_result % 2 == 0) or (bet == "páratlan" and rolled_result % 2 == 1):
                chatuser.current_score += int(amount)*2
                response = f"Gratulálunk! @{sender} nyertél {int(amount)*2} pontot! Az eredmény: {rolled_result}. A jelenelegi pontszámod: {chatuser.current_score}"
            else:
                response = f"Sajnos @{sender}, nem nyertél. Az eredmény: {rolled_result}. A jelenelegi pontszámod: {chatuser.current_score}"
        elif bet in ["alacsony", "magas"]:
            if (bet == "alacsony" and rolled_result <= 18) or (bet == "magas" and rolled_result >= 19):
                chatuser.current_score += int(amount)*2
                response = f"Gratulálunk! @{sender} nyertél {int(amount)*2} pontot! Az eredmény: {rolled_result}. A jelenelegi pontszámod: {chatuser.current_score}"
            else:
                response = f"Sajnos @{sender}, nem nyertél. Az eredmény: {rolled_result}."
        else:
            if rolled_result == int(bet):
                chatuser.current_score += int(amount)*36
                response = f"Gratulálunk! @{sender} nyertél {int(amount)*36} pontot! Az eredmény: {rolled_result}. A jelenelegi pontszámod: {chatuser.current_score}"
            else:
                chatuser.current_score -= int(amount)
                response = f"Sajnos @{sender}, nem nyertél. Az eredmény: {rolled_result}. A jelenelegi pontszámod: {chatuser.current_score}"
        sync_to_async(chatuser.save)()
        return response 
    
    async def get_response(self, source, sender, message):
        #await sync_to_async(self.chatbot.refresh_from_db())
        await self.update_data()
        command = ""
        non_command = ""
        matching_non_commands = [
            s for s in self.non_command_strings if message.lower().startswith(s)
        ]
        points_commands = ["pontszám","pontszam","points"]
        if any([message.startswith(f"{self.chatbot.twitch_prefix}{c}") for c in points_commands]):
            chatuser = await self.get_or_create_chatuser(sender)
            return f"Kedves {sender}, jelenelegi pontszámod: {chatuser.current_score}"
        elif message.startswith(f"{self.chatbot.twitch_prefix}rulett"):
            return await self.play_roulette(sender, message)

        #Ha a szöveg egy kész parancs 
        if matching_non_commands:
            non_command = matching_non_commands[0]
            template = Template(self.simple_commands[non_command])
            context = Context({"sender": sender, "message": message})
            return self.rephrase_text(template.render(context))
        #Ha a szöveg előtt prefixet kap ("!") 
        elif source == "twitch" and message.startswith(self.chatbot.twitch_prefix):
            command = message[1:]
            method = getattr(self, "on_" + command, None)
            if method:
                response = method(sender, message)
                return self.rephrase_text(response)
        #Ha "@"
        elif source == "twitch" and f"@{self.chatbot.nickname.lower()}" in message.lower():
            return self.generate_generic_response(sender, message)
        return ""
