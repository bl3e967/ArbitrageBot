# ArbitrageBot
Telegram bot for identifying bitcoin arbitrage opportunities

## Release Process
- Create a new tag. 
- Build the application using `setup.py` on WSL (Ubuntu 20.4)
- Push the built application to the [Arby](https://github.com/bl3e967/Arby.git) repo. 

- SSH into Oracle production server. 
- Fetch the latest changes and checkout the new tag. 
- execute `./Arby`. If you get a `permission denied` error, use `chmod u+x Arby' to make it executable. 
