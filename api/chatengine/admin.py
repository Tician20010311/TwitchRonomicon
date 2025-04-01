from django.contrib import admin

from chatengine.models import SimpleCommands , ChatBot

class ChatbotAdmin(admin.ModelAdmin):
    list_display = ("nickname", "twitch_channel")

class SimpleCommandsAdmin(admin.ModelAdmin):
    list_display = ("command", "response")

admin.site.register(SimpleCommands, SimpleCommandsAdmin)
admin.site.register(ChatBot, ChatbotAdmin)
