import os 
import platform

from cmd_chat.client.core.abs.abs_renderer import ClientRenderer
from cmd_chat.client.config import COLORS

from colorama import init

init()


class DefaultClientRenderer(ClientRenderer):

    def __get_os(self) -> str:
        """ checking what kind of platform you need
        """
        if "Linux" in str(platform.platform()):
            return "Linux"
        return "Windows"

    def print_message(self, message: str) -> str:
        """ generating string with message in required format
        """
        message = message.split(":")
        if message[0] == self.username:
            return COLORS["my_username_color"] + message[0] + ": " + message[1] + COLORS["text_color"]
        return message[0] + ": " + message[1] + COLORS["text_color"]

    def clear_console(self):
        # For windows clear command its cls
        # For linux clear command its clear
        if self.__get_os() == "Linux":
            os.system("clear")
        else:
            os.system("cls")

    def print_ip(
        self,
        ip: str
    ) -> str:
        return f"IP: " + COLORS["ip_color"] + ip + COLORS["text_color"]
    
    def print_username(
        self,
        username: str
    ) -> str:
        return f"USERNAME: " + COLORS["ip_color"] + username + COLORS["username_color"]

    def print_chat(self, response: list[str]) -> str:
        for i, msg in enumerate(response["messages"]):
            actual_message = self._decrypt(msg)
            if i == 0:
                for user in response["users_in_chat"]:
                    print(self.print_ip(user.split(",")[0]))
                    print(self.print_username(user.split(",")[1]))
                print("Write 'q' to quit from chat")
                print(f"\n{self.print_message(actual_message)}")
            else:
                print(f"{self.print_message(actual_message)}")
