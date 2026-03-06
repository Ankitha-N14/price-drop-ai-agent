def price_decision(current,last):

    if last == 0:
        return "Monitoring"

    drop = last - current

    percent = (drop / last) * 100

    if percent > 20:
        return "BUY NOW - Big drop"

    elif percent > 10:
        return "GOOD DEAL - Consider buying"

    elif percent > 5:
        return "WAIT - Might drop more"

    else:
        return "HOLD - Price stable"
