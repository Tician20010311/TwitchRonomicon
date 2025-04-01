from openai import OpenAI
from django.conf import settings 
from django.core.management.base import BaseCommand

client = OpenAI(
    api_key=settings.OPENAI_API_KEY  # Cseréld le a saját API-kulcsodra, de ne osszd meg nyilvánosan!
)

class Command(BaseCommand):
    help = 'Rövid leírást kérek.'

    def handle(self, *args, **kwargs):
        # Itt írd le a parancs működését
        self.stdout.write("Your command executed successfully!")

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Hogy vagy ?"}
            ]
        )

        print(completion.choices[0].message.content)
