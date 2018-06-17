import datetime
import pytz


def calculateCost(distance):
    """Main function that checks conditions and estimates the cost
    @param: distance in m
    @return: cost in cents"""
    now = datetime.datetime.now(pytz.timezone("Asia/Singapore"))
    low = 0
    high = 0
    # 1. Flagdown
    low += 320
    high += 390
    # 2. Distance
    blocks = calcDistanceBlock(distance)
    low += 22 * blocks
    high += 25 * blocks
    # 3.Waiting Time
    ## TODO: Calc waiting time surcharge (same rate as above)
    # 4. Surcharges
    if isPeakPeriod(now):
        low *= 1.25
        high *= 1.25
    if isLateNight(now):
        low *= 1.5
        high *= 1.5
    return [int(low), int(high)]


def isPeakPeriod(now):
    today6am = now.replace(hour=6, minute=0, second=0, microsecond=0)
    today930am = now.replace(hour=9, minute=30, second=0, microsecond=0)
    today6pm = now.replace(hour=18, minute=0, second=0, microsecond=0)
    tmrw12am = now.replace(hour=23, minute=59, second=59, microsecond=999)

    dayOfWeek = datetime.datetime.today().weekday()
    # On weekdays
    if (0 <= dayOfWeek <= 4) and (
        (today6am < now < today930am) or (today6pm < now < tmrw12am)
    ):
        return True

    # On weekends
    if (5 <= dayOfWeek <= 6) and (today6pm < now < tmrw12am):
        return True

    return False


def isLateNight(now):
    today12am = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today6am = now.replace(hour=6, minute=0, second=0, microsecond=0)
    return today12am < now < today6am


def calcDistanceBlock(distance):
    """Calculates number of distance blocks"""
    # first 1km is free
    distance -= 1000
    if distance <= 0:
        return 0
    elif distance < 9000:
        result = distance // 400
    else:
        result = 9000 // 400
        result += (distance - 9000) // 350
    return result
