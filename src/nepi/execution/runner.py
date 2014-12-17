#
#    NEPI, a framework to manage network experiments
#    Copyright (C) 2013 INRIA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Alina Quereilhac <alina.quereilhac@inria.fr>

from nepi.execution.ec import ExperimentController, ECState

import math
import numpy
import os
import time

class ExperimentRunner(object):
    """ The ExperimentRunner entity is responsible of
    re-running an experiment described by an ExperimentController 
    multiple time

    """
    def __init__(self):
        super(ExperimentRunner, self).__init__()
    
    def run(self, ec, min_runs = 1, max_runs = -1, wait_time = 0, 
            wait_guids = [], compute_metric_callback = None, 
            evaluate_convergence_callback = None ):
        """ Run a same experiment independently multiple times, until the 
        evaluate_convergence_callback function returns True

        :param ec: Description of experiment to replicate. 
            The runner takes care of deploying the EC, so ec.deploy()
            must not be invoked directly before or after invoking
            runner.run().
        :type ec: ExperimentController

        :param min_runs: Minimum number of times the experiment must be 
            replicated
        :type min_runs: int

        :param max_runs: Maximum number of times the experiment can be 
            replicated
        :type max_runs: int

        :param wait_time: Time to wait in seconds on each run between invoking
            ec.deploy() and ec.release().
        :type wait_time: float

        :param wait_guids: List of guids wait for finalization on each run.
            This list is passed to ec.wait_finished()
        :type wait_guids: list 

        :param compute_metric_callback: User defined function invoked after 
            each experiment run to compute a metric. The metric is usually
            a network measurement obtained from the data collected 
            during experiment execution.
            The function is invoked passing the ec and the run number as arguments. 
            It must return the value for the computed metric(s) (usually a single 
            numerical value, but it can be several).

                metric = compute_metric_callback(ec, run)
            
        :type compute_metric_callback: function 

        :param evaluate_convergence_callback: User defined function invoked after
            computing the metric on each run, to evaluate the experiment was
            run enough times. It takes the list of cumulated metrics produced by 
            the compute_metric_callback up to the current run, and decided 
            whether the metrics have statistically converged to a meaningful value
            or not. It must return either True or False. 

                stop = evaluate_convergence_callback(ec, run, metrics)

            If stop is True, then the runner will exit.
            
        :type evaluate_convergence_callback: function 

        """

        if (not max_runs or max_runs < 0) and not compute_metric_callback:
            msg = "Undefined STOP condition, set stop_callback or max_runs"
            raise RuntimeError, msg

        if compute_metric_callback and not evaluate_convergence_callback:
            evaluate_convergence_callback = self.evaluate_normal_convergence
            ec.logger.info(" Treating data as normal to evaluate convergence. "
                    "Experiment will stop when the standard error with 95% "
                    "confidence interval is >= 5% of the mean of the collected samples ")
        
        # Force persistence of experiment controller
        ec._persist = True

        filepath = ec.save(dirpath = ec.exp_dir)

        samples = []
        run = 0
        stop = False

        while not stop: 
            run += 1

            ec = self.run_experiment(filepath, wait_time, wait_guids)
            
            ec.logger.info(" RUN %d \n" % run)

            if compute_metric_callback:
                metric = compute_metric_callback(ec, run)
                if metric is not None:
                    samples.append(metric)

                    if run >= min_runs and evaluate_convergence_callback:
                        if evaluate_convergence_callback(ec, run, samples):
                            stop = True

            if run >= min_runs and max_runs > -1 and run >= max_runs :
                stop = True

            ec.shutdown()
            del ec

        return run

    def evaluate_normal_convergence(self, ec, run, metrics):
        """ Returns True when the confidence interval of the sample mean is
        less than 5% of the mean value, for a 95% confidence level,
        assuming normal distribution of the data
        """

        if len(metrics) == 0:
            msg = "0 samples collected"
            raise RuntimeError, msg

        x = numpy.array(metrics)
        n = len(metrics)
        std = x.std()
        se = std / math.sqrt(n)
        m = x.mean()

        # Confidence interval for 95% confidence level, 
        # assuming normally distributed data.
        ci95 = se * 2
        
        ec.logger.info(" RUN %d - SAMPLES %d MEAN %.2f STD %.2f CI (95%%) %.2f \n" % (
            run, n, m, std, ci95 ) )

        return m * 0.05 >= ci95

    def run_experiment(self, filepath, wait_time, wait_guids):
        """ Run an experiment based on the description stored
        in filepath.

        """
        ec = ExperimentController.load(filepath)

        ec.deploy()
    
        ec.wait_finished(wait_guids)
        time.sleep(wait_time)

        ec.release()

        if ec.state == ECState.FAILED:
            raise RuntimeError, "Experiment failed"

        return ec

