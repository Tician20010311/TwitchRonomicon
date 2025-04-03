import random
from chatengine.games.chatgame import ChatGame

class Blackjack(ChatGame):
    def __init__(self, chatbot):
        super().__init__(chatbot)
        self.active_games = {}  # Aktív játékok tárolása {'channel_name': {'players': [], 'deck': [], 'hands': {}, 'dealer': [], 'bets': {}}}

    def create_deck(self):
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        suits = ['hearts', 'diamonds', 'clubs', 'spades']
        deck = [{'rank': r, 'suit': s} for r in ranks for s in suits]
        random.shuffle(deck)
        return deck

    async def player_move(self, chatuser, message):
        channel = chatuser.username  # Twitch csatorna neve
        if message.startswith('!blackjack'):
            return await self.start_game(channel, chatuser)
        elif message.startswith('!join'):
            return await self.join_game(channel, chatuser)
        elif message.startswith('!hit'):
            return await self.hit(channel, chatuser)
        elif message.startswith('!stand'):
            return await self.stand(channel, chatuser)

    async def start_game(self, channel, chatuser):
        if channel in self.active_games:
            return "Már van egy aktív Blackjack játék! Csatlakozz: !join"
        self.active_games[channel] = {
            'players': [chatuser.username],
            'deck': self.create_deck(),
            'hands': {},
            'dealer': [],
            'bets': {},
            'turn': 0
        }
        return f"{chatuser.username} elindította a Blackjack játékot! Csatlakozz: !join (max 3 játékos)"

    async def join_game(self, channel, chatuser):
        if channel not in self.active_games:
            return "Nincs aktív Blackjack játék! Indítsd el: !blackjack"
        game = self.active_games[channel]
        if chatuser.username in game['players']:
            return "Már csatlakoztál a játékhoz!"
        if len(game['players']) >= 3:
            return "A játék tele van! Maximum 3 játékos játszhat."
        game['players'].append(chatuser.username)
        return f"{chatuser.username} csatlakozott a játékhoz! Még {3 - len(game['players'])} hely van."

    async def hit(self, channel, chatuser):
        if channel not in self.active_games:
            return "Nincs aktív játék! Indítsd el: !blackjack"
        game = self.active_games[channel]
        if chatuser.username != game['players'][game['turn']]:
            return "Nem a te köröd van!"
        card = game['deck'].pop()
        game['hands'].setdefault(chatuser.username, []).append(card)
        hand_value = self.calculate_hand_value(game['hands'][chatuser.username])
        if hand_value > 21:
            game['turn'] += 1  # Következő játékos
            return f"{chatuser.username} húzott egy lapot: {card['rank']} {card['suit']} - TÚLLÉPTED a 21-et! Kiestél!"
        return f"{chatuser.username} húzott egy lapot: {card['rank']} {card['suit']} - Összérték: {hand_value}"

    async def stand(self, channel, chatuser):
        if channel not in self.active_games:
            return "Nincs aktív játék! Indítsd el: !blackjack"
        game = self.active_games[channel]
        if chatuser.username != game['players'][game['turn']]:
            return "Nem a te köröd van!"
        game['turn'] += 1  # Következő játékos
        if game['turn'] >= len(game['players']):
            return await self.dealer_turn(channel)
        return f"{chatuser.username} megállt! Következő: {game['players'][game['turn']]}"

    async def dealer_turn(self, channel):
        game = self.active_games[channel]
        while self.calculate_hand_value(game['dealer']) < 17:
            game['dealer'].append(game['deck'].pop())
        dealer_value = self.calculate_hand_value(game['dealer'])
        result = f"Az osztó lapjai: {', '.join([card['rank'] for card in game['dealer']])} ({dealer_value})\n"
        for player in game['players']:
            player_value = self.calculate_hand_value(game['hands'][player])
            if player_value > 21:
                result += f"{player}: Vesztett (Túllépte a 21-et)\n"
            elif dealer_value > 21 or player_value > dealer_value:
                result += f"{player}: Nyert! ({player_value})\n"
            elif player_value == dealer_value:
                result += f"{player}: Döntetlen ({player_value})\n"
            else:
                result += f"{player}: Vesztett ({player_value})\n"
        del self.active_games[channel]
        return result

    def calculate_hand_value(self, hand):
        value = 0
        aces = 0
        for card in hand:
            if card['rank'].isdigit():
                value += int(card['rank'])
            elif card['rank'] in ['J', 'Q', 'K']:
                value += 10
            else:  # Ace
                aces += 1
                value += 11
        while value > 21 and aces:
            value -= 10
            aces -= 1
        return value
