from twitchio.ext import commands

class Bot(commands.Bot):

    SOURCE_NAME = "twitch"

    def __init__(self, chatengine):
        self.prefix = '!'
        super().__init__(token=chatengine.chatbot.access_token, prefix=chatengine.chatbot.twitch_prefix, initial_channels=[f'#{chatengine.chatbot.twitch_channel}'])
        self.chatengine = chatengine

    async def event_ready(self):
        print(f'Bejelentkezve mint : {self.nick}')
        print(f'UserID : {self.user_id}')

    async def event_message(self, message):
        if message.echo:
            return
        print(message.content)
        response = await self.chatengine.get_response(self.SOURCE_NAME,message.author.name, message.content)
        if response:
            await message.channel.send(response)
