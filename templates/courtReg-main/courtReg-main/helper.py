import sys
from mysqlconnection import connectToMySQL
from datetime import timedelta
from flask import flash


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
    query = "UPDATE ebc_db.users SET onCourt=0 WHERE first_name = '{}';".format(name)
    mysql.query_db(query)


def calculate_end_time(num_players, start_time, one_player_time, two_player_time, three_player_time, four_player_time):
    """Calculate the end time for the court depending on the number of players on court"""
    end_time = None
    if num_players == 1:
        end_time = start_time + timedelta(minutes=one_player_time)
    elif num_players == 2:
        end_time = start_time + timedelta(minutes=two_player_time)
    elif num_players == 3:
        end_time = start_time + timedelta(minutes=three_player_time)
    elif num_players == 4:
        end_time = start_time + timedelta(minutes=four_player_time)
    return end_time.strftime("%H:%M:%S")