import ephem
import math
import datetime
from ics import Calendar, Event

def get_ecliptic_lon(body, date):
    body.compute(date)
    # Convert equatorial coordinates to ecliptic (Tropical Zodiac)
    ecl = ephem.Ecliptic(body)
    return math.degrees(ecl.lon)

def generate_transit_calendar():
    cal = Calendar()
    today = datetime.datetime.utcnow().date()
    
    planets = {
        'Mercury': ephem.Mercury(),
        'Venus': ephem.Venus(),
        'Mars': ephem.Mars(),
        'Jupiter': ephem.Jupiter(),
        'Saturn': ephem.Saturn()
    }
    
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
             
    for name, body in planets.items():
        prev_lon = get_ecliptic_lon(body, today)
        prev_sign = signs[int(prev_lon / 30) % 12]
        
        # Check initial movement to see if the planet is ALREADY retrograde today
        next_day = today + datetime.timedelta(days=1)
        next_lon = get_ecliptic_lon(body, next_day)
        init_diff = next_lon - prev_lon
        if init_diff > 180: init_diff -= 360
        elif init_diff < -180: init_diff += 360
        
        is_retrograde = init_diff < 0
        retrograde_start_date = today if is_retrograde else None
        
        for i in range(1, 365):
            current_date = today + datetime.timedelta(days=i)
            lon = get_ecliptic_lon(body, current_date)
            sign = signs[int(lon / 30) % 12]
            
            diff = lon - prev_lon
            # Adjust for the mathematical loop when crossing from 360 back to 0 degrees
            if diff > 180:
                diff -= 360
            elif diff < -180:
                diff += 360
                
            currently_retrograde = diff < 0
            
            # 1. State Change: Retrograde Begins
            if currently_retrograde and not is_retrograde:
                retrograde_start_date = current_date
                is_retrograde = True
                
                # Keep the single-day marker for easy spotting
                e_start = Event(name=f"🔄 {name} Retrograde Begins", begin=current_date)
                e_start.make_all_day()
                cal.events.add(e_start)
                
            # 2. State Change: Goes Direct (Creates the continuous block)
            elif not currently_retrograde and is_retrograde:
                is_retrograde = False
                
                # In .ics logic, the end date of an all-day event must be exclusive (the day after)
                end_date_exclusive = current_date + datetime.timedelta(days=1)
                
                # Generate the continuous multi-day block
                e_block = Event(
                    name=f"⏪ {name} is Retrograde", 
                    begin=retrograde_start_date, 
                    end=end_date_exclusive
                )
                e_block.make_all_day()
                cal.events.add(e_block)
                
                # Keep the single-day marker for when it ends
                e_end = Event(name=f"➡️ {name} Goes Direct", begin=current_date)
                e_end.make_all_day()
                cal.events.add(e_end)
                
            # 3. Log Zodiac Sign Changes (Transits)
            if sign != prev_sign:
                e = Event(name=f"🚪 {name} enters {sign}", begin=current_date)
                e.make_all_day()
                cal.events.add(e)
                
            prev_lon = lon
            prev_sign = sign
            
        # Clean-up: If a slower planet (like Saturn) is still retrograde at the end of 
        # our 365-day rolling window, we must close the block so it still renders on the calendar.
        if is_retrograde:
            end_date_exclusive = today + datetime.timedelta(days=366)
            e_block = Event(
                name=f"⏪ {name} is Retrograde", 
                begin=retrograde_start_date, 
                end=end_date_exclusive
            )
            e_block.make_all_day()
            cal.events.add(e_block)
            
    with open("planetary_transits.ics", "w") as f:
        f.writelines(cal.serialize_iter())

if __name__ == "__main__":
    generate_transit_calendar()
