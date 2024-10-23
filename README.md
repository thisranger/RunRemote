
# RunRemote

`RunRemote` is a Python script designed to transfer files via SCP and execute a script on a remote SSH server. It is particularly useful for workflows like developing code on a local PC and seamlessly transferring it to a Raspberry Pi (or any other SSH-accessible server) for execution.

## SshMiniTerm

The `SshMiniTerm` module, inspired by `MiniTerm`, provides SSH terminal functionality specifically tailored for `RunRemote`. It handles the SSH connection and executes commands on the remote server.

## How to Use

You can either run the script interactively by executing:

```bash
python RunRemote.py
```

It will prompt you for all the required information.

Alternatively, you can provide all necessary arguments via the command line. For example:

```bash
python RunRemote.py -h Test -u this -s 1234 -i test.py -o '~\Documents\Test' -c "python test.py"
```

This will transfer the `test.py` file and execute it on the remote server using the specified command (`python test.py`).

**Note:**  
- The **output directory path** (`-o`) is surrounded by single quotes to prevent the shell from expanding `~`.
- The **command** (`-c`) is wrapped in double quotes to ensure it is executed properly in the specified directory.
- It should work on both Linux and Windows, though special keys might only work properly when connecting from Windows to Linux or Linux to Linux.
### Available Options

- `-h, --host TEXT`  
   The hostname or IP address of the SSH server.
  
- `-u, --username TEXT`  
   The SSH username for authentication.
  
- `-s, --password TEXT`  
   The SSH password for authentication.
  
- `-p, --port INTEGER`  
   The SSH port to connect to. (Default: 22)
  
- `-i, --input TEXT`  
   The local directory or file to transfer to the remote server.
  
- `-o, --outputDir TEXT`  
   The remote directory where files will be transferred.
  
- `-c, --command TEXT`  
   The command you want to run after the file transfer.
  
- `--help`  
   Displays this help message and exits.
