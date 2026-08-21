# from globals import active_users, dict_lock
import threading, time


active_users = {}
dict_lock = threading.Lock()


def getDictLock() -> threading.Lock:
    return dict_lock


def getActiveUsers() -> dict:
    return active_users

def addUserToGlobals(user_id : str):
    
    with dict_lock:
        active_users[user_id] = {
            'interruptChat': False,
            'last-seen': time.time()
        }
        return len(str(active_users[user_id])) > 0


# this will be called on a thread by the main python script
def cleanupActiveUsers():
    """
    Automatically clears the global dictionary: 'active_users', defined in the globals.py script.
    Loops over every key (user_id/UUID) and checks if the user has timed out (has not pinged the server for > 30 seconds).

    If the user has not pinged the server for more than 30 seconds, they have timed out and are removed from the global dictionary.
    Otherwise, nothing happens. Deleted users are printed to the terminal for debugging purposes. 
    """



    timeout_seconds = 31 # define how long a user can go without pinging the backend and still have their user_ID saved (in the global dictionary)
    while True:
        time.sleep(timeout_seconds/2)
        current_time = time.time()
        expired_ids = []
        
        print("Current global dict (prior to update): ", active_users) # debug line

        with dict_lock:
            for user_id, info in active_users.items():
                if current_time-info['last-seen'] > timeout_seconds:
                    expired_ids.append(user_id)
                    
            for user_id in expired_ids:
                print(f"Deleting inactive user from global dictionary: {user_id}")
                del active_users[user_id]