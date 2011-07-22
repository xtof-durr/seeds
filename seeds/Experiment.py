# -*- coding: utf-8 -*-
""" The Experiment encompasses all aspects of the experiment. It maintains the
Actions, Resources, Cells, the configuration, and time.

"""

__author__ = "Brian Connelly <bdc@msu.edu>"
__credits__ = "Brian Connelly"

import os
import random
import sys
import time
import uuid

import seeds
from seeds.ActionManager import *
from seeds.Cell import *
from seeds.Config import *
from seeds.PluginManager import *
from seeds.Population import *
from seeds.Resource import *
from seeds.SEEDSError import *
from seeds.Topology import *

class Experiment(object):
    """
    The Experiment object captures the state of a experiment

    Properties:

    action_manager
        An ActionManager object which manages all Actions in the experiment
    config
        A Config object storing the configuration for the experiment
    data
        A dict that can be used to store additional data.  For example, see the
        'type_count' value, which is used to store the counts of different cell
        types (for cells that have different types) across the population.
        This is faster than scanning the population whenever this information
        is needed.
    epoch
        An integer storing the current epoch (unit of time)
    plugin_manager
        A PluginManager object which manages all Plugins for the experiment
    population
        A Population object that keeps information about the Cells (organisms)
        and their interactions
    proceed
        Boolean value indicating whether or not the experiment should continue.
    resources
        A hash of available resources.  The key is the name of the resource,
        and the value is a Resource object.
    uuid
        A practically unique identifier for the experiment. (RFC 4122 ver 4)

    """

    def __init__(self, configfile=None, seed=-1):
        """Initialize a Experiment object

        Parameters:

        *configfile*
            Name of configuration file for the experiment.  If none is
            provided, the experiment will either use defaults for all
            parameters or values provided to the Config object elsewhere (e.g.,
            through the command-line or GUI program).
        *seed*
            Seed for pseudorandom number generator.  If undefined, the current
            time will be used.

        """

        self.config = Config(experiment=self, filename=configfile)
        self.epoch = 0
        self.is_setup = False
        self.proceed = True
        self.seed = seed
        self.uuid = uuid.uuid4()
        self.data = {}
        self.resources = {}

        if not self.config.has_section("Experiment"):
            raise ConfigurationError("Configuration section '%s' not defined" % ("Experiment"))

    def setup(self):
        """Set up the Experiment including its Actions, Topologies, and Cells"""
        if self.seed == -1:
            configseed = self.config.getint('Experiment', 'seed', default=-1)
            if configseed != -1:
                self.seed = configseed
            else:
                self.seed = int(time.time()*10)

        random.seed(self.seed)
        self.config.set('Experiment', 'seed', self.seed)

        self.experiment_epochs = self.config.getint('Experiment', 'epochs',
                                                    default=-1)

        # Create a plugin manager.  Append the system-wide plugins
        # to the list of plugin sources.
        self.plugin_manager = PluginManager(self)
        global_plugin_path = os.path.join(os.path.dirname(seeds.__file__), "plugins")
        for d in ["cell", "topology", "action", "resource"]:
            plugin_path = os.path.join(global_plugin_path, d)
            self.plugin_manager.append_dir(plugin_path)


        # Initialize all of the Resources
        self.data['resources'] = {}
        resourcestring = self.config.get("Experiment", "resources")
        if resourcestring:
            reslist = [res.strip() for res in resourcestring.split(',')]

            for res in reslist:
                sec = "Resource:%s" % (res)
                if not self.config.has_section(sec):
                    raise ConfigurationError("No configuration for resource '%s'" % (res))

                r = Resource(experiment=self, label=res)

                if r.name not in self.resources:
                    self.resources[r.name] = r
                else:
                    print "Warning: Resource '%s' listed twice.  Skipping duplicates." % (res)

        # Create the Population
        self.data['population'] = {}

        population_raw = self.config.get("Experiment", "population", default="Population")
        parsed = population_raw.split(':')

        if parsed[0] != "Population":
            print "ERROR: pop name must be 'population'" # TODO: throw a configerror

        if len(parsed) > 1:
            poplabel = parsed[1]
        else:
            poplabel = None

        try:
            self.population = Population(experiment=self, label=poplabel)
        except TopologyPluginNotFoundError as err:
            raise TopologyPluginNotFoundError(err.topology)
        except CellPluginNotFoundError as err:
            raise CellPluginNotFoundError(err.cell)

        self.action_manager = ActionManager(experiment=self)
        self.is_setup = True

    def update(self):
        """Update the Experiment and all of its objects"""
        if not self.is_setup:
            self.setup()

        self.action_manager.update()	# Update the actions
        [self.resources[res].update() for res in self.resources]
        self.population.update()
        self.epoch += 1

        # If we've surpassed the configured number of epochs to run for, set
        # proceed to false
        if self.experiment_epochs != -1 and self.epoch >= self.experiment_epochs:
            self.proceed = False

    def __iter__(self):
        """Experiment is an iterator, so it can be used with commands such as

        e = Experiment(....)
        for epoch in e:
            print "Updated Experiment.  Now at epoch %d" % (epoch)
        """

        return self

    def next(self):
        """Proceed with the experiment.  Update the Experiment and return the current epoch"""
        if not self.proceed:
            raise StopIteration
        else:
            self.update()
            return self.epoch

    def end(self):
        """Set the experiment to end after this epoch"""
        self.proceed = False

    def teardown(self):
        """Perform any necessary cleanup at the end of a run"""
        self.action_manager.teardown()
        [self.resources[res].teardown() for res in self.resources]
        self.population.teardown()

    def is_resource_defined(self, name):
        """Helper function to determine whether a given resource has been
        defined or not
        """

        return self.resources.has_key(name)

    def get_resource(self, name):
        """Helper function to get the Resource object with the given name.  If
        the resource is not defined, ResourceNotDefinedError is thrown.
        """

        try:
            r = self.resources[name]
            return r
        except KeyError:
            raise ResourceNotDefinedError(name)
