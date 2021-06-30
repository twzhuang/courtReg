import sys
from mysqlconnection import connectToMySQL
from datetime import timedelta, datetime
from flask import flash

ONE_PLAYER_TIME = 1
TWO_PLAYER_TIME = 16
THREE_PLAYER_TIME = 21
FOUR_PLAYER_TIME = 26


def court_is_full(current_or_next, court_num_info):
    """
    :param current_or_next: user's court selection to be added to the current court or to be next on
        values: 'current' or 'next'
    :param court_num_info: dictionary containing information about the selected court number
    :return:
    """
    print(court_num_info, file=sys.stderr)
    if len(court_num_info[current_or_next]['players']) >= 4:
        return True
    return False


def generate_court():
    """
    Each court will contain a dictionary containing info for players currently
    on court and players up next on the court
    """
    court_info = {
        "current": {
            "start_time": "",
            "end_time": "",
            "players": []
        },
        "next": {
            "start_time": "",
            "end_time": "",
            "players": []
        }
    }
    return court_info


def remove_user_from_db(db, name):
    mysql = connectToMySQL(db)
    query = "UPDATE {}.users SET onCourt=0 WHERE first_name = '{}';".format(db, name)
    mysql.query_db(query)


def move_players_on_current_court(court_info):
    # Move "next on" players to "currently on"
    court_info["current"] = court_info["next"]
    court_info["next"] = {
        "start_time": "",
        "end_time": "",
        "players": []
    }

    # Set start time and end time for new players on court
    if court_info["current"]["players"]:
        start_time = datetime.now(pytz.utc)
        court_info["current"]["start_time"] = start_time.strftime("%I:%M %p").lstrip("0")
        court_info["current"]["end_time"] = calculate_end_time(
            len(court_info["current"]["players"]),
            start_time
        )


def calculate_end_time(num_players, start_time):
    """Calculate the end time for the court depending on the number of players on court"""
    end_time = None
    if num_players == 1:
        end_time = start_time + timedelta(minutes=ONE_PLAYER_TIME)
    elif num_players == 2:
        end_time = start_time + timedelta(minutes=TWO_PLAYER_TIME)
    elif num_players == 3:
        end_time = start_time + timedelta(minutes=THREE_PLAYER_TIME)
    elif num_players == 4:
        end_time = start_time + timedelta(minutes=FOUR_PLAYER_TIME)
    return end_time.strftime("%H:%M:%S")

