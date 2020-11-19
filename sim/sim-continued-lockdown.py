
import sys
if '..' not in sys.path:
    sys.path.append('..')

import random as rd
import pandas as pd
from lib.measures import *
from lib.experiment import Experiment, options_to_str, process_command_line
from lib.calibrationSettings import calibration_lockdown_beta_multipliers
from lib.calibrationFunctions import get_calibrated_params

TO_HOURS = 24.0

if __name__ == '__main__':

    name = 'continued-lockdown'
    random_repeats = 48
    full_scale = True
    verbose = True
    seed_summary_path = None
    set_initial_seeds_to = None

    # command line parsing
    args = process_command_line()
    config = args.config
    cpu_count = args.cpu_count

    # Load calibrated parameters up to `maxBOiters` iterations of BO
    maxBOiters = 40 if config.area in ['BE', 'JU', 'RH'] else None
    calibrated_params = get_calibrated_params(config=config,
                                              multi_beta_calibration=False,
                                              maxiters=maxBOiters)

    # experiment parameters
    # Continue lockdown for 'lockdown_weeks' number of weeks
    lockdown_weeks = [100, 4, 2]
    p_stay_home = calibrated_params['p_stay_home']

    # seed
    c = 0
    np.random.seed(c)
    rd.seed(c)

    # set simulation and intervention dates
    start_date = config.calibration_start_dates
    end_date = config.calibration_end_dates
    measure_start_date = config.calibration_lockdown_dates['start']
    measure_window_in_hours = dict()
    measure_window_in_hours['start'] = (pd.to_datetime(measure_start_date) - pd.to_datetime(start_date)).days * TO_HOURS
    measure_window_in_hours['end'] = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days * TO_HOURS

    # create experiment object
    experiment_info = f'{name}-{config.country}-{config.area}'
    experiment = Experiment(
        experiment_info=experiment_info,
        start_date=start_date,
        end_date=end_date,
        random_repeats=random_repeats,
        cpu_count=cpu_count,
        full_scale=full_scale,
        verbose=verbose,
    )

    # Continue lockdown for different time periods
    for weeks in lockdown_weeks:
        # measures
        max_days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days

        m = [
            SocialDistancingForAllMeasure(
                t_window=Interval(
                    measure_window_in_hours['start'], 
                    measure_window_in_hours['start'] + TO_HOURS * 7 * weeks),
                p_stay_home=p_stay_home),

            BetaMultiplierMeasureByType(
                t_window=Interval(
                    measure_window_in_hours['start'], 
                    measure_window_in_hours['start'] + TO_HOURS * 7 * weeks),
                beta_multiplier=calibration_lockdown_beta_multipliers)
            ]

        simulation_info = options_to_str(extended_lockdown_weeks=weeks)

        experiment.add(
            simulation_info=simulation_info,
            config=args.config,
            measure_list=m,
            lockdown_measures_active=False,
            test_update=None,
            seed_summary_path=seed_summary_path,
            set_calibrated_params_to=calibrated_params,
            set_initial_seeds_to=set_initial_seeds_to,
            full_scale=full_scale)
    print(f'{experiment_info} configuration done.')

    # execute all simulations
    experiment.run_all()

