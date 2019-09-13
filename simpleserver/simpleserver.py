from subprocess import Popen, PIPE
from time import sleep, asctime, time
from os import chdir, mkdir
import numpy as np
import shutil
import socket
import signal
import logging
try:
    import mock
except ImportError:
    from unittest import mock
from threading import Thread
from parser import ParserSetup, ArgumentParserError
import modes

# TODO: Need to make sure folders go to where the client issued request (or the run file home)
# TODO: Warning if no servers are allocated
logging.basicConfig(filename='example.log',level=logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

job_status = {-1: 'FAILED',
              0: 'WAITING',
              1: 'STARTED',
              2: 'COMPLETE'}


class JobServer:
    def __init__(self):
        self.job_list = []  # Jobs waiting to run
        self._running_jobs = []  # Jobs currently running
        self.server_list = {}
        self.folders = {}  # TODO: May not need this
        self._output_buffer = {}  # Store messages to be sent to clients

        self.buf_stash = []  # Stores commands clients have sent to server
        self.threads = []
        self.stop_listen = False  # Stop listener thread (terminate server)
        self.job_count = 1

        # Begin Server Startup
        signal.signal(signal.SIGINT, self.signal_handler)

        # Start parser
        self._parse()

        # Start server monitor
        self.server_monitor_thread = Thread(target=self._server_monitor)
        self.server_monitor_thread.daemon = True
        self.server_monitor_thread.start()

        # start job launcher
        sleep(0.25)  # Pause to offset thread cycles
        self.job_launcher_thread = Thread(target=self._job_launcher)
        self.job_launcher_thread.daemon = True
        self.job_launcher_thread.start()

        # Start listener
        self.communicator_thread = Thread(target=self._communicator, args=(self.stop_listen,))
        self.communicator_thread.start()

    def _communicator(self, stop):
        """
        Starts thread to listen for commands from a client.
        """
        self.MAX_LENGTH = 4096
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.PORT = 10000
        self.HOST = '127.0.0.1'

        self.serversocket.bind((self.HOST, self.PORT))
        self.serversocket.listen(2)
        while 1:
            clientsocket, address = self.serversocket.accept()
            self._output_buffer[clientsocket] = ''
            self.client_requests = Thread(target=self._handle_receiver, args=(clientsocket,))
            self.client_requests.start()
            self.client_messages = Thread(target=self._handle_sender, args=(clientsocket,))
            self.client_messages.start()
            # self.threads.append(self.client_requests)

    def _parse(self):
        """
        Starts thread that will parse requests received from a client.
        """
        self.parser = ParserSetup
        self.parsing_handler = Thread(target=self._buf_handler)
        self.parsing_handler.daemon = True
        self.parsing_handler.start()
        self.threads.append(self.parsing_handler)

    def _handle_receiver(self, clientsocket):
        """
        Manages incoming messages from the client socket and passes them to JobServer for execution
        """
        while 1:
            # Receiver
            buf = clientsocket.recv(self.MAX_LENGTH)
            if len(buf) == 0:
                # End receiving and cleanup
                sleep(0.001)
                logging.info('Communication with handler {} terminated'.format(clientsocket))

                # Cleanup output buffer
                self._output_buffer.pop(clientsocket)
                break

            print("Buffer received: {}".format(buf))
            self.buf_stash.append(buf)

    def _handle_sender(self, clientsocket):
        """
        Checks for messages to be sent to client and sends them
        """
        while 1:
            # Sender

            # print('mailbox of', clientsocket, self._output_buffer[clientsocket])
            try:
                # Check socket is still open and registered
                self._output_buffer[clientsocket]
            except KeyError:
                break

            if self._output_buffer[clientsocket]:
                clientsocket.send(self._output_buffer[clientsocket])
                self._output_buffer[clientsocket] = ''

            sleep(1.75)

    def _buf_handler(self):
        """
        Initial any server actions in a buffer from a client.
        :return:
        """
        while 1:
            if len(self.buf_stash) > 0:
                task = self.buf_stash.pop().decode('utf-8')
                with mock.patch('sys.argv', ['', ] + task.split()):
                    try:
                        args = self.parser()
                        getattr(self, args().server_action)(args())
                    except ArgumentParserError as e:
                        self._messenger('input was not understood: {}'.format(task))
            sleep(4)

    def _server_monitor(self):
        """
        Checks servers and changes status of servers and jobs when appropriate
        """
        while 1:
            for server in self.server_list.values():
                server.cleanup_tasks()

            sleep(3)

    def _job_launcher(self):
        # Starts new jobs and invokes job order management routines
        while 1:
            # Launch all jobs available that will fit
            for candidate, job in self._job_selector():
                job_status = candidate.launch_task(job)
                if job_status == -1:
                    self._messenger("Job {name} could not be started".format(name=job.name))
                else:
                    job.status = job_status
                logging.info("Job {name} launched on Server {id}".format(name=job.name, id=candidate.id))
            # Perform cleanup of job list
            job_holding = []
            for job in self.job_list:
                if job.status == 1:
                    self._running_jobs.append(job)
                else:
                    job_holding.append(job)
            self.job_list = list(job_holding)

            # TODO: Need to clean up running_job list

            sleep(3)

    def _job_selector(self):
        # Determines which job should be assigned to an open server
        for job in self.job_list:
            # Find server with least number of cores that will still fit the job
            candidate = None
            candidate_cores = job.cores
            print('jcores', candidate_cores)
            for server in self.server_list.values():
                print('server has', server.id, server.free_cores)
                if candidate_cores <= server.free_cores:
                    candidate = server
                    candidate_cores = server.free_cores
            if candidate is not None:
                yield candidate, job

    def job_commissar(self):
        # Maintains order in job ranks
        # TODO: First just move all priority 1 jobs to start

        pass

    def add_server(self, parser):
        # Add server to pool
        id = parser.id
        if id not in self.server_list:
            self.server_list[id] = Server(id)
            self._messenger("Added server ID: {}".format(id))
        else:
            self._messenger("ID \'{}\' already exists".format(id))

    def stop_server(self, parser):
        # Stop a server, remove current output, reassign point
        assert parser.id in self.server_list, "ID \'{}\' is not being used by the server".format(parser.id)
        server = self.server_list[parser.id]

        server.kill(parser.remove_output)

    def remove_server(self, parser):
        # Remove server from pool, don't cancel any current job running on it
        assert parser.id in self.server_list, "ID \'{}\' is not being used by the server".format(parser.id)
        self.server_list.pop(parser.id)
        print("Server {} removed from pool. Job will finish without monitoring.".format(parser.id))

    def simulation(self, parser):
        new_job = modes.Job(**{key: getattr(parser, key) for key in vars(parser)})
        new_job.simulation(*parser.args)
        new_job.job_id = self.job_count
        self.job_count += 1
        self.job_list.append(new_job)
        logging.info("New job posted: {name} {cores}".format(name=parser.name, cores=parser.cores))
        self._messenger("New job posted: {name}".format(name=parser.name))

    def scan(self, parser):
        args = parser.args
        points = []
        for arg in args:
            points.append(np.linspace(*arg))
        mesh = np.meshgrid(*points)
        mesh = [m.ravel() for m in mesh]

        for vals in zip(*mesh):
            new_job = modes.Job(**{key: getattr(parser, key) for key in vars(parser)})
            new_job.simulation(*vals)
            self.job_list.append(new_job)

    def server_report(self, parser):

        for id in parser.ids:
            if id == 0:
                # default, print status of all servers
                for i in sorted([id for id in self.server_list.keys()]):
                    self._messenger(self.server_list[i].server_report())
                break
            else:
                try:
                    self._messenger(self.server_list[id].server_report())
                except KeyError:
                    self._messenger("Server {} is not registered".format(id))

    def job(self, parser):
        """
        Perform actions on currently running or queued jobs.
        :param parser:
        :return:
        """
        if parser.stop_job_id:
            self.stop_job(parser.stop_job_id)

    def stop_job(self, job_id):
        for job in self.job_list:
            if job.job_id == job_id:
                self.job_list.remove(job)
                report = "Job {id} was removed from the queue.".format(id=job_id)
                self._messenger(report)
            else:
                # Job is running, will need to stop process
                for server in self.server_list:
                    for proc, job in server.jobs.items():
                        if job.job_id == job_id:
                            proc.kill()
                            server.cleanup_tasks()
                            report = "Job {id} was stopped.".format(id=job_id)
                            self._messenger(report)

    def _messenger(self, message):
        # Since I didn't create a way to tie server commands to the client that sent them
        #  all messages are broadcast to all open sockets right now
        for socket, mailbox in self._output_buffer.items():
            self._output_buffer[socket] += message + '\n'

    def _exit(self):
        # Need to nicely disconnect sockets and end threads
        self.serversocket.close()

    def signal_handler(self, sig, frame):
        print('You pressed Ctrl+C!')
        self._exit()
        exit(0)


class Server:
    def __init__(self, id, folder=None):
        self.id = id
        self.creation = asctime()
        self._start = time()
        self.busytime = 0  # TODO: find a good way to log this
        self.folder = folder
        self.cores = self._core_count()
        self.free_cores = self.cores
        self.jobs = {}

    @property
    def uptime(self):
        return time() - self._start

    def _core_count(self):
        try:
            cpus = Popen("""rsmpi -n 1 -h {} python3 -c "from multiprocessing import cpu_count; print(cpu_count())" """.format(id),
                         shell=True, stdout=PIPE, stderr=PIPE)
            return int(cpus.communicate()[0]) // 2
        except ValueError:
            print("Failed to find core count\nAssuming testing mode and assigning 20")
            return 20

    def kill(self, remove_output):
        print("dummy: Server was killed")
        if remove_output:
            self.remove_output()

    def remove_output(self):  # TODO: Move this, folders shouldn't be tied to servers
        try:
            shutil.rmtree(self.folder)
        except OSError as e:
            print("Could not remove {}\n\n {}".format(self.folder, e))

    def launch_task(self, job):
        try:
            chdir(job.file_path)
        except OSError as e:
            logging.error('Could not change directory to: {}'.format(job.file_path))
            return -1

        self.free_cores -= job.cores
        change_directory = Popen('cd {}'.format(job.directory), shell=True)
        change_directory.wait()
        self.jobs[Popen(job.task.format(id=self.id), shell=True)] = job
        job.starttime = time()

        return 1

    def cleanup_tasks(self):
        process_cleanup = []
        for process in self.jobs.keys():
            if process.poll() is not None:
                # Job no longer running, free up cores
                self.free_cores += self.jobs[process].cores
                # Cleanup for job completion
                self.jobs[process].status = process.poll()
                process_cleanup.append(process)

                process.endtime = time()

        for process in process_cleanup:
            self.jobs.pop(process)

    def server_report(self):
        report  = "Report: Server {}\n".format(self.id)
        report += "Registered on {}\n".format(self.creation)
        report += "Usage: {} out of {} hours, {}% occupation\n".format(self.busytime,
                                                                       self.uptime / 60. / 60.,
                                                                       self.busytime / self.uptime * 100)
        report += "{} Jobs Running\n".format(len(self.jobs))
        for i, job in enumerate(self.jobs.values()):
            report += "{}. {}: {}s on {} cores -- {}\n".format(i, job.name, time() - job.starttime, job.cores, job.task)

        return report


if __name__ == '__main__':
    server = JobServer()


