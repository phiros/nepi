from nepi.execution.resource import ResourceManager, clsinit_copy, \
     ResourceState, reschedule_delay
from nepi.resources.iotlab.node import IOTLABNode
from nepi.execution.attribute import Attribute, Flags
from nepi.resources.iotlab.iotlab_api_factory import IOTLABAPIFactory


@clsinit_copy
class IOTLABApplication(ResourceManager):
    """
    .. class:: Class Args :
      
        :param ec: The Experiment controller
        :type ec: ExperimentController
        :param guid: guid of the RM
        :type guid: int

    """
    _rtype = "IOTLABApplication"
    _authorized_connections = ["IOTLABNode"]

    @classmethod
    def _register_attributes(cls):
        """ Register the attributes of a Firmware application

        """
        command = Attribute("command", "Command to execute",
        	flags = Flags.Design)
        firmware_path = Attribute("firmware_path", "Firmware file path",
        	flags = Flags.Design)
        cls._register_attribute(command)
        cls._register_attribute(firmware_path)
        
    def __init__(self, ec, guid):
        """
        :param ec: The Experiment controller
        :type ec: ExperimentController
        :param guid: guid of the RM
        :type guid: int
        """
        super(IOTLABApplication, self).__init__(ec, guid)
        self._rest_api = None

    @property
    def exp_id(self):
        return self.ec.exp_id

    @property
    def node(self):
        rm_list = self.get_connected(IOTLABNode.get_rtype())
        if rm_list: return rm_list[0]
        return None

    def do_deploy(self):
        """ Deploy the RM.
        """
        node = self.node
        if not node or node.state < ResourceState.READY:
            self.debug("---- RESCHEDULING DEPLOY ---- node state %s "
                       % node.state )
            self.ec.schedule(reschedule_delay, self.deploy)
        else: 
            if not self.get('command'):
            	msg = "Command is not initialized."
            	self.error(msg)
            	raise RuntimeError(msg)

            if (self.get('command') == 'update' and 
            	not self.get('firmware_path')):
            	msg = "Firmware path is not initialized."
            	self.error(msg)
            	raise RuntimeError(msg)

            if not self._rest_api :
                self._rest_api = IOTLABAPIFactory.get_api(node.get('username'),
                 	node.get('password'), node.get('hostname'), exp_id = self.exp_id)

            super(IOTLABApplication, self).do_deploy()

    def do_start(self):
        """ Start the RM. It means : Send REST Request to execute
        command. 
        """
        if self.get('command') == 'update':
            self._rest_api.update(self.get('firmware_path'))
        elif self.get('command') == 'start':
			self._rest_api.start()
        elif self.get('command') == 'stop':
			self._rest_api.stop()
        elif self.get('command') == 'reset':
			self._rest_api.reset()
        else:
            msg = "Command is unknown."
            self.error(msg)
            raise RuntimeError(msg)

        super(IOTLABApplication, self).do_start()


