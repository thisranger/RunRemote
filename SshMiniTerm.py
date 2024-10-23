import paramiko
import threading
import sys
import time
import platform
import colorama
import click
import re

if platform.system() == "Windows":
    import msvcrt  # For Windows keyboard input handling
else:
    import termios
    import tty

windowsToLinuxKeys = {
    '0x48': '\x1b[A',    # Up Arrow
    '0x50': '\x1b[B',    # Down Arrow
    '0x4b': '\x1b[D',    # Left Arrow
    '0x4d': '\x1b[C',    # Right Arrow
    '0x47': '\x1b[H',    # Home
    '0x4f': '\x1b[F',    # End
    '0x49': '\x1b[5~',   # Page Up
    '0x51': '\x1b[6~',   # Page Down
    '0x52': '\x1b[2~',   # Insert
    '0x53': '\x1b[3~',   # Delete
    '0x3b': '\x1b[11~',  # F1
    '0x3c': '\x1b[12~',  # F2
    '0x3d': '\x1b[13~',  # F3
    '0x3e': '\x1b[14~',  # F4
    '0x3f': '\x1b[15~',  # F5
    '0x40': '\x1b[16~',  # F6
    '0x41': '\x1b[17~',  # F7
    '0x42': '\x1b[18~',  # F8
    '0x43': '\x1b[19~',  # F9
    '0x44': '\x1b[20~',  # F10
    '0x57': '\x1b[21~',  # F11
    '0x58': '\x1b[22~',  # F12
    '0x0f': '\x1b[Z',    # Shift + Tab
}

# Color output functions using colorama
def PrintError(error):
    print(colorama.Fore.RED + error + colorama.Fore.RESET)


def PrintWarning(warning):
    print(colorama.Fore.YELLOW + warning + colorama.Fore.RESET)


def PrintInfo(info):
    print(colorama.Fore.GREEN + info + colorama.Fore.RESET)


class SshMiniTerm:
    def __init__(self, host: str, username: str, password: str, port: int = 22):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.shell = None
        self.running = False

        colorama.init()  # Initialize colorama for cross-platform color support

    def Open(self):
        """Open an SSH connection and interactive shell."""
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.client.connect(self.host, port=self.port, username=self.username, password=self.password)
            self.shell = self.client.invoke_shell()
            PrintInfo(f"Connected to {self.host}:{self.port}. You are now in an interactive SSH session. Press Ctrl+] to close.")
        except Exception as e:
            PrintError(f"Failed to connect to {self.host}:{self.port} - {str(e)}")
            sys.exit(1)

    def Close(self):
        """Close the SSH connection."""
        if self.client:
            self.client.close()
            PrintWarning("\nConnection closed.")

    def Send(self, command: str):
        self.shell.send(command)

    def Flush(self):
        end_time = time.time() + 0.5  # 1 second from now
        while time.time() < end_time:
            try:
                if self.shell.recv_ready():
                    _ = self.shell.recv(1024)  # Read and discard
            except Exception as e:
                PrintError(f"Error while discarding data: {str(e)}")

    def PrintServerOutput(self):
        """Read from SSH server and print output with colorized prompt and path."""
        if not self.client:
            return

        while self.running:
            try:
                if self.shell.recv_ready():
                    output = self.shell.recv(1024).decode("utf-8")
                    if not output:
                        PrintWarning("\nConnection closed by the server.")
                        self.StopTerminal()
                        break

                    # Regex to match \x1b[?2004h, the username@hostname, path, and $
                    prompt_regex = r"((?=(\x1b\[\?2004h))(.*?)@(.*?))(?=\:) \: (?<=\:)(.*?)(?<=\$)"

                    # Function to colorize the matched parts
                    def colorize_prompt(match):
                        user = f"{colorama.Fore.GREEN}{match.group(1)}{colorama.Fore.RESET}"  # Bracketed sequence
                        path = f"{colorama.Fore.BLUE}{match.group(5)}{colorama.Fore.RESET}"  # Path
                        return user + ':' + path

                    # Apply the colorization using regex substitution
                    output = re.sub(prompt_regex, colorize_prompt, output, flags=re.VERBOSE)

                    # Print the colorized output
                    sys.stdout.write(output)
                    sys.stdout.flush()
                time.sleep(0.1)
            except Exception as e:
                PrintWarning(f"Error in receiving data: {str(e)}")

    def SendTerminalInput(self):
        if not self.client:
            return

        """Send input to SSH server."""
        while self.running:
            try:
                if platform.system() == "Windows":
                    if msvcrt.kbhit():
                        user_input = msvcrt.getwch()

                        if user_input == '\x1d':  # Ctrl+]
                            PrintWarning("\nCtrl+] pressed, stopping SSH session.")
                            self.StopTerminal()

                        elif user_input == '\xe0':
                            user_input = msvcrt.getwch()

                            if windowsToLinuxKeys.__contains__(hex(ord(user_input))):
                                self.shell.send(windowsToLinuxKeys[hex(ord(user_input))])
                            else:
                                PrintWarning("Unknown command" + hex(ord(user_input)))
                        else:
                            self.shell.send(user_input)
                else:
                    user_input = sys.stdin.read(1)

                    if user_input == '\x1d':  # Detect Ctrl+]
                        PrintWarning("\nCtrl+] pressed, stopping SSH session.")
                        self.StopTerminal()
                    else:
                        self.shell.send(user_input)

            except OSError as e:
                PrintError("OSError:" + str(e))
                self.StopTerminal()

    def RunTerminal(self):
        """Start the interactive terminal."""
        self.running = True
        if not self.client:
            self.Open()

        # Start a thread to read from the SSH server.
        read_thread = threading.Thread(target=self.PrintServerOutput)
        read_thread.daemon = True
        read_thread.start()
        while self.running:
            try:
                if platform.system() == "Windows":
                    self.SendTerminalInput()
                else:
                    # Configure terminal for raw input on Unix-like systems.
                    old_tty_settings = termios.tcgetattr(sys.stdin)
                    try:
                        tty.setraw(sys.stdin)
                        self.SendTerminalInput()
                    finally:
                        # Restore terminal settings on exit.
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tty_settings)
            except KeyboardInterrupt:
                if self.shell:
                    self.shell.send('\x03')  # Send Ctrl+C to SSH session

    def StopTerminal(self):
        """Stop the SSH session and cleanup."""
        self.running = False
        self.Close()


@click.command(help="A simple SSH terminal emulator that connects to a remote server.")
@click.option('--host', '-h', prompt="Enter SSH Hostname", help='The hostname or IP address of the SSH server.')
@click.option('--username', '-u', prompt="Enter SSH Username", help='The SSH username for authentication.')
@click.option('--password', '-s', prompt=True, hide_input=True, confirmation_prompt=False, help='The SSH password for authentication.')
@click.option('--port', '-p', default=22, help='The SSH port to connect to.')
def main(host, username, password, port):
    SshMiniTerm(host, username, password, port).RunTerminal()


if __name__ == "__main__":
    main()
