# ArbitrageBot
Telegram bot for identifying bitcoin arbitrage opportunities

## Release Process

### New Release 
- Create a new tag. 
- Build the application using `setup.py` on WSL (Ubuntu 20.4)
- Push the built application to the [Arby](https://github.com/bl3e967/Arby.git) repo. 

### Running 
- SSH into Oracle production server. 
- Fetch the latest changes and checkout the new tag. 
- Test that the program works by running it. Execute `./Arby`. If you get a `permission denied` error, use `chmod u+x Arby` to make it executable. 
- Terminate the session. 

### Starting Arby Service 
- Go to `cd /lib/systemd/system` where the service execution script is defined in `arby.service`. 
- Execute `sudo systemctl start arby.service`
- Check the service has been started correctly: `sudo systemctl status arby.service`
- If the `arby.service` script is edited, `sudo systemctl daemon-reload` needs to be run to make `systemctl` reload the latest changes. 
