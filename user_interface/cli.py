# user_interface/cli.py

class CommandLineInterface:
    def __init__(self, manager):
        self.manager = manager

    async def start(self):
        while True:
            try:
                user_input = input(">>> ")
            except EOFError:
                print("EOFError encountered. Exiting gracefully...")
                break
            except KeyboardInterrupt:
                print("Interrupted by user. Exiting gracefully...")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                continue
            if user_input.lower() in ['exit', 'quit']:
                print("Exiting the CLI...")
                break
            await self.process_input(user_input)

    async def process_input(self, user_input):
        # Interpret and delegate tasks
        await self.manager.handle_user_request(user_input)