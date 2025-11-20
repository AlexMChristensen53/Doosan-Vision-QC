"""Robot client helpers for sending TP (teach pendant) commands to Doosan.

Denne fil indeholder en lille hjælperfunktion `send_tp_pop` som bygger
en TP-kommando til at vise en popup på robotten via `tp_pop(...)`.
"""

import socket


def send_tp_pop(sock: socket.socket,
				message: str,
				level: str = 'DR_PM_MESSAGE',
				command_name: str = 'tp_pop',
				quote_level: bool = False,
				encoding: str = 'utf-8') -> None:
	"""Send en tp_pop-kommando til Doosan robotten over en åben socket.

	Denne funktion logger den nøjagtige tekst (repr) den sender, og giver
	muligheder for at sende alternative varianter, da forskellige Doosan
	setups nogle gange forventer lidt forskelligt format.

	Args:
		sock: En åben, forbundet `socket.socket` instans.
		message: Teksten der skal vises i popup'en. Dobbelte anførselstegn escaperes.
		level: Popup-niveau/konstant (standard: 'DR_PM_MESSAGE').
		command_name: 'tp_pop' eller f.eks. 'tp_popup' hvis robot-programmet bruger andet navn.
		quote_level: Hvis True sendes level i dobbelte anførselstegn: "DR_PM_MESSAGE".
		encoding: Tegnsæt til at encode strengen før send.

	Returnerer ikke noget, men printer den fulde kommando (repr) så du kan
	sammenligne med hvad robotten modtager.
	"""
	# Escape dobbelte anførselstegn i beskeden
	safe_msg = message.replace('"', '\\"')
	# Bestem hvordan level skal indgå i kommandoen
	if quote_level:
		level_part = f'"{level}"' if not (level.startswith('"') or level.startswith("'")) else level
	else:
		level_part = level

	cmd = f'{command_name}("{safe_msg}", {level_part})\r\n'
	# Log nøjagtigt hvad der sendes (repr for at se kontroltegn)
	print(f"Sending (repr): {repr(cmd)}")
	sock.sendall(cmd.encode(encoding))


def send_tp_popup(sock: socket.socket, message: str, **kwargs) -> None:
	"""Alias der prøver kommando-navnet `tp_popup` hvis din robot bruger det."""
	send_tp_pop(sock, message, command_name='tp_popup', **kwargs)


if __name__ == '__main__':
	# Hurtig manuelle test (kræver at en Doosan-robot er tilgængelig på HOST:PORT)
	HOST = '192.168.137.51'
	PORT = 20002
	try:
		with socket.create_connection((HOST, PORT), timeout=5) as s:
			print(f"Forbundet til {HOST}:{PORT}, sender tp_pop-test...")
			send_tp_pop(s, "Test popup fra Robot_client.py")
			print("Sendt.")
	except Exception as e:
		print(f"Kunne ikke sende tp_pop-test: {e}")

