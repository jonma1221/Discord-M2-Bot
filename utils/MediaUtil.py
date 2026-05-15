
def convertSecondsToMinutesAndSeconds(seconds):
    minutes, remaining_seconds = divmod(seconds, 60)
    return minutes, remaining_seconds