import asyncio
import argparse
from cmd_chat.server.server import run_server
from cmd_chat.client.client import Client

def run_http_server(ip: str, port: int, password: str | None) -> None:
    run_server(ip, int(port), False, password)

async def run_client(username: str, server: str, port: int, password: str | None) -> None:
    Client(server=server, port=port, username=username, password=password).run()

async def run() -> None:
    parser = argparse.ArgumentParser(description='Command-line chat application')
    subparsers = parser.add_subparsers(dest='command', required=True)

    serve_p = subparsers.add_parser('serve', help='Run server')
    serve_p.add_argument('ip_address')
    serve_p.add_argument('port')
    serve_p.add_argument('--password', '-p', required=True, help='Admin password required for clients')

    connect_p = subparsers.add_parser('connect', help='Connect to server')
    connect_p.add_argument('ip_address')
    connect_p.add_argument('port')
    connect_p.add_argument('username')
    connect_p.add_argument('password', help='Password to auth on server')

    args = parser.parse_args()

    if args.command == 'serve':
        run_http_server(args.ip_address, args.port, args.password)
    elif args.command == 'connect':
        await run_client(args.username, args.ip_address, int(args.port), args.password)

def main():
    asyncio.run(run())

if __name__ == '__main__':
    main()
