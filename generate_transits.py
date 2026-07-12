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
    
    # Tracking the primary visible planets used in traditional magick
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
        # Get baseline starting position
        prev_lon = get_ecliptic_lon(body, today)
        prev_sign = signs[int(prev_lon / 30) % 12]
        is_retrograde = False 
        
        for i in range(1, 365):
            current_date = today + datetime.timedelta(days=i)
            lon = get_ecliptic_lon(body, current_date)
            sign = signs[int(lon / 30) % 12]
            
            # Calculate daily movement to check for backward (retrograde) motion
            diff = lon - prev_lon
            # Adjust for the mathematical loop when crossing from 360 back to 0 degrees
            if diff > 180:
                diff -= 360
            elif diff < -180:
                diff += 360
                
            currently_retrograde = diff < 0
            
            # 1. Log Retrograde / Direct Stations
            if currently_retrograde and not is_retrograde:
                e = Event(name=f"🔄 {name} Retrograde Begins", begin=current_date)
                e.make_all_day()
                cal.events.add(e)
                is_retrograde = True
            elif not currently_retrograde and is_retrograde:
                e = Event(name=f"➡️ {name} Goes Direct", begin=current_date)
                e.make_all_day()
                cal.events.add(e)
                is_retrograde = False
                
            # 2. Log Zodiac Sign Changes (Transits)
            if sign != prev_sign:
                e = Event(name=f"🚪 {name} enters {sign}", begin=current_date)
                e.make_all_day()
                cal.events.add(e)
                
            # Save current position to compare against tomorrow
            prev_lon = lon
            prev_sign = sign
            
    with open("planetary_transits.ics", "w") as f:
        f.writelines(cal.serialize_iter())

if __name__ == "__main__":
    generate_transit_calendar()
