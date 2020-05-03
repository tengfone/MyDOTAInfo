import logging, os, sys, requests, json
from telegram import ParseMode, ReplyKeyboardMarkup, ChatAction
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, CallbackQueryHandler, \
    ConversationHandler
from functools import wraps
from vanityToSteam32 import get32id
from datetime import datetime
from API_KEY import STEAM_API
from collections import Counter
from API_KEY import TOKEN

# logger
logger = logging.getLogger()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# global variable
mode = "dev"
INVALID_ID = "This profile does not have any DOTA2 Information.\nTry exposing match data in DOTA2 Settings.\nTry another profile! Or /start to restart"

# api_key = os.getenv("API_KEY")

def send_typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(update, context, *args, **kwargs)

    return command_func


# the different type of states
MENU, STEAM_ID, PLAYER_OPTIONS, NUMBER_OF_LINES, NUMBER_OF_MATCHES = range(5)

# different type of custom keyboard
menu_reply_keyboard = [["Let's Go 🎮", 'Infoℹ️']]
player_reply_keyboard = [["Recent Matches👁", "Word Count💬", "Heroes"], ["More Info ℹ", "Back"]]


@send_typing_action
def start(update, context):
    update.message.reply_text("Welcome to MyDotaInfo, click on the following options to begin!",
                              reply_markup=ReplyKeyboardMarkup(menu_reply_keyboard, one_time_keyboard=True))
    return MENU


@send_typing_action
def info(update, context):
    update.message.reply_text(
        "This bot is using Steam and OpenDota API's. Following information provided might not be up to date as there are delays.\nFor more accurate information please use a proper DOTA2 performance tracker.\n\nPlease expose match data to public in DOTA2 Settings. If there are any problems please contact @tengfone. GLHF!",
        reply_markup=ReplyKeyboardMarkup(menu_reply_keyboard, one_time_keyboard=True))
    return MENU


@send_typing_action
def getsteamid(update, context):
    update.message.reply_text("Please enter Steam ID:\nExample: steamcommunity(.)com/id/XXX where XXX is your ID")
    return STEAM_ID


@send_typing_action
def display_main(update, context):
    text = update.message.text
    text = text.strip().replace(' ', '')
    try:
        steam32id = get32id(text)
        context.user_data['accountID'] = steam32id
        output = account_info(steam32id)
        if output == INVALID_ID:
            update.message.reply_text(output)
            return STEAM_ID
        update.message.reply_text(output,
                                  reply_markup=ReplyKeyboardMarkup(player_reply_keyboard, one_time_keyboard=True))
    except ValueError:
        update.message.reply_text(
            "Something went wrong, key in a valid ID. If you're keying a long serial of number, it will not work. It must be a user define name. Please go Steam settings to configure a profile URL.")
        return STEAM_ID
    return PLAYER_OPTIONS


@send_typing_action
def recent_matches(update, context):
    account_id = str(context.user_data['accountID'])
    text = update.message.text
    try:
        text = int(text)
        if text > 20:
            text = 20
        output = get_recent_matches(account_id, text)
        if len(output) > 4096:
            for x in range(0, len(output), 4096):
                update.message.reply_text(output[x:x + 4096])
        else:
            update.message.reply_text(output,
                                      reply_markup=ReplyKeyboardMarkup(player_reply_keyboard, one_time_keyboard=True))

        return PLAYER_OPTIONS
    except ValueError:
        update.message.reply_text("Key In An Integer, Maximum 20 Matches")
        return NUMBER_OF_MATCHES


@send_typing_action
def user_word_count(update, context):
    update.message.reply_text("How many lines you wanna see? Maximum 450 lines")
    return NUMBER_OF_LINES

@send_typing_action
def user_recent_matches(update,context):
    update.message.reply_text("How many matches you wanna see? Maximum 20 Matches")
    return NUMBER_OF_MATCHES


@send_typing_action
def word_counter(update, context):
    account_id = str(context.user_data['accountID'])
    text = update.message.text
    try:
        text = int(text)
        output = most_used_words(account_id, text)
        if len(output) > 4096:
            for x in range(0, len(output), 4096):
                update.message.reply_text(output[x:x + 4096])
        else:
            update.message.reply_text(output,
                                      reply_markup=ReplyKeyboardMarkup(player_reply_keyboard, one_time_keyboard=True))

        return PLAYER_OPTIONS
    except ValueError:
        update.message.reply_text("Key In An Integer")
        return NUMBER_OF_LINES


@send_typing_action
def heroes_stats(update, context):
    account_id = str(context.user_data['accountID'])
    output = get_hero_stats(account_id)
    if len(output) > 4096:
        for x in range(0, len(output), 4096):
            update.message.reply_text(output[x:x + 4096],
                                      reply_markup=ReplyKeyboardMarkup(player_reply_keyboard, one_time_keyboard=True))
    else:
        update.message.reply_text(output,
                                  reply_markup=ReplyKeyboardMarkup(player_reply_keyboard, one_time_keyboard=True))
    return PLAYER_OPTIONS


@send_typing_action
def player_info(update, context):
    account_id = str(context.user_data['accountID'])
    output = played_with_pro(account_id)
    if len(output) > 4096:
        for x in range(0, len(output), 4096):
            update.message.reply_text(output[x:x + 4096],
                                      reply_markup=ReplyKeyboardMarkup(player_reply_keyboard, ReplyKeyboardRemove=True))
    else:
        update.message.reply_text(output,
                                  reply_markup=ReplyKeyboardMarkup(player_reply_keyboard, ReplyKeyboardRemove=True))
    return PLAYER_OPTIONS


def main():
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MENU: [MessageHandler(Filters.regex("Let's Go 🎮"), getsteamid, pass_user_data=True),
                   MessageHandler(Filters.regex('Infoℹ️'), info, pass_chat_data=True)],
            STEAM_ID: [MessageHandler(Filters.text, display_main, pass_user_data=True)],
            PLAYER_OPTIONS: [MessageHandler(Filters.regex("Recent Matches👁"), user_recent_matches, pass_user_data=True),
                             MessageHandler(Filters.regex('Word Count💬'), user_word_count, pass_chat_data=True),
                             MessageHandler(Filters.regex('Heroes'), heroes_stats, pass_chat_data=True),
                             MessageHandler(Filters.regex('More Info ℹ'), player_info, pass_chat_data=True)],
            NUMBER_OF_LINES: [MessageHandler(Filters.text, word_counter)],
            NUMBER_OF_MATCHES: [MessageHandler(Filters.text,recent_matches)],
        },
        fallbacks=[MessageHandler(Filters.regex('^Back$'), start, pass_user_data=True)],
        allow_reentry=True  # this line is important as it allows the user to talk to the bot anytime
    )
    dispatcher.add_handler(conv_handler)
    # log all errors
    dispatcher.add_error_handler(error)

    # about me bot
    aboutMe_handler = CommandHandler('about', info)
    dispatcher.add_handler(aboutMe_handler)

    # unknown commands, must put at the end
    unknown_handler = MessageHandler(Filters.command, unknownCommand)
    dispatcher.add_handler(unknown_handler)

    # unknown messages, must put at the end
    unknown_handler = MessageHandler(Filters.text, unknownText)
    dispatcher.add_handler(unknown_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def account_info(accountID):
    response = requests.get("https://api.opendota.com/api/players/{}".format(accountID)).json()
    response2 = requests.get("https://api.opendota.com/api/players/{}/wl".format(accountID)).json()
    try:
        profile = response['profile']
    except KeyError:
        return INVALID_ID
    persona_name = profile['personaname']
    account_id = profile["account_id"]
    steam_profile = profile['profileurl']
    dotaplus = str(profile['plus'])
    if dotaplus == "False":
        edit_dotaplus = "Nope, too poor to afford DotaPlus"
    else:
        edit_dotaplus = "Yes you have that unfair advantage"
    region = profile["loccountrycode"]
    rank_tier = response['rank_tier']
    leaderboard_rank = response['leaderboard_rank']
    player_medal = medals(rank_tier)
    mmr_estimate = response["mmr_estimate"]["estimate"]
    competitive_rank = response["competitive_rank"]
    solo_competitive_rank = response["solo_competitive_rank"]
    win_matches = int(response2["win"])
    lost_matches = int(response2["lose"])
    win_rate = round((win_matches / (win_matches + lost_matches)) * 100, 2)

    output = "Hello {}, this is your Dota account ID:{} and your steam account profile: {} .\nDotaPlus: {}\nRegion: {}\nMedal Rank: {}\nLeaderboard: {}\nEstimated MMR: {}\nParty MMR: {}\nSolo Rank: {}\nWin/Lose Rate: {}/{} = {}%".format(
        persona_name, account_id, steam_profile, edit_dotaplus, region, player_medal, leaderboard_rank, mmr_estimate,
        competitive_rank, solo_competitive_rank, win_matches, lost_matches, win_rate)
    return output


def medals(rank_tier):
    rank_tier = str(rank_tier)
    if rank_tier[0] == "1":
        medal = "Herald "
        output = medal + rank_tier[-1]
    elif rank_tier[0] == "2":
        medal = "Guardian "
        output = medal + rank_tier[-1]
    elif rank_tier[0] == "3":
        medal = "Crusader "
        output = medal + rank_tier[-1]
    elif rank_tier[0] == "4":
        medal = "Archon "
        output = medal + rank_tier[-1]
    elif rank_tier[0] == "5":
        medal = "Legend "
        output = medal + rank_tier[-1]
    elif rank_tier[0] == "6":
        medal = "Ancient "
        output = medal + rank_tier[-1]
    elif rank_tier[0] == "7":
        medal = "Divine "
        output = medal + rank_tier[-1]
    elif rank_tier[0] == "8":
        medal = "Immortal "
        output = medal
    else:
        output = "None"
    return output


def get_recent_matches(accountID, how_many):
    output = ""
    response = requests.get("https://api.opendota.com/api/players/{}/recentMatches".format(accountID)).json()
    lobby_data = json.loads(open('Data/LobbyType.json').read())
    hero_id = requests.get(
        "https://api.steampowered.com/IEconDOTA2_570/GetHeroes/v0001/?key={}&language=en_us&format=JSON".format(
            STEAM_API))
    if hero_id.status_code == 403:
        raise ValueError("Steam API Key is invalid")
    else:
        hero_id.raise_for_status()
        hero_id = (hero_id.json())['result']['heroes']

    top3_match = response[0:how_many]

    for each in top3_match:
        match_id = each['match_id']
        player_slot = int(each['player_slot'])
        if 0 <= player_slot <= 127:
            player_team = "Radiant"
        elif 128 <= player_slot <= 255:
            player_team = "Dire"
        else:
            player_team = "Unknown"
        radiant_win = each['radiant_win']
        if player_team == "Radiant" and radiant_win:
            player_win = "Won Match"
        elif player_team == "Dire" and radiant_win == False:
            player_win = "Won Match"
        else:
            player_win = "Lost Match"
        duration = int(each['duration'])
        match_time_second = duration % (24 * 3600)
        match_time_hour = match_time_second // 3600
        match_time_second %= 3600
        match_time_minutes = match_time_second // 60
        match_time_second %= 60
        match_time = "%d:%02d:%02d" % (match_time_hour, match_time_minutes, match_time_second)
        lobby_type = each['lobby_type']
        try:
            lobby_kind = lobby_data[str(lobby_type)]['name']
        except KeyError:
            lobby_kind = "Unknown"
        raw_hero_id = (each['hero_id'])
        for i in hero_id:
            if i['id'] == raw_hero_id:
                player_hero = i['localized_name']
                break
        kills = str(each['kills'])
        deaths = str(each['deaths'])
        assists = str(each['assists'])
        player_kda = kills + "/" + deaths + "/" + assists
        skill = str(each['skill'])
        if skill == '1':
            player_skill = "Normal Skill"
        elif skill == '2':
            player_skill = "High Skill"
        elif skill == '3':
            player_skill = "Very High Skill"
        else:
            player_skill = "Unknown"
        start_time = each['start_time']
        ts = int(start_time)
        player_date = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        per_line = "MatchID: {}\nGame Played On: {}\nPlayer Team: {}\nMatch Outcome: {}\nMatch Duration: {}\nLobby Type: {}\nSkill Bracket: {}\nHero Played: {}\nKDA Ratio: {}\n\n".format(
            match_id, player_date, player_team, player_win, match_time, lobby_kind, player_skill, player_hero,
            player_kda)
        output = output + per_line
    return output


def most_used_words(accountID, input):
    output = ''
    response = requests.get("https://api.opendota.com/api/players/{}/wordcloud".format(accountID)).json()
    word_count = response["all_word_counts"]
    word_count = Counter(word_count)
    for k, v in word_count.most_common(input):
        per_line = ('%s: %i' % (k, v)) + "\n"
        output = output + per_line
    return output


def get_hero_stats(accountID):
    output = ''
    response = requests.get("https://api.opendota.com/api/players/{}/heroes".format(accountID)).json()
    hero_id = requests.get(
        "https://api.steampowered.com/IEconDOTA2_570/GetHeroes/v0001/?key={}&language=en_us&format=JSON".format(
            STEAM_API))

    if hero_id.status_code == 403:
        raise ValueError("Steam API Key is invalid")
    else:
        hero_id.raise_for_status()
        hero_id = (hero_id.json())['result']['heroes']

    for each in response:
        raw_hero_id = int(each['hero_id'])
        total_games = each['games']
        won_game = each['win']
        try:
            hero_wr = round((won_game / (total_games)) * 100, 2)
        except ZeroDivisionError:
            hero_wr = 0
        hero_wr = str(hero_wr)
        total_games = str(total_games)
        for i in hero_id:
            if int(i['id']) == raw_hero_id:
                player_hero = str(i['localized_name'])
                break
        per_line = "You played {} {} times. Win rate: {}%\n".format(player_hero, total_games, hero_wr)
        output = output + per_line
    return output


def played_with_pro(accountID):
    output = ''
    response = requests.get("https://api.opendota.com/api/players/{}/pros".format(accountID)).json()
    if len(response) == 0:
        output = "You have not match with any pro player's yet. Don't worry you'll get there soon!"

    for each in response:
        pro_name = each['name']
        pro_personaname = each['personaname']
        pro_profileurl = each['profileurl']
        pro_countrycode = each['country_code']
        if pro_countrycode == '':
            pro_countrycode = pro_name + " did not provide a country."
        else:
            pro_countrycode = pro_countrycode.upper()
        pro_games = each['games']
        per_line = "You have matched up with {} AKA {} from {} for {} time(s)!\nSteam Profile: {}\n\n".format(
            pro_name,
            pro_personaname,
            pro_countrycode,
            pro_games,
            pro_profileurl)
        output = output + per_line
    return output

@send_typing_action
def unknownCommand(update, context):
    context.bot.send_message(chat_id=update.message.chat_id,
                             text="Invalid command. /start if Unsure")


@send_typing_action
def unknownText(update, context):
    context.bot.send_message(chat_id=update.message.chat_id,
                             text="Invalid text. /start if unsure")


if __name__ == '__main__':
    logger.info("Starting bot")
    main()
