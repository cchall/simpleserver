from threading import Thread


class Job:
    def __init__(self, name, runfile, cores, priority=2, mode='distributed', command='python2', **_unused):
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
        self.process = None
        self.file_path = '.'  # TODO: Put in setting to modify directory

        self.debug = True

        if self.debug:
            print("Temporary testing mpiexec used")
            self.base_string = "python monkey_program.py -n {cores} -h {id} {command} {runfile}"
            self.base_string = "{command} {runfile} -n {cores} -h {id}"
        else:
            self.base_string = "rsmpi -n {cores} -h {id} {command} {runfile}"

    def simulation(self, *args):
        inputs_str = ' '
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

    def record(self):
        writer_thread = Thread(target=self._stream_writer)
        writer_thread.daemon = True
        writer_thread.start()

    def _stream_writer(self):
        with open(self.name + '.log', 'w') as ff:
            while True:
                line = self.process.stdout.readline()
                ff.write(line)
                if line == '' and self.process.poll() != None:
                    try:
                        line = self.process.stderr.readlines()
                        ff.write(line)
                    except:
                        pass
                    break

    def _status(self):
        # Check status of tasks and assign from `job_status`
        # Need to set some sort of semaphore. Should be handled by server monitoring process output.
        pass
