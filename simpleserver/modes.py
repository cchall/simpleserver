
class Job:
    def __init__(self, name, runfile, cores, priority=2, mode='distributed', command='python', **_unused):
        assert (mode == 'distributed') or (mode == 'serial'), "Run mode not understood"
        self.name = name
        self.runfile = runfile
        self.priority = priority
        self.mode = mode
        self.command = command
        self.cores = cores
        self.status = 0
        self.task = None
        self.starttime = None
        self.endtime = None
        self.directory = './test/'  # TODO: Put in setting to modify directory

        print("Temporary testing mpiexec used")
        self.base_string = "python monkey_program.py -n {cores} -h {id} {command} {runfile}"

    def simulation(self, *args):
        inputs_str = ''
        for arg in args:
            inputs_str += arg + ' '
        base_string = self.fill_string_parameters()
        run_string = base_string + inputs_str
        self.task = run_string

    def fill_string_parameters(self):
            return self.base_string.format(cores=self.cores,
                                           command=self.command,
                                           runfile=self.runfile,
                                           id='{id}')  # id is filled in by the Server at execution

    def _status(self):
        # Check status of tasks and assign from `job_status`
        # Need to set some sort of semaphore. Should be handled by server monitoring process output.
        pass
