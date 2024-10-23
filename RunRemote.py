import os
import tqdm
import click
from scp import SCPClient
from SshMiniTerm import SshMiniTerm, PrintInfo


# Function to calculate directory size
def GetDirSize(path):
    total = 0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += GetDirSize(entry.path)
    return total


# Progress bar class for file transfer
class ProgressBar:
    def __init__(self, amountOfFiles, totalSize=None):
        self.amountOfFiles = amountOfFiles
        self.totalSize = totalSize
        if self.amountOfFiles > 1:
            self.totalProgress = tqdm.tqdm(unit='B', unit_scale=True, total=self.totalSize, position=1, desc="File 1 of " + str(self.amountOfFiles))
        self.currentFile = ""
        self.fileProgress = None
        self.prvProgress = 0
        self.fileSend = 0

    def Progress(self, filename, size, sent):
        if self.currentFile != filename:
            if self.fileProgress is not None:
                self.fileProgress.close()
            self.prvProgress = 0
            self.currentFile = filename
            self.fileProgress = tqdm.tqdm(unit='B', unit_scale=True, total=size, position=0, desc=filename.decode('utf-8'))

            if self.amountOfFiles > 1:
                self.fileSend += 1
                self.totalProgress.set_description("File " + str(self.fileSend) + " of " + str(self.amountOfFiles))

        if self.amountOfFiles > 1:
            self.totalProgress.update(sent - self.prvProgress)

        self.fileProgress.update(sent - self.prvProgress)
        self.prvProgress = sent

    def Complete(self):
        if self.fileProgress is not None:
            self.fileProgress.close()
        if self.amountOfFiles > 1:
            self.totalProgress.close()


# Main function that handles arguments using Click and interactive prompts
@click.command(help="A simple script to transfer files via SCP and run a script on a remote SSH server.")
@click.option('--host', '-h', prompt="Enter SSH Hostname", help='The hostname or IP address of the SSH server.')
@click.option('--username', '-u', prompt="Enter SSH Username", help='The SSH username for authentication.')
@click.option('--password', '-s', prompt=True, hide_input=True, confirmation_prompt=False, help='The SSH password for authentication.')
@click.option('--port', '-p', default=22, type=int, help='The SSH port to connect to.')
@click.option('--input', '-i', type=str, prompt="Enter Directory or File which to transfer", help='The local directory or file to transfer to the remote server.')
@click.option('--output-dir', '-o', prompt="Enter Output Directory", help='The remote directory where files will be transferred.')
@click.option('--command', '-c', type=str, prompt="Enter Command to Run Remotely", help='The command you want to run after transfer.')
def main(host, username, password, port, input, output_dir, command):
    output_dir = output_dir.replace("\'", "").replace("\\", "/")

    # Establish an SSH connection using the provided parameters
    ssh_terminal = SshMiniTerm(host, username, password, port)
    ssh_terminal.Open()

    PrintInfo("Starting transfer:")

    # Set up the progress bar for file transfer
    if os.path.isdir(input):
        bar = ProgressBar(len(os.listdir(input)), GetDirSize(input))
    else:
        bar = ProgressBar(1)

    # Use SCPClient to transfer files
    with SCPClient(ssh_terminal.client.get_transport(), progress=bar.Progress) as scp:
        scp.put(input, output_dir, True)
        bar.Complete()

    # Flush and run the provided command on the remote server
    ssh_terminal.Send("cd " + output_dir + "\n")
    ssh_terminal.Flush()
    ssh_terminal.Send("\n" + command + "\n")
    ssh_terminal.RunTerminal()


if __name__ == "__main__":
    main()
