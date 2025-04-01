from chatengine.models import SimpleCommands
from django.template import Context, Template   
from asgiref.sync import sync_to_async 
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

class ChatEngine:
    def __init__(self,chatbot):
        self.chatbot = chatbot
        self.simple_commands = {}
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
        llm = ChatOpenAI(model_name="gpt-4o",temperature=1.0)
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
    #Személyiség
    def generate_generic_response(self, sender, message):
        generic_prompt = self.chatbot.generic_prompt
        llm = ChatOpenAI(model_name="gpt-4o",temperature=1.0)
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

    async def get_response(self, source, sender, message):
        await self.update_data()
        command = ""
        non_command = ""
        matching_non_commands = [
            s for s in self.non_command_strings if message.lower().startswith(s)
        ]
        #Abban az esetben ha a kapott szöveg nem egy parancs vagy megszólítás ("!" , "@")
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
