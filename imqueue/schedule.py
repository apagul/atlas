import matplotlib.pyplot as plt
import numpy as np
import typing
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, get_sun

def schedule(target_list: [str]):
    """
    This function receives a list of target names and outputs a primary
    observable target
    
    Inputs:
    -------
    target_list :str: :list: List containing the names of the targets.
    
    Outputs:
    --------
    primary_target :str: Name of the highest priority target
    wait :astropy.Time: Wait time in seconds until optimal observation.
    It takes the value -1 when the object(s) is not observable.
    """
    
    max_altitude_time = {'target':[], 'altitude':[], 'time':[], 'wait':[]}   
     
    seo = EarthLocation(lat=38.2886*u.deg, lon=-122.50400*u.deg, height=60*u.m)    
    
    obs_time = Time.now()
    delta_obs_time = np.linspace(0, 18, 1000)*u.hour
    times = obs_time+delta_obs_time
    frame = AltAz(obstime=times, location=seo)
    
    sun_altaz = get_sun(times).transform_to(frame)
    sundown_time = times[np.where((sun_altaz.alt < -12*u.deg) == True)[0][0]]
    sunup_time = times[np.where((sun_altaz.alt < -12*u.deg) == True)[0][-1]]
    
    for target in target_list:
        max_altitude_time['target'].append(target)
        
        target_coordinates = SkyCoord.from_name(target)
        target_altaz = target_coordinates.transform_to(frame)
        if (np.max(target_altaz.alt)) > 40*u.degree:
            max_altitude_time['altitude'].append(np.max(target_altaz.alt))
        else:
            max_altitude_time['altitude'].append(0)
        
        aux_time = times[np.argmax(target_altaz.alt)]
        max_altitude_time['time'].append(aux_time)
        
        aux_delta_time = delta_obs_time[np.argmax(target_altaz.alt)]
        
        if (times[np.argmax(target_altaz.alt)] > sundown_time)& (times[np.argmax(target_altaz.alt)] < sunup_time):
            max_altitude_time['wait'].append(aux_delta_time.to(u.second))
        else:
            max_altitude_time['wait'].append('-1')
    
    primary_target = max_altitude_time['target'][np.argmin(Time(max_altitude_time['time'])-Time.now())]
    primary_target_id = np.argmin(Time(max_altitude_time['time'])-Time.now())
    return primary_target, max_altitude_time['wait'][primary_target_id]
