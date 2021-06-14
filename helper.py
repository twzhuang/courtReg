import sys
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
